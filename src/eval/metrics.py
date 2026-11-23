"""Answer accuracy and one-to-one exact-provenance precision/recall."""
from __future__ import annotations
import json
import math
from pathlib import Path
import re
from statistics import mean
from typing import Any
from config.ontology import ENTITY_ALIASES, METRIC_SYNONYMS, CanonicalMetric
from src.entity_names import US_STATES, entity_key

ROOT=Path(__file__).resolve().parents[2]
TYPES=('single-fact','multi-hop','cross-filing')

def normalize(text: Any) -> str:
    return ' '.join(re.sub(r'[^a-z0-9]+',' ',str(text).casefold()).split())

def canonical_entity(value: str) -> str:
    companies={}
    for company in json.loads((ROOT/'config/companies.json').read_text()):
        id='COMP:'+company['ticker']
        for name in (id,company['ticker'],company['name']): companies[normalize(name)]=normalize(id)
    external=bool(re.match(r'^EXT\s*:',value,re.I))
    key=normalize(re.sub(r'^EXT\s*:','',value,flags=re.I))
    without_suffix=re.sub(r' (?:inc|incorporated|corporation|corp|company|co|llp|ltd)$','',key)
    if not (external and key.upper() in US_STATES):
        if key in companies:return companies[key]
        if without_suffix in companies:return companies[without_suffix]
    aliases={entity_key(alias):entity_key(id) for alias,id in ENTITY_ALIASES.items()}
    aliases.update({entity_key(id):entity_key(id) for id in ENTITY_ALIASES.values()})
    key=entity_key(value)
    without_suffix=re.sub(r' (?:inc|incorporated|corporation|corp|company|co|llp|ltd)$','',key)
    return aliases.get(key,aliases.get(without_suffix,key))

def canonical_predicate(value: str) -> str:
    name=value.removeprefix('METRIC:')
    for metric in CanonicalMetric:
        if normalize(name)==normalize(metric.value) or any(normalize(name)==normalize(a) for a in METRIC_SYNONYMS.get(metric.value,())):
            return 'METRIC:'+metric.value
    return value.upper()

def normalized_number(value: Any, unit: str | None) -> tuple[float,str]:
    if isinstance(value,bool): raise ValueError('Boolean is not numeric')
    number=float(value)
    if not math.isfinite(number): raise ValueError('Nonfinite numeric answer')
    label=normalize(unit or '')
    if label in ('percent','percentage','percentage points','pct'): return number/100,'dimensionless'
    if label in ('ratio','decimal','decimal ratio'):return number,'dimensionless'
    scale=1.0
    for token,factor in (('trillion',1e12),('billion',1e9),('million',1e6),('thousand',1e3)):
        if token in label:scale=factor;break
    if any(t in label for t in ('usd','dollar')):
        return number*scale,'USD/share' if 'share' in label else 'USD'
    return number,label

def answer_correct(question: dict, prediction: dict) -> bool:
    gold=question['golden_answer'];value=prediction.get('structured_answer')
    if prediction.get('abstained'):return gold is None
    if gold is None:return value is None
    kind=question['answer_type']
    if prediction.get('answer_type') not in (None,kind):return False
    if kind=='numeric':
        try:
            predicted,punit=normalized_number(value,prediction.get('unit'))
            expected,gunit=normalized_number(gold,question.get('unit'))
            # Missing units are not assumed when the other side is explicitly annotated.
            if punit!=gunit:return False
            return abs(predicted-expected)<=max(abs(expected)*.01,1e-12)
        except (TypeError,ValueError):return False
    if kind=='boolean':return type(value) is bool and type(gold) is bool and value==gold
    if kind=='entity':return isinstance(value,str) and isinstance(gold,str) and canonical_entity(value)==canonical_entity(gold)
    if kind=='entity_list':
        if not isinstance(value,list) or not isinstance(gold,list) or not all(isinstance(x,str) for x in value+gold):return False
        predicted=[canonical_entity(x) for x in value];expected=[canonical_entity(x) for x in gold]
        ranked=question.get('order_sensitive',False) or bool(re.search(r'\b(rank(?:ing)?|ordered|descending|ascending|top\s+\d+)\b',question['question'],re.I))
        return predicted==expected if ranked else set(predicted)==set(expected)
    raise ValueError('Unsupported answer_type: '+kind)

def fact_matches(retrieved: dict, gold: dict, *, page_tolerance: int=0) -> bool:
    if retrieved.get('source_doc')!=gold['doc_id'] or retrieved.get('company_id')!=gold['company_id']:return False
    if abs(retrieved.get('page_num',-10000)-gold['page_num'])>page_tolerance:return False
    predicate=canonical_predicate(gold['predicate'])
    if canonical_predicate(retrieved.get('predicate',''))!=predicate:return False
    if gold.get('period') is not None and retrieved.get('period')!=gold['period']:return False
    # Preserve the strict primary definition. The relaxed page diagnostic must
    # additionally identify the same relation target, including same-page claims.
    if page_tolerance and not predicate.startswith('METRIC:') and gold.get('expected_value') is not None:
        expected=canonical_entity(str(gold['expected_value']))
        values=[retrieved.get(k) for k in ('target_name','target_id','value')]
        return any(isinstance(v,str) and canonical_entity(v)==expected for v in values)
    return True

def match_facts(retrieved: list[dict], gold: list[dict], *, page_tolerance: int=0) -> dict:
    """Maximum bipartite matching; each prediction and gold fact earns at most one match.

    Duplicate retrieved entries stay in the precision denominator and become extras.
    Maximum matching matters for overlapping +/-1-page neighborhoods.
    """
    assignment={}
    def assign(index,visited):
        for j,fact in enumerate(gold):
            if j in visited or not fact_matches(retrieved[index],fact,page_tolerance=page_tolerance):continue
            visited.add(j)
            if j not in assignment or assign(assignment[j],visited):
                assignment[j]=index;return True
        return False
    for i in range(len(retrieved)):assign(i,set())
    used=set(assignment.values());count=len(assignment)
    return dict(matched_count=count,retrieved_count=len(retrieved),gold_count=len(gold),
                precision=count/len(retrieved) if retrieved else 0.0,recall=count/len(gold) if gold else 0.0,
                matched_facts=[dict(retrieved=retrieved[i],gold=gold[j]) for j,i in sorted(assignment.items())],
                missed_facts=[f for j,f in enumerate(gold) if j not in assignment],
                extra_facts=[f for i,f in enumerate(retrieved) if i not in used])

def score_question(question: dict, prediction: dict) -> dict:
    retrieved=prediction.get('retrieved_facts',[]);gold=question['gold_supporting_facts']
    return dict(id=question['id'],type=question['type'],correct=answer_correct(question,prediction),
                strict=match_facts(retrieved,gold),page_plus_minus_1=match_facts(retrieved,gold,page_tolerance=1))

def aggregate(scores: list[dict]) -> dict:
    def group(rows):
        output={'questions':len(rows),'accuracy':mean(r['correct'] for r in rows) if rows else 0.0}
        for key in ('strict','page_plus_minus_1'):
            matched=sum(r[key]['matched_count'] for r in rows);retrieved=sum(r[key]['retrieved_count'] for r in rows);gold=sum(r[key]['gold_count'] for r in rows)
            output[key]=dict(precision_macro=mean(r[key]['precision'] for r in rows) if rows else 0.,
                recall_macro=mean(r[key]['recall'] for r in rows) if rows else 0.,
                precision_micro=matched/retrieved if retrieved else 0.,recall_micro=matched/gold if gold else 0.,
                matched_facts=matched,retrieved_facts=retrieved,gold_facts=gold)
        return output
    return {**{kind:group([r for r in scores if r['type']==kind]) for kind in TYPES},'Overall':group(scores)}
