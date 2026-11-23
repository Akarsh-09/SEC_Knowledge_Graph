"""Deterministic formatting of graph results; never generates unsupported prose."""
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, ConfigDict, model_validator
from src.llm_client import LLMClient
from src.graph.store import GraphStore
from src.query.concept_resolver import resolve
from src.query.planner import plan_question
from src.query.fallback_planner import PlanningError
from src.query.executor import Executor

class AnswerContract(BaseModel):
    """JSON-safe scalar/entity answer for evaluation; detailed rows remain available."""
    model_config = ConfigDict(strict=True)
    structured_answer: float | str | list[str] | bool | None
    answer_type: Literal['numeric','entity','entity_list','boolean']
    comparability_notes: list[str] = []

    @model_validator(mode='after')
    def consistent(self):
        value=self.structured_answer
        types={'numeric':float,'entity':str,'entity_list':list,'boolean':bool}
        if value is not None and type(value) is not types[self.answer_type]:
            raise ValueError('Structured answer does not match answer_type')
        return self


def answer_contract(result, plan, store):
    rows=result['rows'];last=plan.steps[-1] if plan else None
    entity_aggregate=last is not None and last.action=='aggregate_compare' and last.op in ('max','min','rank','top_k')
    if rows and all(type(r.get('value')) is bool for r in rows):
        kind='boolean';value=rows[0]['value']
    elif rows and (entity_aggregate or 'value' not in rows[0] or len(rows)>1):
        ids=list(dict.fromkeys(r['node_id'] for r in rows))
        ranked_list=entity_aggregate and (last.op=='rank' or (last.op=='top_k' and last.k!=1))
        kind='entity' if len(ids)==1 and not ranked_list else 'entity_list'
        value=ids[0] if kind=='entity' else ids
    else:
        kind='numeric';value=float(rows[0]['value']) if rows else None
    notes=[];labels={}
    for fact in result['retrieved_facts']:
        node=store.graph.nodes[fact['fact_id']]
        if node['node_type']=='MetricObservation':
            labels.setdefault(node['metric_id'],{}).setdefault(node['company_id'],set()).add(node.get('raw_label',''))
    for metric,companies in labels.items():
        if len(companies)>1 and len({label for group in companies.values() for label in group if label})>1:
            notes.append(metric+' uses distinct reported labels: '+'; '.join(company+' = '+', '.join(sorted(group)) for company,group in sorted(companies.items()))+'. Definitions may differ.')
    if result['abstained']: value=None
    return AnswerContract(structured_answer=value,answer_type=kind,comparability_notes=notes).model_dump()

ROOT=Path(__file__).resolve().parents[2]

def synthesize(result: dict, plan, planner_source: str, store) -> dict:
    citations=list(dict.fromkeys(f"[{f['source_doc']}, p. {f['page_num']}]" for f in result['retrieved_facts']))
    values=[];texts=[];entities=[]
    for row in result['rows']:
        id=row.get('node_id');name=store.graph.nodes[id].get('name',id) if id in store.graph else id
        if id and not any(e['node_id']==id for e in entities):entities.append(dict(node_id=id,name=name))
        if 'value' in row:
            value=row['value'];values.append(dict(entity_id=id,value=value) if id else value)
            texts.append((f'{name}: ' if name else '')+f"{value:,.6f}".rstrip('0').rstrip('.')+f" {row['unit']}")
        else:values.append(id);texts.append(name or str(id))
    answer='Abstained: '+result['reason'] if result['abstained'] else '; '.join(texts)+' '+ ' '.join(citations)
    units={row.get('unit') for row in result['rows']}
    return dict(**answer_contract(result,plan,store),answer=answer,answer_value=values[0] if len(values)==1 else values or None,
                unit=next(iter(units)) if len(units)==1 else None,citations=citations,
                retrieved_facts=result['retrieved_facts'],plan=plan.model_dump(exclude_none=True) if plan else None,
                planner_source=planner_source,abstained=result['abstained'],reason=result['reason'],execution_trace=result['trace'],
                answer_entities=entities)

def ask(question: str, *, offline: bool=False, graph_path: Path | None=None, client=None) -> dict:
    store=GraphStore(graph_path or ROOT/'data/graph/kg.json')
    client=client or LLMClient(offline=offline)
    try:
        plan,source=plan_question(question,resolve(question,store),client)
    except PlanningError as error:
        return synthesize(dict(rows=[],trace=[],retrieved_facts=[],abstained=True,reason=str(error)),None,'deterministic_fallback',store)
    return synthesize(Executor(store).execute(plan),plan,source,store)
