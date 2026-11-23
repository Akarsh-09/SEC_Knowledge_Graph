"""OpenAI-compatible structured JSON, bounded retries, model fallback and offline replay."""
from __future__ import annotations

import copy
import hashlib
import json
import logging
import math
import os
from pathlib import Path
import re
import sqlite3
import threading
import time
from typing import Literal, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

ROOT = Path(__file__).resolve().parents[1]
LOG = logging.getLogger(__name__)
T = TypeVar('T', bound=BaseModel)
Source = Literal['llm_live', 'llm_cache']


class OfflineCacheMiss(LookupError):
    """No valid cached response exists; callers may use a deterministic fallback."""


class StructuredOutputError(ValueError):
    """The provider exhausted its bounded JSON/schema validation retries."""


def _json_content(content: str) -> object:
    """Strip only a complete optional Markdown fence; never repair malformed JSON."""
    content = content.strip()
    fenced = re.fullmatch(r'```(?:json)?\s*\n?(.*?)\n?```', content, re.I | re.S)
    if fenced:
        content = fenced[1].strip()
    def reject_constant(value):
        raise json.JSONDecodeError('Nonfinite JSON number: '+value,content,0)
    return json.loads(content,parse_constant=reject_constant)


def _strict_schema(schema: type[BaseModel]) -> dict:
    """Constrain model objects for strict providers; preserve nullable field types."""
    definition = copy.deepcopy(schema.model_json_schema())

    def visit(node):
        if isinstance(node, dict):
            node.pop('default', None)
            if 'properties' in node:
                node['additionalProperties'] = False
                node['required'] = list(node['properties'])
            for value in node.values():
                visit(value)
        elif isinstance(node, list):
            for value in node:
                visit(value)
    visit(definition)
    return definition


def _gemini_schema(schema: type[BaseModel]) -> dict:
    """Inline references and simplify nullable unions for compatibility gateways.

    Complex unions still require JSON-object mode below. The original Pydantic
    model always validates responses; a wire-format workaround never relaxes it.
    """
    definition = _strict_schema(schema)

    def visit(node, stack=()):
        if isinstance(node, list):
            return [visit(value, stack) for value in node]
        if not isinstance(node, dict):
            return node
        node = copy.deepcopy(node)
        if '$ref' in node:
            ref = node.pop('$ref')
            if not ref.startswith('#/') or ref in stack:
                raise ValueError('Recursive/external schema references require JSON-object mode')
            target = definition
            for token in ref[2:].split('/'):
                target = target[token.replace('~1', '/').replace('~0', '~')]
            node = visit(target, (*stack, ref)) | node
        node = {key: visit(value, stack) for key, value in node.items()
                if key not in ('$defs', 'definitions', 'discriminator', 'title')}
        if 'const' in node:
            node['enum'] = [node.pop('const')]
        if 'oneOf' in node:
            node['anyOf'] = node.pop('oneOf')
        variants = node.get('anyOf', [])
        nonnull = [v for v in variants if v.get('type') != 'null']
        if len(variants) == 2 and len(nonnull) == 1 and isinstance(nonnull[0].get('type'), str):
            node.pop('anyOf')
            nullable = nonnull[0]
            node.update(nullable)
            node['type'] = [nullable['type'], 'null']
            if 'enum' in node:
                node['enum'] = list(dict.fromkeys(node['enum'] + [None]))
        return node

    return visit(definition)


def _complex_union(node: object) -> bool:
    if isinstance(node, dict):
        return 'anyOf' in node or 'oneOf' in node or any(_complex_union(v) for v in node.values())
    return isinstance(node, list) and any(_complex_union(v) for v in node)


class LLMClient:
    """Cache keys remain SHA256(actual_model + system_prompt + user_prompt).

    Missing keys force offline mode. Model fallbacks require explicit configuration;
    cached fallback-model responses are never stored under the primary model's key.
    Only the relation-extraction collection contract may degrade to an uncached empty
    result after three invalid responses. Query plans and all other schemas fail closed.
    """

    def __init__(self, *, offline: bool = False, cache_path: Path | None = None,
                 model: str | None = None, base_url: str | None = None,
                 api_key: str | None = None, max_retries: int = 4,
                 reasoning_effort: str | None = None,
                 fallback_models: list[str] | None = None,
                 min_interval_seconds: float | None = None) -> None:
        self.model = model if model is not None else os.getenv('LLM_MODEL', '')
        self.api_key = api_key if api_key is not None else os.getenv('LLM_API_KEY', '')
        self.base_url = (base_url or os.getenv('LLM_BASE_URL', 'https://api.openai.com/v1')).rstrip('/')
        self.offline = offline or not self.api_key.strip()
        self.reasoning_effort = (reasoning_effort if reasoning_effort is not None else os.getenv('LLM_REASONING_EFFORT', '')).strip()
        configured = fallback_models if fallback_models is not None else os.getenv('LLM_FALLBACK_MODELS', '').split(',')
        self.models = list(dict.fromkeys([self.model] + [m.strip() for m in configured if m.strip() and m.strip() != self.model]))
        self.min_interval_seconds = float(min_interval_seconds if min_interval_seconds is not None else os.getenv('LLM_MIN_INTERVAL_SECONDS', '0') or '0')
        if not math.isfinite(self.min_interval_seconds) or self.min_interval_seconds < 0:
            raise ValueError('LLM_MIN_INTERVAL_SECONDS must be finite and nonnegative')
        if max_retries < 0:
            raise ValueError('max_retries must be nonnegative')
        self.max_retries = max_retries
        self._last_request: float | None = None
        self._pacing_lock = threading.Lock()
        self._json_object_models: set[str] = set()
        self._compatibility_logged: set[tuple[str, type[BaseModel]]] = set()
        self.last_model = self.model
        self.validation_failures = 0
        self.skipped_relation_pages = 0
        self.cache_path = cache_path or ROOT / '.cache/llm_cache.sqlite'
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.cache_path) as db:
            db.execute('CREATE TABLE IF NOT EXISTS responses (key TEXT PRIMARY KEY, model TEXT NOT NULL, response TEXT NOT NULL)')

    @staticmethod
    def _key(model: str, system: str, user: str) -> str:
        return hashlib.sha256((model + system + user).encode()).hexdigest()

    def _cached(self, model: str, system: str, user: str, schema: type[T]) -> T | None:
        with sqlite3.connect(self.cache_path) as db:
            row = db.execute('SELECT response FROM responses WHERE key=?', (self._key(model, system, user),)).fetchone()
        if row is None:
            return None
        try:
            return schema.model_validate(_json_content(row[0]))
        except (ValidationError, json.JSONDecodeError):
            LOG.warning('Ignoring invalid cached response for model=%s schema=%s', model, schema.__name__)
            return None

    def _pace(self) -> None:
        # One shared instance paces request starts, including retries and format negotiation.
        with self._pacing_lock:
            now = time.monotonic()
            if self._last_request is not None:
                delay = max(0.0, self.min_interval_seconds - (now - self._last_request))
                if delay:
                    time.sleep(delay)
            self._last_request = time.monotonic()

    def _payload(self, model: str, system: str, user: str, schema: type[T]) -> dict:
        definition = _strict_schema(schema)
        json_object = model in self._json_object_models
        if 'gemini' in model.casefold() or any(host in self.base_url for host in ('generativelanguage.googleapis.com', 'aiplatform.googleapis.com')):
            try:
                definition = _gemini_schema(schema)
                json_object = json_object or _complex_union(definition)
            except (ValueError, KeyError):
                json_object = True
            if json_object and (model, schema) not in self._compatibility_logged:
                LOG.info('model=%s schema=%s uses JSON-object compatibility mode with local validation', model, schema.__name__)
                self._compatibility_logged.add((model, schema))
        response_format = {'type': 'json_object'} if json_object else {
            'type': 'json_schema', 'json_schema': {'name': schema.__name__, 'strict': True, 'schema': definition}}
        if json_object:
            schema_text = json.dumps(schema.model_json_schema(), sort_keys=True)
            if schema_text not in system:
                system += '\nReturn ONLY valid JSON matching this JSON Schema: ' + schema_text
        payload = dict(model=model, temperature=0, messages=[
            dict(role='system', content=system), dict(role='user', content=user)], response_format=response_format)
        if self.reasoning_effort:
            payload['reasoning_effort'] = self.reasoning_effort
        return payload

    @staticmethod
    def _empty_relations(schema: type[T]) -> T | None:
        # Compatibility adapter for the frozen extractor: no import or changes to its
        # exception handling are required, and planners cannot silently become empty.
        from typing import get_args, get_origin
        if set(schema.model_fields) != {'claims'}:
            return None
        annotation = schema.model_fields['claims'].annotation
        item = get_args(annotation)
        if get_origin(annotation) is not list or len(item) != 1:
            return None
        candidate = item[0]
        if not isinstance(candidate, type) or not issubclass(candidate, BaseModel):
            return None
        if set(candidate.model_fields) != {'relation_type', 'target_name', 'page_num', 'verbatim_quote'}:
            return None
        try:
            return schema.model_validate({'claims': []})
        except ValidationError:
            return None

    def structured(self, system_prompt: str, user_prompt: str, schema: type[T]) -> tuple[T, Source]:
        """Replay first; live responses get two additional validation attempts.

        HTTP/transport retry budget is independent of JSON retries. A provider's 400
        on json_schema downgrades that model to json_object for this client instance.
        No invalid or synthetic empty response is ever written to the disk cache.
        """
        for model in self.models if self.offline else self.models[:1]:
            cached = self._cached(model, system_prompt, user_prompt, schema)
            if cached is not None:
                self.last_model = model
                return cached, 'llm_cache'
        if self.offline:
            raise OfflineCacheMiss(f'Offline cache miss: {self._key(self.model, system_prompt, user_prompt)}')
        if not self.model:
            raise ValueError('LLM_MODEL must be set for live requests')
        model_index = 0
        last_error: Exception | None = None
        with httpx.Client(timeout=90) as client:
            for validation_attempt in range(3):
                transient_attempt = 0
                while True:
                    model = self.models[model_index]
                    payload = self._payload(model, system_prompt, user_prompt, schema)
                    self._pace()
                    try:
                        response = client.post(self.base_url + '/chat/completions', json=payload,
                                               headers={'Authorization': f'Bearer {self.api_key}'})
                    except httpx.TransportError:
                        if transient_attempt >= self.max_retries:
                            raise
                        time.sleep(min(2 ** transient_attempt, 30))
                        transient_attempt += 1
                        continue
                    if response.status_code == 400 and payload['response_format']['type'] == 'json_schema':
                        self._json_object_models.add(model)
                        response.close()
                        LOG.warning('model=%s rejected json_schema (400); retrying with json_object', model)
                        continue
                    if response.status_code == 429 or 500 <= response.status_code < 600:
                        if transient_attempt >= self.max_retries:
                            response.raise_for_status()
                        if response.status_code in (429, 503) and model_index + 1 < len(self.models):
                            model_index += 1
                            next_model = self.models[model_index]
                            LOG.warning('model=%s returned HTTP %d; using configured fallback model=%s', model, response.status_code, next_model)
                            # A JSON retry must bypass all cached responses.
                            if validation_attempt == 0:
                                cached = self._cached(next_model, system_prompt, user_prompt, schema)
                                if cached is not None:
                                    self.last_model = next_model
                                    response.close()
                                    return cached, 'llm_cache'
                        response.close()
                        time.sleep(min(2 ** transient_attempt, 30))
                        transient_attempt += 1
                        continue
                    response.raise_for_status()
                    self.last_model = model
                    break
                try:
                    envelope = response.json()
                    try:
                        content = envelope['choices'][0]['message']['content']
                    except (KeyError, IndexError, TypeError) as error:
                        raise json.JSONDecodeError('Missing chat completion content', '', 0) from error
                    if not isinstance(content, str):
                        raise json.JSONDecodeError('Chat completion content must be a JSON string', '', 0)
                    validated = schema.model_validate(_json_content(content))
                except (ValidationError, json.JSONDecodeError) as error:
                    last_error = error
                    self.validation_failures += 1
                    LOG.warning('Invalid structured JSON model=%s schema=%s attempt=%d/3 (%s)',
                                model, schema.__name__, validation_attempt + 1, type(error).__name__)
                    continue
                with sqlite3.connect(self.cache_path) as db:
                    db.execute('INSERT OR REPLACE INTO responses VALUES (?, ?, ?)',
                               (self._key(model, system_prompt, user_prompt), model, validated.model_dump_json()))
                return validated, 'llm_live'
        empty = self._empty_relations(schema)
        if empty is not None:
            self.skipped_relation_pages += 1
            context = user_prompt.split('\n', 1)[0][:160] if user_prompt.startswith('Company: ') else 'relation page'
            LOG.warning('Skipping malformed %s after 3 validation attempts; returning uncached empty candidates (model=%s)', context, self.last_model)
            return empty, 'llm_live'
        raise StructuredOutputError(f'Invalid {schema.__name__} JSON after 3 validation attempts (model={self.last_model})') from last_error
