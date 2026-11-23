"""Provider JSON negotiation/recovery, model-keyed cache, pacing and offline safety."""
import hashlib
import json
import sqlite3
from unittest.mock import patch
import httpx
import pytest
from pydantic import BaseModel
from src.llm_client import LLMClient, OfflineCacheMiss, StructuredOutputError
from src.extract.relation_extractor import Candidates, extract
from src.ingest.pdf_parser import ParsedPage

class Reply(BaseModel):
    value: int


def completion(content):
    return httpx.Response(200,json={'choices':[{'message':{'content':content}}]})


def configured(tmp_path, handler, **options):
    http=httpx.Client(transport=httpx.MockTransport(handler))
    client=LLMClient(api_key='unit-test',model='primary',cache_path=tmp_path/'cache.sqlite',min_interval_seconds=0,**options)
    return client,http


def cached_rows(client):
    with sqlite3.connect(client.cache_path) as db:return db.execute('SELECT key,model,response FROM responses').fetchall()

@pytest.mark.parametrize('invalid',['{"value": >\n}', '{"value":"not an integer"}'])
def test_json_and_schema_validation_retry(tmp_path,invalid):
    calls=[]
    def handle(request):
        calls.append(json.loads(request.content))
        return completion(invalid if len(calls)==1 else '{"value":7}')
    client,http=configured(tmp_path,handle)
    with patch('src.llm_client.httpx.Client',return_value=http):
        value,source=client.structured('s','u',Reply)
    assert value.value==7 and source=='llm_live' and len(calls)==2
    assert client.validation_failures==1
    fmt=calls[0]['response_format']
    assert fmt['type']=='json_schema' and fmt['json_schema']['name']=='Reply'
    assert fmt['json_schema']['strict'] is True
    assert fmt['json_schema']['schema']['additionalProperties'] is False
    assert len(cached_rows(client))==1 and json.loads(cached_rows(client)[0][2])=={'value':7}

@pytest.mark.parametrize('content',['```json\n{"value":7}\n```','```\n{"value":7}\n```'])
def test_markdown_fence(tmp_path,content):
    client,http=configured(tmp_path,lambda request:completion(content))
    with patch('src.llm_client.httpx.Client',return_value=http):
        assert client.structured('s','u',Reply)[0].value==7


def test_schema_400_downgrades_and_is_remembered(tmp_path):
    formats=[]
    def handle(request):
        fmt=json.loads(request.content)['response_format']['type'];formats.append(fmt)
        return httpx.Response(400) if fmt=='json_schema' else completion('{"value":1}')
    client,http=configured(tmp_path,handle)
    # One call validates fallback negotiation; its subsequent JSON retry stays downgraded.
    with patch('src.llm_client.httpx.Client',return_value=http):
        assert client.structured('s','u',Reply)[0].value==1
    assert formats==['json_schema','json_object']
    assert client._payload('primary','s','u2',Reply)['response_format']=={'type':'json_object'}


def test_invalid_generic_response_fails_closed_without_cache(tmp_path):
    count=0
    def handle(request):
        nonlocal count
        count+=1;return completion('{"value": >}')
    client,http=configured(tmp_path,handle)
    with patch('src.llm_client.httpx.Client',return_value=http),pytest.raises(StructuredOutputError):
        client.structured('s','u',Reply)
    assert count==3 and cached_rows(client)==[]


def test_malformed_relation_page_skips_and_next_page_continues(tmp_path,caplog):
    calls=[]
    def handle(request):
        body=json.loads(request.content);calls.append(body)
        prompt=body['messages'][1]['content']
        if 'PDF page 1\n' in prompt:return completion('{"claims": [>\n}')
        return completion(json.dumps({'claims':[dict(relation_type='ACQUIRED',target_name='Acme',page_num=2,verbatim_quote='We acquired Acme.')]}))
    client,http=configured(tmp_path,handle)
    pages=[ParsedPage(source_doc='example.pdf',page_num=i,section='Item 1',text='We acquired Acme.',tables=[]) for i in [1,2]]
    real_client=httpx.Client
    http.close()
    with patch('src.llm_client.httpx.Client',side_effect=lambda **kwargs:real_client(**kwargs,transport=httpx.MockTransport(handle))):
        facts=extract(pages,'COMP:EXAMPLE',client)
    assert len(calls)==4 and len(facts)==1 and facts[0].page_num==2
    assert client.skipped_relation_pages==1
    assert 'uncached empty candidates' in caplog.text
    rows=cached_rows(client)
    assert len(rows)==1 and json.loads(rows[0][2])['claims'][0]['page_num']==2


def test_json_retry_bypasses_new_cache_entry(tmp_path):
    calls=0;client=None
    def handle(request):
        nonlocal calls
        calls+=1
        if calls==1:
            # Simulate a competing process filling the cache during validation retry.
            with sqlite3.connect(client.cache_path) as db:
                db.execute('INSERT INTO responses VALUES (?,?,?)',(hashlib.sha256(b'primarysu').hexdigest(),'primary','{"value":99}'))
            return completion('{"value": >}')
        return completion('{"value":7}')
    client,http=configured(tmp_path,handle)
    with patch('src.llm_client.httpx.Client',return_value=http):
        assert client.structured('s','u',Reply)[0].value==7
    assert calls==2

@pytest.mark.parametrize('status',[429,503])
def test_explicit_fallback_model_has_own_cache_key(tmp_path,status):
    models=[]
    def handle(request):
        model=json.loads(request.content)['model'];models.append(model)
        return httpx.Response(status) if model=='primary' else completion('{"value":5}')
    client,http=configured(tmp_path,handle,fallback_models=['backup'])
    with patch('src.llm_client.httpx.Client',return_value=http),patch('src.llm_client.time.sleep'):
        assert client.structured('s','u',Reply)[0].value==5
    assert models==['primary','backup'] and client.last_model=='backup'
    rows=cached_rows(client)
    assert rows[0][0]==hashlib.sha256(b'backupsu').hexdigest() and rows[0][1]=='backup'
    offline=LLMClient(offline=True,model='primary',fallback_models=['backup'],cache_path=client.cache_path)
    with patch('src.llm_client.httpx.Client',side_effect=AssertionError('network forbidden')):
        assert offline.structured('s','u',Reply)[1]=='llm_cache'
        with pytest.raises(OfflineCacheMiss):offline.structured('s','unknown',Reply)


def test_unconfigured_fallback_never_switches_model(tmp_path,monkeypatch):
    monkeypatch.delenv('LLM_FALLBACK_MODELS',raising=False)
    models=[]
    def handle(request):
        models.append(json.loads(request.content)['model']);return httpx.Response(503)
    client,http=configured(tmp_path,handle,max_retries=1)
    with patch('src.llm_client.httpx.Client',return_value=http),patch('src.llm_client.time.sleep'),pytest.raises(httpx.HTTPStatusError):
        client.structured('s','u',Reply)
    assert models==['primary','primary'] and not cached_rows(client)


def test_transport_retry(tmp_path):
    calls=0
    def handle(request):
        nonlocal calls
        calls+=1
        if calls==1:raise httpx.ReadError('reset')
        return completion('{"value":1}')
    client,http=configured(tmp_path,handle)
    with patch('src.llm_client.httpx.Client',return_value=http),patch('src.llm_client.time.sleep'):
        assert client.structured('s','u',Reply)[0].value==1
    assert calls==2


def test_interval_applies_to_negotiation_and_json_retries(tmp_path):
    calls=0;clock=[0.0];delays=[]
    def sleep(delay):delays.append(delay);clock[0]+=delay
    def handle(request):
        nonlocal calls
        calls+=1
        if calls==1:return httpx.Response(400)
        return completion('{"value": >}' if calls==2 else '{"value":1}')
    http=httpx.Client(transport=httpx.MockTransport(handle))
    client=LLMClient(api_key='test',model='primary',min_interval_seconds=2,cache_path=tmp_path/'c.sqlite')
    with patch('src.llm_client.httpx.Client',return_value=http),patch('src.llm_client.time.monotonic',side_effect=lambda:clock[0]),patch('src.llm_client.time.sleep',side_effect=sleep):
        assert client.structured('s','u',Reply)[0].value==1
    assert delays==[2,2]


def test_environment_configuration(tmp_path,monkeypatch):
    monkeypatch.setenv('LLM_FALLBACK_MODELS',' backup-a,backup-b,backup-a,primary ')
    monkeypatch.setenv('LLM_MIN_INTERVAL_SECONDS','1.5')
    client=LLMClient(offline=True,model='primary',cache_path=tmp_path/'c.sqlite')
    assert client.models==['primary','backup-a','backup-b'] and client.min_interval_seconds==1.5


def test_corrupted_offline_cache_never_calls_network(tmp_path):
    client=LLMClient(offline=True,model='primary',cache_path=tmp_path/'c.sqlite')
    with sqlite3.connect(client.cache_path) as db:
        db.execute('INSERT INTO responses VALUES (?,?,?)',(hashlib.sha256(b'primarysu').hexdigest(),'primary','{"value": >}'))
    with patch('src.llm_client.httpx.Client',side_effect=AssertionError('network forbidden')),pytest.raises(OfflineCacheMiss):
        client.structured('s','u',Reply)


def test_invalid_http_envelope_is_retried(tmp_path):
    calls=0
    def handle(request):
        nonlocal calls
        calls+=1
        return httpx.Response(200,text='not JSON') if calls==1 else completion('{"value":7}')
    client,http=configured(tmp_path,handle)
    with patch('src.llm_client.httpx.Client',return_value=http):
        assert client.structured('s','u',Reply)[0].value==7
    assert calls==2


def test_nonfinite_json_never_cached(tmp_path):
    class Number(BaseModel):
        value: float
    client,http=configured(tmp_path,lambda request:completion('{"value":NaN}'))
    with patch('src.llm_client.httpx.Client',return_value=http),pytest.raises(StructuredOutputError):
        client.structured('s','u',Number)
    assert not cached_rows(client)


def test_fallback_reuses_cached_response_without_misattribution(tmp_path):
    calls=[]
    def handle(request):
        calls.append(json.loads(request.content)['model']);return httpx.Response(429)
    client,http=configured(tmp_path,handle,fallback_models=['backup'])
    with sqlite3.connect(client.cache_path) as db:
        db.execute('INSERT INTO responses VALUES (?,?,?)',(hashlib.sha256(b'backupsu').hexdigest(),'backup','{"value":5}'))
    with patch('src.llm_client.httpx.Client',return_value=http):
        answer,source=client.structured('s','u',Reply)
    assert answer.value==5 and source=='llm_cache' and calls==['primary']
    assert cached_rows(client)[0][1]=='backup'


def test_gemini_simple_schema_inlines_references_and_nullable_fields(tmp_path):
    from src.llm_client import _gemini_schema
    class Detail(BaseModel):
        label: str
    class Nested(BaseModel):
        detail: Detail
        note: str | None = None
    client=LLMClient(api_key='test',model='gemini-test',cache_path=tmp_path/'c.sqlite')
    payload=client._payload(client.model,'system','user',Nested)
    wire=payload['response_format']['json_schema']['schema']
    serialized=json.dumps(wire)
    assert payload['response_format']['type']=='json_schema'
    assert '$ref' not in serialized and '$defs' not in serialized and 'discriminator' not in serialized
    assert wire['properties']['detail']['properties']['label']['type']=='string'
    assert wire['properties']['note']['type']==['string','null']
    assert 'anyOf' not in json.dumps(_gemini_schema(Nested))
    assert Nested.model_validate({'detail':{'label':'ok'},'note':None}).note is None


def test_gemini_query_plan_uses_json_object_without_schema_400_probe(tmp_path):
    from src.query.planner import GraphQueryPlan
    plan={'steps':[dict(action='lookup_metric',output_var='$values',company_ids=['COMP:B','COMP:A'],metric_id='METRIC:REVENUE',period_id='FY2025'),
                   dict(action='aggregate_compare',output_var='$answer',input_var='$values',op='ratio')]}
    calls=[]
    def handle(request):
        body=json.loads(request.content);calls.append(body)
        assert body['response_format']=={'type':'json_object'}
        assert 'JSON Schema' in body['messages'][0]['content']
        assert 'aggregate_compare' in body['messages'][0]['content'] and 'ratio' in body['messages'][0]['content']
        return completion(json.dumps(plan))
    http=httpx.Client(transport=httpx.MockTransport(handle))
    client=LLMClient(api_key='test',model='gemini-test',cache_path=tmp_path/'c.sqlite')
    with patch('src.llm_client.httpx.Client',return_value=http):
        result,source=client.structured('system','user',GraphQueryPlan)
    assert source=='llm_live' and len(calls)==1 and result.steps[-1].op=='ratio'
    assert cached_rows(client)[0][0]==hashlib.sha256(b'gemini-testsystemuser').hexdigest()


def test_provider_400_json_object_fallback_includes_explicit_schema(tmp_path):
    calls=[]
    def handle(request):
        body=json.loads(request.content);calls.append(body)
        return httpx.Response(400) if len(calls)==1 else completion('{"value":1}')
    client,http=configured(tmp_path,handle)
    with patch('src.llm_client.httpx.Client',return_value=http):
        assert client.structured('system','user',Reply)[0].value==1
    assert calls[1]['response_format']=={'type':'json_object'}
    assert json.dumps(Reply.model_json_schema(),sort_keys=True) in calls[1]['messages'][0]['content']
    assert calls[1]['messages'][1]['content']=='user'


def test_gemini_query_plan_still_fails_closed_on_invalid_ast(tmp_path):
    from src.query.planner import GraphQueryPlan
    calls=[]
    def handle(request):
        body=json.loads(request.content);calls.append(body)
        assert body['response_format']=={'type':'json_object'}
        return completion('{"steps":[{"action":"execute_python","output_var":"$x"}]}')
    client,http=configured(tmp_path,handle)
    client.model='gemini-test';client.models=[client.model]
    with patch('src.llm_client.httpx.Client',return_value=http),pytest.raises(StructuredOutputError):
        client.structured('system','user',GraphQueryPlan)
    assert len(calls)==3 and not cached_rows(client)


def test_gemini_compatibility_detected_by_endpoint_even_with_aliased_model(tmp_path):
    from src.query.planner import GraphQueryPlan
    client=LLMClient(api_key='test',model='proxy-model',base_url='https://generativelanguage.googleapis.com/v1beta/openai',cache_path=tmp_path/'c.sqlite')
    assert client._payload(client.model,'system','user',GraphQueryPlan)['response_format']=={'type':'json_object'}
