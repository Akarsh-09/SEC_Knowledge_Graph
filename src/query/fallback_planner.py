"""Conservative offline planning for standard financial and graph questions."""
import re
from src.query.planner import GraphQueryPlan

class PlanningError(ValueError):
    """The rule planner cannot unambiguously express this question."""

def _fallback_plan(question: str, c: dict) -> GraphQueryPlan:
    text=question.casefold();steps=[]
    companies=c['company_ids'];periods=c['period_ids'];metrics=c['metric_ids'];relations=c['relation_types'];entities=c['external_entity_ids']
    if len(relations)>1: raise PlanningError('Specify one relation per fallback question')
    def add(action,**kwargs):
        var=f'$step{len(steps)+1}';steps.append(dict(action=action,output_var=var,**kwargs));return var
    scope=companies
    if c['sectors']:
        if len(c['sectors'])!=1: raise PlanningError('Specify one sector')
        scope=add('filter_companies',sector=c['sectors'][0],company_ids=companies or None)
    if relations and entities:
        if len(relations)!=1 or len(entities)!=1: raise PlanningError('Ambiguous relation filter')
        scope=add('traverse_relation',relation_type=relations[0],direction='in',target_node=entities[0],restrict_to=scope or None)
    formulas=c['formula_ids']
    # Difference between companies is an aggregate, not a within-company formula.
    specific=[f for f in formulas if f not in ('DIFF','RATIO')]
    if len(specific)>1: raise PlanningError('Ambiguous formula')
    formula=specific[0] if specific else None
    if formula is None and 'RATIO' in formulas: formula='RATIO'
    if formula is None and 'DIFF' in formulas and len(metrics)==2: formula='DIFF'
    if len(periods)>1 and formula!='YOY_GROWTH': raise PlanningError('Multiple periods require an explicit supported growth question')
    threshold=re.search(r'\b(above|over|greater than|below|under|less than|at least|at most)\s*\$?([\d,.]+)\s*(trillion|billion|million|thousand)?',text)
    if threshold:
        if not scope or len(metrics)!=1 or not periods: raise PlanningError('Threshold requires a company scope, one metric and a fiscal year')
        multiplier={'trillion':1e12,'billion':1e9,'million':1e6,'thousand':1e3,None:1}[threshold[3]]
        op={'above':'gt','over':'gt','greater than':'gt','below':'lt','under':'lt','less than':'lt','at least':'gte','at most':'lte'}[threshold[1]]
        scope=add('filter_companies',company_ids=scope,metric_id=metrics[0],period_id=periods[0],op=op,threshold=float(threshold[2].replace(',',''))*multiplier)
        if not formula and not re.search(r'\b(highest|lowest|rank|top|average|sum)\b',text):
            if 'how many' in text:add('aggregate_compare',input_var=scope,op='count')
            return GraphQueryPlan.model_validate({'steps':steps})
    quantitative=bool(formula or metrics)
    if not quantitative:
        if relations and not entities and scope:
            add('traverse_relation',relation_type=relations[0],start_nodes=scope)
        elif not steps: raise PlanningError('No supported graph lookup was resolved')
    else:
        if not scope: raise PlanningError('Specify companies or a sector/relation filter')
        if not periods: raise PlanningError('Specify a fiscal year; the planner will not guess one')
        period=max(periods) if formula=='YOY_GROWTH' else periods[0]
        if formula:
            kwargs=dict(company_ids=scope,formula_id=formula,period_id=period)
            if formula=='YOY_GROWTH':
                if len(metrics)!=1: raise PlanningError('Growth requires exactly one metric')
                kwargs.update(metric_id=metrics[0],base_period_id=min(periods) if len(periods)>1 else f'FY{int(period[2:])-1}')
            if formula in ('RATIO','DIFF'):
                if len(metrics)!=2: raise PlanningError('Ratio/difference requires two metrics')
                # Preserve question operand order rather than ontology iteration order.
                ordered=metrics
                kwargs.update(numerator_metric_id=ordered[0],denominator_metric_id=ordered[1])
            result=add('compute_derived',**kwargs)
        else:
            if len(metrics)!=1: raise PlanningError('Specify exactly one metric')
            result=add('lookup_metric',company_ids=scope,metric_id=metrics[0],period_id=period)
        op=None
        if re.search(r'\b(highest|largest|maximum|most)\b',text): op='max'
        elif re.search(r'\b(lowest|smallest|minimum|least)\b',text): op='min'
        elif re.search(r'\baverage\b',text):op='avg'
        elif re.search(r'\b(sum|combined)\b',text):op='sum'
        elif 'difference' in text and len(companies)==2 and formula!='DIFF':op='diff'
        elif re.search(r'\brank\b',text):op='rank'
        top=re.search(r'\btop\s+(\d+)\b',text)
        if top:add('aggregate_compare',input_var=result,op='top_k',k=int(top[1]))
        elif op:add('aggregate_compare',input_var=result,op=op)
    if re.search(r'\bhow many\b',text):add('aggregate_compare',input_var=steps[-1]['output_var'],op='count')
    return GraphQueryPlan.model_validate({'steps':steps})


def fallback_plan(question: str, c: dict) -> GraphQueryPlan:
    """Reject recognized unsupported qualifiers; this is not a full semantic parser."""
    text=question.casefold()
    try:
        unsupported = r'\b(?:automotive|segment[- ]level|segment revenue|regional|restated|trailing twelve|annualized|continuing operations|adjusted|non[- ]gaap|constant currency|inflation[- ]adjusted|organic|excluding|exclude|except|without|not audited|quarterly|quarter|q[1-4]|forecast|predicted|projected|median|weighted average|geographic|european|asian|domestic|international|only if)\b'
        match=re.search(unsupported,text)
        if match: raise PlanningError('Unsupported constraint: '+match[0])
        if c.get('unresolved_qualifiers'): raise PlanningError('Unresolved qualifier(s): '+', '.join(c['unresolved_qualifiers']))
        if re.search(r'\b(?:is|are|does|did|has|was|were)\b',text.split('?')[0][:6]) and not text.startswith(('what','which','where','who','how','among','rank')):
            raise PlanningError('Boolean question planning is not supported by the fallback')
        return _fallback_plan(question,c)
    except PlanningError as error:
        return GraphQueryPlan.model_validate({'steps':[{'action':'abstain','output_var':'$abstain','reason':str(error)}]})
