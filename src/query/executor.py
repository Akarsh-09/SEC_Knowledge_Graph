"""Pure graph execution with active-fact provenance and explicit abstention."""
from __future__ import annotations
import operator
from dataclasses import dataclass, field
from config.ontology import DERIVED_FORMULAS
from src.query.planner import GraphQueryPlan

class MissingFacts(ValueError):
    """Required graph evidence or a defined computation is unavailable."""

@dataclass
class Rows:
    items: list[dict]
    # Scope evidence survives intermediate filters even when individual rows vanish.
    evidence: set[str] = field(default_factory=set)

class Executor:
    def __init__(self, store): self.store=store

    def execute(self, plan: GraphQueryPlan) -> dict:
        bindings={};trace=[];touched={}
        def touch(fact):
            if fact.get('status','active')!='active': raise MissingFacts('Inactive fact selected')
            touched[fact['id']]=fact
            return fact['id']
        def resolve(value):
            if isinstance(value,str) and value.startswith('$'): return bindings[value]
            values=[value] if isinstance(value,str) else value or []
            items={};support=set()
            for item in values:
                rows=resolve(item) if item.startswith('$') else Rows([{'node_id':item,'fact_ids':[]}])
                support.update(rows.evidence)
                for row in rows.items:
                    id=row['node_id']
                    if id not in items:items[id]=dict(row,fact_ids=list(row['fact_ids']))
                    else:items[id]['fact_ids']=list(dict.fromkeys(items[id]['fact_ids']+row['fact_ids']))
            return Rows(list(items.values()),support)
        def evidence(rows):
            return rows.evidence | {id for item in rows.items for id in item['fact_ids']}
        def metric(company, metric_id, period):
            facts=self.store.lookup_metric(company,metric_id,period)
            if not facts: raise MissingFacts(f'Missing {metric_id} for {company} {period}')
            fact=facts[0];touch(fact)
            return fact['analytical_value_usd'],fact['id'],fact['unit']
        def all_companies():
            return Rows([{'node_id':id,'fact_ids':[]} for id,d in self.store.graph.nodes(data=True) if d['node_type']=='Company'])
        try:
            for step in plan.steps:
                action=step.action
                if action=='abstain':
                    trace.append({'action':action,'output_var':step.output_var,'reason':step.reason,'fact_ids':[]})
                    raise MissingFacts(step.reason)
                if action in ('lookup_metric','compute_derived'):
                    source=resolve(step.company_ids);items=[]
                    if not source.items: raise MissingFacts('Empty company scope')
                    for row in source.items:
                        company=row['node_id'];ids=list(row['fact_ids'])
                        if action=='lookup_metric':
                            value,id,unit=metric(company,step.metric_id,step.period_id);ids.append(id)
                        else:
                            formula=step.formula_id
                            if formula=='YOY_GROWTH':
                                current,id,_=metric(company,step.metric_id,step.period_id);ids.append(id)
                                previous,id,_=metric(company,step.metric_id,step.base_period_id or f'FY{int(step.period_id[2:])-1}');ids.append(id)
                                if previous==0: raise MissingFacts('Growth baseline is zero')
                                value=(current-previous)/previous*100;unit='percent'
                            else:
                                operands=DERIVED_FORMULAS.get(formula)
                                if formula=='FREE_CASH_FLOW': operands=('OPERATING_CASH_FLOW','CAPEX')
                                if formula in ('RATIO','DIFF'): operands=(step.numerator_metric_id,step.denominator_metric_id)
                                if not operands: raise MissingFacts('Unsupported formula')
                                values=[];operand_units=[]
                                for operand in operands:
                                    v,id,operand_unit=metric(company,operand if operand.startswith('METRIC:') else 'METRIC:'+operand,step.period_id)
                                    values.append(v);ids.append(id);operand_units.append(operand_unit)
                                if len(set(operand_units))!=1: raise MissingFacts('Incompatible formula units')
                                a,b=values
                                if formula in ('FREE_CASH_FLOW','DIFF'): value=a-b;unit=operand_units[0]
                                else:
                                    if b==0: raise MissingFacts('Division by zero')
                                    value=a/b;unit='ratio'
                                    if formula in ('OPERATING_MARGIN','NET_MARGIN','GROSS_MARGIN','RD_INTENSITY'):value*=100;unit='percent'
                        items.append({'node_id':company,'value':value,'unit':unit,'fact_ids':list(dict.fromkeys(ids))})
                    result=Rows(items,evidence(source))
                elif action=='traverse_relation':
                    outgoing_filter=step.direction=='out' and step.start_nodes is None and step.target_node is not None and step.restrict_to is not None
                    anchor=resolve(step.restrict_to if outgoing_filter else step.start_nodes if step.start_nodes is not None else step.target_node)
                    anchors={r['node_id']:r for r in anchor.items}
                    restriction=resolve(step.restrict_to) if step.restrict_to is not None and not outgoing_filter else None
                    allowed={r['node_id']:r for r in restriction.items} if restriction is not None else None
                    found={}
                    for fact in self.store.relation_claims(step.relation_type):
                        start,end=(fact['company_id'],fact['target_id']) if step.direction=='out' else (fact['target_id'],fact['company_id'])
                        if outgoing_filter:
                            if end!=step.target_node:continue
                            end=start  # Filter returns the company, not the target entity.
                        if start not in anchors or (allowed is not None and end not in allowed): continue
                        id=touch(fact)
                        ids=anchors[start]['fact_ids']+[id]+(allowed[end]['fact_ids'] if allowed is not None else [])
                        found.setdefault(end,{'node_id':end,'fact_ids':[]})['fact_ids'].extend(ids)
                    for r in found.values():r['fact_ids']=list(dict.fromkeys(r['fact_ids']))
                    result=Rows(list(found.values()),evidence(anchor)|(evidence(restriction) if restriction is not None else set()))
                    if not result.items:raise MissingFacts(f'No supporting {step.relation_type} claims for requested traversal')
                elif action=='filter_companies':
                    source=resolve(step.company_ids) if step.company_ids is not None else all_companies()
                    items=[];support=evidence(source)
                    for row in source.items:
                        id=row['node_id'];data=self.store.graph.nodes.get(id,{})
                        if data.get('node_type')!='Company':continue
                        if step.sector and data['sector']!=step.sector:continue
                        ids=list(row['fact_ids'])
                        if step.relation_filter:
                            matches=[f for f in self.store.lookup_relation(id,step.relation_filter.relation_type) if f['target_id']==step.relation_filter.target_node]
                            if not matches:continue
                            ids.append(touch(matches[0]))
                        if step.metric_id:
                            value,fid,_=metric(id,step.metric_id,step.period_id);ids.append(fid);support.add(fid)
                            if not {'gt':operator.gt,'gte':operator.ge,'lt':operator.lt,'lte':operator.le,'eq':operator.eq}[step.op](value,step.threshold):continue
                        items.append({'node_id':id,'fact_ids':ids})
                    result=Rows(items,support)
                    if not items:raise MissingFacts('No companies satisfy the supported filters')
                elif action=='aggregate_compare':
                    source=resolve(step.input_var);items=source.items;support=evidence(source)
                    if not items:raise MissingFacts('Nothing to aggregate')
                    if step.op=='count':result=Rows([{'value':len({r['node_id'] for r in items}),'unit':'count','fact_ids':sorted(support)}],support)
                    else:
                        if any('value' not in r for r in items):raise MissingFacts('Numeric aggregation requires metric rows')
                        if len({r['unit'] for r in items})!=1:raise MissingFacts('Incompatible aggregation units')
                        ordered=sorted(items,key=lambda r:(-r['value'],r.get('node_id','')))
                        if step.op in ('max','min'):
                            extreme=(max if step.op=='max' else min)(r['value'] for r in items)
                            result=Rows([r for r in ordered if r['value']==extreme],support)
                        elif step.op in ('rank','top_k'):
                            selected=ordered if step.op=='rank' else ordered[:step.k]
                            result=Rows([dict(r,rank=1+sum(x['value']>r['value'] for x in items)) for r in selected],support)
                        else:
                            vals=[r['value'] for r in items]
                            if step.op in ('diff','ratio'):
                                if len(vals)!=2:raise MissingFacts('Difference/ratio requires exactly two rows')
                                if step.op=='ratio' and vals[1]==0:raise MissingFacts('Division by zero')
                                # Use source order, never the ranking sort order above.
                                value=vals[0]-vals[1] if step.op=='diff' else vals[0]/vals[1]
                            else:value=sum(vals)/(len(vals) if step.op=='avg' else 1)
                            result=Rows([{'value':value,'unit':'ratio' if step.op=='ratio' else items[0]['unit'],'fact_ids':sorted(support)}],support)
                bindings[step.output_var]=result
                trace.append({'action':action,'output_var':step.output_var,'rows':result.items,'fact_ids':sorted(evidence(result))})
            final=bindings[plan.steps[-1].output_var]
            if not final.items:raise MissingFacts('No supported results')
            if not touched:raise MissingFacts('No source-backed facts support this result')
            return dict(rows=final.items,trace=trace,retrieved_facts=self._provenance(touched),abstained=False,reason=None)
        except MissingFacts as error:
            return dict(rows=[],trace=trace,retrieved_facts=self._provenance(touched),abstained=True,reason=str(error))

    @staticmethod
    def _provenance(touched):
        return [dict(fact_id=id,source_doc=f['source_doc'],page_num=f['page_num'],company_id=f['company_id'],
                     predicate=f.get('metric_id',f.get('relation_type')),period=f.get('period'),
                     value=f.get('analytical_value_usd',f.get('target_name')),snippet=f['snippet']) for id,f in touched.items()]
