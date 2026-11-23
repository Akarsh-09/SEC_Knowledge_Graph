"""Strict, ordered graph query AST and provider/cache-backed planning."""
from __future__ import annotations
import json
import logging
import os
from typing import Annotated, Literal
import httpx
from pydantic import BaseModel, ConfigDict, Field, model_validator
from src.llm_client import LLMClient, OfflineCacheMiss
from config.ontology import CanonicalMetric, DERIVED_FORMULAS, RELATION_TYPES, FISCAL_PERIODS

LOG=logging.getLogger(__name__)
PLANNER_PROMPT_VERSION = "v2"

Binding = str | list[str]
Formula = Literal['OPERATING_MARGIN','NET_MARGIN','GROSS_MARGIN','RD_INTENSITY','DEBT_TO_EQUITY','FREE_CASH_FLOW','YOY_GROWTH','RATIO','DIFF']

class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid')
class Step(Strict):
    output_var: str = Field(pattern=r'^\$[A-Za-z][A-Za-z0-9_]*$')
class LookupMetric(Step):
    action: Literal['lookup_metric']
    company_ids: Binding
    metric_id: str
    period_id: str = Field(pattern=r'^FY20\d{2}$')
class ComputeDerived(Step):
    action: Literal['compute_derived']
    company_ids: Binding
    formula_id: Formula
    period_id: str = Field(pattern=r'^FY20\d{2}$')
    base_period_id: str | None = Field(default=None,pattern=r'^FY20\d{2}$')
    metric_id: str | None = None
    numerator_metric_id: str | None = None
    denominator_metric_id: str | None = None
    @model_validator(mode='after')
    def operands(self):
        if self.formula_id=='YOY_GROWTH' and not self.metric_id: raise ValueError('YOY_GROWTH requires metric_id')
        if self.formula_id in ('RATIO','DIFF') and not (self.numerator_metric_id and self.denominator_metric_id):
            raise ValueError('RATIO/DIFF require numerator_metric_id and denominator_metric_id')
        return self
class TraverseRelation(Step):
    action: Literal['traverse_relation']
    relation_type: str
    direction: Literal['out','in'] = 'out'
    start_nodes: Binding | None = None
    target_node: str | None = None
    restrict_to: Binding | None = None
    @model_validator(mode='after')
    def anchor(self):
        if self.start_nodes is None and self.target_node is None: raise ValueError('Traversal requires an anchor')
        return self
class RelationFilter(Strict):
    relation_type: str
    target_node: str
class FilterCompanies(Step):
    action: Literal['filter_companies']
    company_ids: Binding | None = None
    sector: str | None = None
    relation_filter: RelationFilter | None = None
    metric_id: str | None = None
    period_id: str | None = None
    op: Literal['gt','gte','lt','lte','eq'] | None = None
    threshold: float | None = None
    @model_validator(mode='after')
    def threshold_fields(self):
        fields=[self.metric_id,self.period_id,self.op,self.threshold]
        if any(x is not None for x in fields) and not all(x is not None for x in fields): raise ValueError('Metric threshold requires all four fields')
        return self
class AggregateCompare(Step):
    action: Literal['aggregate_compare']
    input_var: str = Field(pattern=r'^\$[A-Za-z][A-Za-z0-9_]*$')
    op: Literal['max','min','top_k','rank','avg','sum','count','diff','ratio']
    k: int | None = Field(default=None,ge=1)
    @model_validator(mode='after')
    def top(self):
        if self.op=='top_k' and self.k is None: raise ValueError('top_k requires k')
        return self
class Abstain(Step):
    action: Literal['abstain']
    reason: str = Field(min_length=1)

QueryStep = Annotated[Abstain | LookupMetric | ComputeDerived | TraverseRelation | FilterCompanies | AggregateCompare, Field(discriminator='action')]
class GraphQueryPlan(Strict):
    steps: list[QueryStep] = Field(min_length=1,max_length=30)
    @model_validator(mode='after')
    def bindings(self):
        defined=set()
        def references(value):
            if isinstance(value,str) and value.startswith('$'): yield value
            elif isinstance(value,list):
                for item in value: yield from references(item)
            elif isinstance(value,dict):
                for item in value.values(): yield from references(item)
        for step in self.steps:
            data=step.model_dump(exclude={'output_var'})
            if any(ref not in defined for ref in references(data)): raise ValueError('Undefined or forward variable reference')
            if step.output_var in defined: raise ValueError('Duplicate variable binding')
            defined.add(step.output_var)
            for key,value in step.model_dump().items():
                if key in ('metric_id','numerator_metric_id','denominator_metric_id') and value is not None:
                    if value not in {'METRIC:'+m.value for m in CanonicalMetric}: raise ValueError('Unknown metric')
                if key in ('period_id','base_period_id') and value is not None and value not in FISCAL_PERIODS:
                    raise ValueError('Unsupported fiscal period')
            if isinstance(step,TraverseRelation) and step.relation_type not in RELATION_TYPES: raise ValueError('Unknown relation')
            if isinstance(step,FilterCompanies) and step.relation_filter and step.relation_filter.relation_type not in RELATION_TYPES:
                raise ValueError('Unknown relation filter')
        return self

def _templates() -> dict:
    """Illustrative IDs are placeholders; they never encode benchmark answers."""
    lookup=dict(action='lookup_metric',output_var='$values',company_ids=['COMP:A','COMP:B'],metric_id='METRIC:REVENUE',period_id='FY2025')
    scope=dict(action='filter_companies',output_var='$scope',sector='<resolved sector>')
    relation=dict(action='traverse_relation',output_var='$members',relation_type='AUDITED_BY',direction='in',start_nodes=['EXT:AUDITOR'],restrict_to='$scope')
    member_lookup=dict(lookup,company_ids='$members')
    return {
        'single_fact':{'steps':[dict(lookup,company_ids=['COMP:A'])]},
        'ordered_difference_A_minus_B':{'steps':[lookup,dict(action='aggregate_compare',output_var='$answer',input_var='$values',op='diff')]},
        'ordered_ratio_A_divided_by_B':{'steps':[lookup,dict(action='aggregate_compare',output_var='$answer',input_var='$values',op='ratio')]},
        'relation_metric_single_winner':{'steps':[scope,relation,member_lookup,dict(action='aggregate_compare',output_var='$answer',input_var='$values',op='max')]},
        'relation_derived_single_winner':{'steps':[scope,relation,dict(action='compute_derived',output_var='$values',company_ids='$members',formula_id='NET_MARGIN',period_id='FY2025'),dict(action='aggregate_compare',output_var='$answer',input_var='$values',op='min')]},
        'relation_company_list':{'steps':[scope,relation]},
        'relation_company_count':{'steps':[scope,relation,dict(action='aggregate_compare',output_var='$answer',input_var='$members',op='count')]},
    }


def _grounded_plan(plan: GraphQueryPlan, concepts: dict) -> GraphQueryPlan:
    """Reject literal IDs outside the supplied concepts; bindings stay dynamic."""
    allowed=set(concepts.get('company_ids',[])) | set(concepts.get('external_entity_ids',[]))
    for step in plan.steps:
        data=step.model_dump()
        values=[data.get(key) for key in ('company_ids','start_nodes','target_node','restrict_to')]
        if data.get('relation_filter'):values.append(data['relation_filter']['target_node'])
        for value in values:
            for id in (value if isinstance(value,list) else [value]):
                if id is not None and not id.startswith('$') and id not in allowed:
                    raise ValueError('Ungrounded graph entity ID: '+id)
    return plan


def plan_question(question: str, concepts: dict, client: LLMClient, *, allow_live_fallback: bool | None=None) -> tuple[GraphQueryPlan,str]:
    if allow_live_fallback is None:
        allow_live_fallback=os.getenv('PLANNER_ALLOW_LIVE_FALLBACK','false').strip().casefold() in ('1','true','yes')
    system=(f'PLANNER_PROMPT_VERSION={PLANNER_PROMPT_VERSION}. Produce only a JSON graph query plan. '
            'Never answer or calculate. Use only supplied concepts/ontology; never invent IDs or namespaces such as LOC:. '
            'Locations, people, auditors, states and acquired entities are ExternalEntity nodes: use their exact grounded EXT: IDs. '
            'Use ordered steps and $variable bindings, preferably company_ids="$members" rather than ["$members"]. '
            'For a relation filter use direction="in", start_nodes=[the grounded target ID], restrict_to="$scope"; '
            'direction="out", target_node=that ID, restrict_to="$scope" with no start_nodes is equivalent and returns companies. '
            'A company-list question ends at the traversal, not a count; use count only for how many. '
            'Use max/min for a single winner, top_k only for a specified number, and rank for an ordered list. '
            'Use lookup_metric for both companies in the exact question operand order, then aggregate_compare diff for A-B or ratio for A/B. '
            'compute_derived RATIO/DIFF compares two metrics within each company, not two companies. '
            'Percent formulas return numbers on the 0-100 percent scale; debt_to_equity and ratio return dimensionless ratios. '
            'The template IDs and sector below are placeholders: replace them with supplied canonical concepts, never copy placeholders. '
            'DSL templates: '+json.dumps(_templates(),sort_keys=True)+
            ' Validated AST schema: '+json.dumps(GraphQueryPlan.model_json_schema(),sort_keys=True))
    user=json.dumps({'question':question,'concepts':concepts,'metrics':[m.value for m in CanonicalMetric],
                     'formulas':list(DERIVED_FORMULAS)+['FREE_CASH_FLOW','YOY_GROWTH','RATIO','DIFF'],'relations':RELATION_TYPES},sort_keys=True)
    try:
        plan,source=client.structured(system,user,GraphQueryPlan)
        return _grounded_plan(plan,concepts),source
    except OfflineCacheMiss:
        if not getattr(client,'offline',False) and not allow_live_fallback:raise
        from src.query.fallback_planner import fallback_plan
        if getattr(client,'offline',False):LOG.info('planner_source=deterministic_fallback after offline cache miss')
        else:LOG.warning('planner_source=deterministic_fallback; explicit live fallback enabled after OfflineCacheMiss')
        return fallback_plan(question,concepts),'deterministic_fallback'
    except (ValueError,httpx.HTTPError) as error:
        if not allow_live_fallback:raise
        from src.query.fallback_planner import fallback_plan
        LOG.warning('planner_source=deterministic_fallback; explicit live fallback enabled after %s',type(error).__name__)
        return fallback_plan(question,concepts),'deterministic_fallback'
