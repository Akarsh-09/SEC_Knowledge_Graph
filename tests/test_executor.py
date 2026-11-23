"""Graph-only reasoning, provenance, planning modes and abstention regression tests."""
import hashlib
import json
import sqlite3
from unittest.mock import patch
import httpx
import pytest
from src.graph.schema import MetricObservationNode,RelationClaimNode
from src.graph.builder import build
from src.graph.store import GraphStore
from src.llm_client import LLMClient
from src.query.planner import GraphQueryPlan,plan_question
from src.query.concept_resolver import resolve
from src.query.executor import Executor
from src.query.synthesizer import ask

@pytest.fixture
def graph(tmp_path):
    companies=[dict(ticker=t,name=n,sector='Semiconductors',cik=f'{i:010}') for i,(t,n) in enumerate([('AAA','Alpha'),('BBB','Beta')],1)]
    facts=[]
    def metric(t,m,period,value):
        facts.append(MetricObservationNode(id=f'FACT:{t}-{m}-{period}',company_id='COMP:'+t,source_doc=t+'.pdf',page_num=2,
            section='Item 8',snippet=f'{m} {value}',metric_id='METRIC:'+m,period=period,value_raw=value,
            scale_multiplier=1,value_usd=value,audited=True))
    for t,rev,rd,ocf,capex in [('AAA',100,10,30,-5),('BBB',200,40,60,10)]:
        for m,v in [('REVENUE',rev),('RD_EXPENSE',rd),('OPERATING_CASH_FLOW',ocf),('CAPEX',capex),('NET_INCOME',rev/5)]:metric(t,m,'FY2025',v)
        metric(t,'REVENUE','FY2024',rev/2)
        facts.append(RelationClaimNode(id='FACT:'+t+'-audit',company_id='COMP:'+t,source_doc=t+'.pdf',page_num=3,
            section='Auditor Report',snippet='Ernst & Young LLP',relation_type='AUDITED_BY',target_id='EXT:EY',target_name='Ernst & Young LLP'))
    path=tmp_path/'kg.json';build(companies,facts,path)
    return path

def execute(graph,steps):return Executor(GraphStore(graph)).execute(GraphQueryPlan.model_validate({'steps':steps}))

def test_single_fact(graph):
    result=execute(graph,[dict(action='lookup_metric',output_var='$a',company_ids=['COMP:AAA'],metric_id='METRIC:REVENUE',period_id='FY2025')])
    assert result['rows'][0]['value']==100
    assert [f['fact_id'] for f in result['retrieved_facts']]==['FACT:AAA-REVENUE-FY2025']

@pytest.mark.parametrize('company,expected',[('AAA',25),('BBB',50)])
def test_free_cash_flow_sign(graph,company,expected):
    r=execute(graph,[dict(action='compute_derived',output_var='$a',company_ids=['COMP:'+company],formula_id='FREE_CASH_FLOW',period_id='FY2025')])
    assert r['rows'][0]['value']==expected
    assert len(r['retrieved_facts'])==2

def test_yoy(graph):
    r=execute(graph,[dict(action='compute_derived',output_var='$a',company_ids=['COMP:AAA'],formula_id='YOY_GROWTH',metric_id='METRIC:REVENUE',period_id='FY2025')])
    assert r['rows'][0]['value']==100
    assert len(r['retrieved_facts'])==2

def test_multihop_filter_rank(graph):
    r=execute(graph,[
        dict(action='traverse_relation',output_var='$auditor',start_nodes=['COMP:AAA'],relation_type='AUDITED_BY'),
        dict(action='traverse_relation',output_var='$companies',start_nodes='$auditor',relation_type='AUDITED_BY',direction='in'),
        dict(action='filter_companies',output_var='$filtered',company_ids='$companies',sector='Semiconductors',metric_id='METRIC:REVENUE',period_id='FY2025',op='gt',threshold=50),
        dict(action='compute_derived',output_var='$ratios',company_ids='$filtered',formula_id='RD_INTENSITY',period_id='FY2025'),
        dict(action='aggregate_compare',output_var='$winner',input_var='$ratios',op='max')])
    assert not r['abstained']
    assert r['rows'][0]['node_id']=='COMP:BBB' and r['rows'][0]['value']==20
    assert len(r['retrieved_facts'])==6

def test_missing_data(graph):
    r=execute(graph,[dict(action='lookup_metric',output_var='$a',company_ids=['COMP:AAA'],metric_id='METRIC:TOTAL_ASSETS',period_id='FY2025')])
    assert r['abstained'] and not r['rows']

def test_cross_company_and_offline_fallback(graph,tmp_path):
    client=LLMClient(offline=True,cache_path=tmp_path/'cache.sqlite')
    with patch('httpx.Client',side_effect=AssertionError('network forbidden')):
        r=ask('Which had the highest revenue, Alpha or Beta, in FY2025?',graph_path=graph,client=client)
    assert r['planner_source']=='deterministic_fallback'
    assert r['answer_value']['entity_id']=='COMP:BBB'
    assert len(r['retrieved_facts'])==2
    assert 'BBB.pdf, p. 2' in r['answer']

def test_live_then_cache_planner(graph,tmp_path):
    store=GraphStore(graph);question='Alpha revenue FY2025';concepts=resolve(question,store)
    payload={'steps':[dict(action='lookup_metric',output_var='$a',company_ids=['COMP:AAA'],metric_id='METRIC:REVENUE',period_id='FY2025')]}
    transport=httpx.MockTransport(lambda r:httpx.Response(200,json={'choices':[{'message':{'content':json.dumps(payload)}}]}))
    http=httpx.Client(transport=transport)
    path=tmp_path/'cache.sqlite';client=LLMClient(api_key='test',model='test',cache_path=path)
    with patch('httpx.Client',return_value=http):
        plan,source=plan_question(question,concepts,client)
    assert source=='llm_live'
    offline=LLMClient(offline=True,model='test',cache_path=path)
    with patch('httpx.Client',side_effect=AssertionError('network forbidden')):
        cached,source=plan_question(question,concepts,offline)
    assert source=='llm_cache' and cached==plan

def test_plan_rejects_forward_reference():
    with pytest.raises(ValueError):GraphQueryPlan.model_validate({'steps':[dict(action='aggregate_compare',output_var='$a',input_var='$missing',op='count')]})

@pytest.mark.parametrize('op,expected',[('sum',300),('avg',150),('min',100),('diff',-100)])
def test_aggregates(graph,op,expected):
    r=execute(graph,[dict(action='lookup_metric',output_var='$a',company_ids=['COMP:AAA','COMP:BBB'],metric_id='METRIC:REVENUE',period_id='FY2025'),dict(action='aggregate_compare',output_var='$b',input_var='$a',op=op)])
    assert r['rows'][0]['value']==expected

def test_fallback_relation_and_derived(graph,tmp_path):
    client=LLMClient(offline=True,cache_path=tmp_path/'cache.sqlite')
    r=ask('Among Alpha and Beta audited by EY, which had the highest R&D intensity in FY2025?',graph_path=graph,client=client)
    assert not r['abstained'] and r['answer_value']['value']==20
    assert len(r['retrieved_facts'])==6


def test_threshold_fallback_and_count(graph,tmp_path):
    client=LLMClient(offline=True,cache_path=tmp_path/'cache.sqlite')
    r=ask('How many of Alpha and Beta audited by EY had revenue above 150 in FY2025?',graph_path=graph,client=client)
    assert not r['abstained'] and r['answer_value']==1
    # Both metric tests were required, including the excluded company.
    assert len(r['retrieved_facts'])==4


def test_difference_preserves_question_order(graph,tmp_path):
    client=LLMClient(offline=True,cache_path=tmp_path/'cache.sqlite')
    r=ask('What is the difference in revenue between Beta and Alpha in FY2025?',graph_path=graph,client=client)
    assert not r['abstained'] and r['answer_value']==100


def test_no_guessed_year(graph,tmp_path):
    client=LLMClient(offline=True,cache_path=tmp_path/'cache.sqlite')
    r=ask('What was Alpha revenue?',graph_path=graph,client=client)
    assert r['abstained'] and not r['retrieved_facts']


def test_rank_top_k_and_ratio(graph):
    r=execute(graph,[dict(action='compute_derived',output_var='$a',company_ids=['COMP:AAA','COMP:BBB'],formula_id='RATIO',numerator_metric_id='METRIC:RD_EXPENSE',denominator_metric_id='METRIC:REVENUE',period_id='FY2025'),dict(action='aggregate_compare',output_var='$b',input_var='$a',op='top_k',k=1)])
    assert r['rows'][0]['node_id']=='COMP:BBB' and r['rows'][0]['value']==.2
    assert len(r['retrieved_facts'])==4


def test_sector_alias_and_yoy_order(graph,tmp_path):
    store=GraphStore(graph)
    assert resolve('semiconductor companies',store)['sectors']==['Semiconductors']
    client=LLMClient(offline=True,cache_path=tmp_path/'c.sqlite')
    r=ask('What was Alpha revenue growth from FY2024 to FY2025?',graph_path=graph,client=client)
    assert not r['abstained'] and r['answer_value']['value']==100


def test_ratio_alias_operand_order(graph,tmp_path):
    client=LLMClient(offline=True,cache_path=tmp_path/'c.sqlite')
    r=ask('What was Alpha ratio of R&D expense to net sales in FY2025?',graph_path=graph,client=client)
    assert not r['abstained'] and r['answer_value']['value']==.1


@pytest.mark.parametrize('formula,numerator,denominator,expected',[
    ('OPERATING_MARGIN','OPERATING_INCOME','REVENUE',25),
    ('NET_MARGIN','NET_INCOME','REVENUE',25),
    ('GROSS_MARGIN','GROSS_PROFIT','REVENUE',25),
    ('DEBT_TO_EQUITY','LONG_TERM_DEBT','SHAREHOLDERS_EQUITY',.25),
    ('DIFF','REVENUE','COST_OF_REVENUE',-75)])
def test_formula_arithmetic(graph,formula,numerator,denominator,expected):
    store=GraphStore(graph)
    # Reuse validated fixture observations with distinct metric bindings.
    original=store.lookup_metric('COMP:AAA','METRIC:REVENUE','FY2025')[0]
    for metric_id,value in [(numerator,25),(denominator,100)]:
        fact=dict(original,id='FACT:'+metric_id,metric_id='METRIC:'+metric_id,value_usd=value,analytical_value_usd=value)
        store.metrics[('COMP:AAA','METRIC:'+metric_id,'FY2025')]=[fact]
    data=dict(action='compute_derived',output_var='$a',company_ids=['COMP:AAA'],formula_id=formula,period_id='FY2025')
    if formula=='DIFF': data.update(numerator_metric_id='METRIC:'+numerator,denominator_metric_id='METRIC:'+denominator)
    result=Executor(store).execute(GraphQueryPlan.model_validate({'steps':[data]}))
    assert result['rows'][0]['value']==expected


def test_zero_denominator(graph):
    store=GraphStore(graph)
    store.metrics[('COMP:AAA','METRIC:REVENUE','FY2025')][0]['analytical_value_usd']=0
    result=Executor(store).execute(GraphQueryPlan.model_validate({'steps':[dict(action='compute_derived',output_var='$a',company_ids=['COMP:AAA'],formula_id='NET_MARGIN',period_id='FY2025')]}))
    assert result['abstained'] and 'zero' in result['reason'].lower()


@pytest.mark.parametrize('q',[
    'What was Alpha adjusted revenue in FY2025?',
    'Among Alpha and MysteryCorp, which had the highest revenue in FY2025?',
    'What was Alpha revenue in Q1 FY2025?',
    'Among AAA and TSLA, which had the highest revenue in FY2025?'])
def test_guarded_abstention_plan(graph,tmp_path,q):
    client=LLMClient(offline=True,cache_path=tmp_path/'cache.sqlite')
    result=ask(q,graph_path=graph,client=client)
    assert result['abstained'] and result['structured_answer'] is None
    assert result['plan']['steps'][0]['action']=='abstain'
    assert not result['retrieved_facts']


def test_structured_answer_contract(graph,tmp_path):
    client=LLMClient(offline=True,cache_path=tmp_path/'cache.sqlite')
    numeric=ask('Alpha revenue FY2025',graph_path=graph,client=client)
    assert type(numeric['structured_answer']) is float and numeric['answer_type']=='numeric'
    winner=ask('Which had the highest revenue, Alpha or Beta, in FY2025?',graph_path=graph,client=client)
    assert winner['structured_answer']=='COMP:BBB' and winner['answer_type']=='entity'
    ranked=ask('Rank Alpha and Beta by revenue in FY2025',graph_path=graph,client=client)
    assert ranked['structured_answer']==['COMP:BBB','COMP:AAA'] and ranked['answer_type']=='entity_list'


def test_unresolved_metric_scope_guard(graph,tmp_path):
    client=LLMClient(offline=True,cache_path=tmp_path/'cache.sqlite')
    result=ask('What was Alpha automotive revenue in FY2025?',graph_path=graph,client=client)
    assert result['abstained'] and 'Unsupported constraint' in result['reason']


def test_distinct_label_comparability_note(graph,tmp_path):
    from src.query.synthesizer import synthesize
    store=GraphStore(graph)
    a=store.lookup_metric('COMP:AAA','METRIC:REVENUE','FY2025')[0]
    b=store.lookup_metric('COMP:BBB','METRIC:REVENUE','FY2025')[0]
    a['raw_label']='Revenue';b['raw_label']='Total net revenue'
    plan=GraphQueryPlan.model_validate({'steps':[dict(action='lookup_metric',output_var='$a',company_ids=['COMP:AAA','COMP:BBB'],metric_id='METRIC:REVENUE',period_id='FY2025')]})
    result=Executor(store).execute(plan)
    # Index dictionaries and graph nodes share data after GraphStore loading.
    output=synthesize(result,plan,'deterministic_fallback',store)
    assert len(output['comparability_notes'])==1
    assert 'Total net revenue' in output['comparability_notes'][0]


def test_known_uppercase_company_and_metric_not_unresolved(graph,tmp_path):
    client=LLMClient(offline=True,cache_path=tmp_path/'cache.sqlite')
    result=ask('What was ALPHA CAPEX in FY2025?',graph_path=graph,client=client)
    assert not result['abstained'] and result['structured_answer']==5


@pytest.mark.parametrize('op,expected', [('diff', 100), ('ratio', 2)])
def test_cross_company_arithmetic_keeps_explicit_operand_order(graph, op, expected):
    steps=[dict(action='lookup_metric',output_var='$values',company_ids=['COMP:BBB','COMP:AAA'],metric_id='METRIC:REVENUE',period_id='FY2025'),
           dict(action='aggregate_compare',output_var='$answer',input_var='$values',op=op)]
    result=execute(graph,steps)
    assert not result['abstained'] and result['rows'][0]['value']==expected
    assert result['rows'][0]['unit']==('ratio' if op=='ratio' else 'USD')
    assert [r['node_id'] for r in result['trace'][0]['rows']]==['COMP:BBB','COMP:AAA']
    assert [f['company_id'] for f in result['retrieved_facts']]==['COMP:BBB','COMP:AAA']
    steps[0]['company_ids'].reverse()
    assert execute(graph,steps)['rows'][0]['value']==(-100 if op=='diff' else .5)


@pytest.mark.parametrize('direction,start,target', [('out',None,'EXT:EY'),('in',['EXT:EY'],None),('in',None,'EXT:EY')])
def test_symmetric_relation_filter_and_wrapped_variable(graph,direction,start,target):
    store=GraphStore(graph)
    # An inactive matching claim must never become a member or supporting fact.
    store.lookup_relation('COMP:BBB','AUDITED_BY')[0]['status']='corroborating'
    steps=[dict(action='filter_companies',output_var='$scope',sector='Semiconductors'),
           dict(action='traverse_relation',output_var='$audited',relation_type='AUDITED_BY',direction=direction,start_nodes=start,target_node=target,restrict_to=['$scope']),
           dict(action='lookup_metric',output_var='$values',company_ids=['$audited'],metric_id='METRIC:REVENUE',period_id='FY2025')]
    result=Executor(store).execute(GraphQueryPlan.model_validate({'steps':steps}))
    assert not result['abstained'] and result['rows'][0]['node_id']=='COMP:AAA'
    assert {f['fact_id'] for f in result['retrieved_facts']}=={'FACT:AAA-audit','FACT:AAA-REVENUE-FY2025'}


def test_wrapped_company_binding_keeps_order_and_provenance(graph):
    steps=[dict(action='filter_companies',output_var='$scope',company_ids=['COMP:BBB','COMP:AAA']),
           dict(action='lookup_metric',output_var='$values',company_ids=['$scope'],metric_id='METRIC:REVENUE',period_id='FY2025'),
           dict(action='aggregate_compare',output_var='$answer',input_var='$values',op='ratio')]
    result=execute(graph,steps)
    assert not result['abstained'] and result['rows'][0]['value']==2
    assert len(result['retrieved_facts'])==2


def test_cross_company_ratio_abstains_on_zero_and_wrong_arity(graph):
    store=GraphStore(graph)
    store.lookup_metric('COMP:AAA','METRIC:REVENUE','FY2025')[0]['analytical_value_usd']=0
    steps=[dict(action='lookup_metric',output_var='$values',company_ids=['COMP:BBB','COMP:AAA'],metric_id='METRIC:REVENUE',period_id='FY2025'),
           dict(action='aggregate_compare',output_var='$answer',input_var='$values',op='ratio')]
    result=Executor(store).execute(GraphQueryPlan.model_validate({'steps':steps}))
    assert result['abstained'] and 'zero' in result['reason'].lower() and len(result['retrieved_facts'])==2
    steps[0]['company_ids']=['COMP:BBB']
    result=execute(graph,steps)
    assert result['abstained'] and 'exactly two' in result['reason']


@pytest.mark.parametrize('op,k,expected', [('max',None,'COMP:BBB'),('min',None,'COMP:AAA'),('top_k',1,'COMP:BBB')])
def test_single_winner_aggregates_are_scalar_entities(graph,op,k,expected):
    from src.query.synthesizer import synthesize
    store=GraphStore(graph)
    plan=GraphQueryPlan.model_validate({'steps':[
        dict(action='lookup_metric',output_var='$values',company_ids=['COMP:AAA','COMP:BBB'],metric_id='METRIC:REVENUE',period_id='FY2025'),
        dict(action='aggregate_compare',output_var='$answer',input_var='$values',op=op,k=k)]})
    result=synthesize(Executor(store).execute(plan),plan,'llm_cache',store)
    assert result['answer_type']=='entity' and result['structured_answer']==expected


def test_external_answer_preserves_graph_id_and_display_name(graph):
    from src.query.synthesizer import synthesize
    store=GraphStore(graph)
    plan=GraphQueryPlan.model_validate({'steps':[dict(action='traverse_relation',output_var='$answer',start_nodes=['COMP:AAA'],relation_type='AUDITED_BY')]})
    result=synthesize(Executor(store).execute(plan),plan,'llm_cache',store)
    assert result['structured_answer']=='EXT:EY'
    assert result['answer_entities']==[{'node_id':'EXT:EY','name':'Ernst & Young LLP'}]
    assert 'Ernst & Young LLP' in result['answer']


@pytest.mark.parametrize('phrase,expected', [
    ('headquartered in Seattle, WA','EXT:SEATTLE_WASHINGTON'),
    ('headquartered in seattle, washington','EXT:SEATTLE_WASHINGTON'),
    ('incorporated in Delaware','EXT:DELAWARE'),
    ('acquired Nimbus','EXT:NIMBUS_HOLDING_LIMITED'),
    ('audited by EY','EXT:EY')])
def test_external_concepts_are_grounded_to_existing_nodes(graph,phrase,expected):
    store=GraphStore(graph)
    for id,name in [('EXT:SEATTLE_WASHINGTON','Seattle, Washington'),('EXT:WASHINGTON','Washington'),('EXT:DELAWARE','Delaware'),('EXT:NIMBUS','Nimbus'),('EXT:NIMBUS_HOLDING_LIMITED','Nimbus Holding Limited')]:
        store.graph.add_node(id,node_type='ExternalEntity',name=name)
    concepts=resolve('Which Alpha company is '+phrase+'?',store)
    assert concepts['external_entity_ids']==[expected]
    assert any(e['node_id']==expected and e['name']==store.graph.nodes[expected]['name'] for e in concepts['external_entities'])
    assert 'WA' not in concepts['unresolved_qualifiers']
    assert all(id in store.graph for id in concepts['external_entity_ids'])


def test_external_resolver_does_not_invent_aliases_or_match_prepositions(graph):
    store=GraphStore(graph)
    for state in ['Indiana','Oregon','Maine']:
        store.graph.add_node('EXT:'+state.upper(),node_type='ExternalEntity',name=state)
    concepts=resolve('What was Alpha or Beta revenue in FY2025?',store)
    assert not concepts['external_entity_ids']
    assert not resolve('Which company depends on TSMC?',store)['external_entity_ids']


def test_planner_v2_templates_and_grounded_ids_reach_provider(graph):
    from src.query.planner import PLANNER_PROMPT_VERSION,_templates
    for template in _templates().values():GraphQueryPlan.model_validate(template)
    captured=[]
    class Client:
        offline=False
        def structured(self,system,user,schema):
            captured.append((system,json.loads(user)))
            return GraphQueryPlan.model_validate({'steps':[dict(action='lookup_metric',output_var='$answer',company_ids=['COMP:AAA'],metric_id='METRIC:REVENUE',period_id='FY2025')]}),'llm_live'
    store=GraphStore(graph)
    store.graph.add_node('EXT:SEATTLE_WASHINGTON',node_type='ExternalEntity',name='Seattle, Washington')
    concepts=resolve('Alpha revenue FY2025, headquartered in Seattle, WA',store)
    _,source=plan_question('a synthetic question',concepts,Client())
    system,user=captured[0]
    assert PLANNER_PROMPT_VERSION=='v2' and 'PLANNER_PROMPT_VERSION=v2' in system
    assert 'EXT:SEATTLE_WASHINGTON' in user['concepts']['external_entity_ids']
    assert 'ordered_difference_A_minus_B' in system and 'ordered_ratio_A_divided_by_B' in system
    assert 'relation_company_list' in system and 'relation_company_count' in system
    assert source=='llm_live'


def test_live_planning_failure_is_closed_unless_explicitly_configured(graph,monkeypatch,caplog):
    from src.llm_client import StructuredOutputError
    class Client:
        offline=False
        def structured(self,*args):raise StructuredOutputError('bad provider JSON')
    question='Alpha revenue FY2025';concepts=resolve(question,GraphStore(graph))
    monkeypatch.delenv('PLANNER_ALLOW_LIVE_FALLBACK',raising=False)
    with pytest.raises(StructuredOutputError):plan_question(question,concepts,Client())
    plan,source=plan_question(question,concepts,Client(),allow_live_fallback=True)
    assert source=='deterministic_fallback' and plan.steps[0].action=='lookup_metric'
    assert 'planner_source=deterministic_fallback' in caplog.text
    monkeypatch.setenv('PLANNER_ALLOW_LIVE_FALLBACK','true')
    assert plan_question(question,concepts,Client())[1]=='deterministic_fallback'
    with pytest.raises(StructuredOutputError):plan_question(question,concepts,Client(),allow_live_fallback=False)


@pytest.mark.parametrize('target',['LOC:SEATTLE_WASHINGTON','EXT:INVENTED_LOCATION'])
def test_live_planner_rejects_ungrounded_entity_ids(graph,target):
    class Client:
        offline=False
        def structured(self,*args):
            plan=GraphQueryPlan.model_validate({'steps':[dict(action='traverse_relation',output_var='$answer',relation_type='HEADQUARTERED_IN',direction='in',target_node=target)]})
            return plan,'llm_live'
    store=GraphStore(graph)
    store.graph.add_node('EXT:SEATTLE_WASHINGTON',node_type='ExternalEntity',name='Seattle, Washington')
    with pytest.raises(ValueError,match='Ungrounded graph entity ID'):
        plan_question('headquartered in Seattle, WA',resolve('headquartered in Seattle, WA',store),Client(),allow_live_fallback=False)


def test_one_row_rank_stays_list_and_tied_extreme_keeps_all_winners(graph):
    from src.query.synthesizer import synthesize
    store=GraphStore(graph)
    plan=GraphQueryPlan.model_validate({'steps':[
        dict(action='lookup_metric',output_var='$values',company_ids=['COMP:AAA'],metric_id='METRIC:REVENUE',period_id='FY2025'),
        dict(action='aggregate_compare',output_var='$answer',input_var='$values',op='rank')]})
    result=synthesize(Executor(store).execute(plan),plan,'llm_cache',store)
    assert result['answer_type']=='entity_list' and result['structured_answer']==['COMP:AAA']
    store.lookup_metric('COMP:BBB','METRIC:REVENUE','FY2025')[0]['analytical_value_usd']=100
    data=plan.model_dump();data['steps'][0]['company_ids']=['COMP:AAA','COMP:BBB'];data['steps'][1]['op']='max'
    plan=GraphQueryPlan.model_validate(data)
    result=synthesize(Executor(store).execute(plan),plan,'llm_cache',store)
    assert result['answer_type']=='entity_list' and result['structured_answer']==['COMP:AAA','COMP:BBB']


def test_uppercase_prepositions_are_not_external_state_mentions(graph):
    store=GraphStore(graph)
    for state in ['Indiana','Oregon']:
        store.graph.add_node('EXT:'+state.upper(),node_type='ExternalEntity',name=state)
    assert not resolve('WHAT WAS ALPHA OR BETA REVENUE IN FY2025?',store)['external_entity_ids']
    assert resolve('Which company is incorporated in OR?',store)['external_entity_ids']==['EXT:OREGON']


def test_distinct_legal_forms_remain_ambiguous_and_separate_state_mention_survives(graph):
    store=GraphStore(graph)
    for id,name in [('EXT:NIMBUS_LIMITED','Nimbus Limited'),('EXT:NIMBUS_LLC','Nimbus LLC'),('EXT:SEATTLE_WASHINGTON','Seattle, Washington'),('EXT:WASHINGTON','Washington')]:
        store.graph.add_node(id,node_type='ExternalEntity',name=name)
    assert set(resolve('acquired Nimbus',store)['external_entity_ids'])=={'EXT:NIMBUS_LIMITED','EXT:NIMBUS_LLC'}
    assert resolve('Seattle, WA and Washington',store)['external_entity_ids']==['EXT:SEATTLE_WASHINGTON','EXT:WASHINGTON']
