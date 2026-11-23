"""Accuracy, strict provenance, diagnostics and aggregation regression tests."""
from copy import deepcopy
import pytest
from src.eval.metrics import answer_correct,match_facts,score_question,aggregate


def question(kind='numeric',gold=100,unit='USD',**overrides):
    return dict(id='Q1',type='single-fact',question='What was revenue in FY2025?',answer_type=kind,golden_answer=gold,unit=unit,gold_supporting_facts=[],**overrides)

def prediction(value,kind='numeric',unit='USD',abstained=False):
    return dict(structured_answer=value,answer_type=kind,unit=unit,abstained=abstained,retrieved_facts=[])

@pytest.mark.parametrize('value,correct',[(100,True),(100.9,True),(101,True),(101.01,False),(98.99,False),(0,False)])
def test_numeric_tolerance(value,correct):
    assert answer_correct(question(),prediction(value)) is correct


def test_unit_normalization():
    assert answer_correct(question(gold=25,unit='percent'),prediction(.25,unit='ratio'))
    assert answer_correct(question(gold=2e9),prediction(2,unit='USD billions'))
    assert not answer_correct(question(gold=25,unit='percent'),prediction(.25,unit='USD'))
    assert not answer_correct(question(gold=25,unit='percent'),prediction(.25,unit=None))
    assert not answer_correct(question(gold=0),prediction(1))
    assert not answer_correct(question(),prediction(float('nan')))


def test_entity_and_order():
    assert answer_correct(question('entity','COMP:NVDA',None),prediction('NVIDIA','entity',None))
    q=question('entity_list',['COMP:NVDA','COMP:AAPL'],None)
    assert answer_correct(q,prediction(['Apple','NVDA'],'entity_list',None))
    q['question']='Rank NVDA and AAPL by revenue in FY2025'
    assert not answer_correct(q,prediction(['Apple','NVDA'],'entity_list',None))
    assert answer_correct(q,prediction(['NVDA','Apple'],'entity_list',None))


def test_boolean_and_abstention():
    assert answer_correct(question('boolean',True,None),prediction(True,'boolean',None))
    assert not answer_correct(question('boolean',True,None),prediction(1,'boolean',None))
    assert not answer_correct(question(),prediction(None,abstained=True))
    assert answer_correct(question(gold=None),prediction(None,abstained=True))


def gold(page=5,predicate='METRIC:REVENUE',period='FY2025'):
    return dict(doc_id='NVDA.pdf',page_num=page,company_id='COMP:NVDA',predicate=predicate,period=period)

def retrieved(page=5,predicate='METRIC:REVENUE',period='FY2025',id='FACT:1'):
    return dict(fact_id=id,source_doc='NVDA.pdf',page_num=page,company_id='COMP:NVDA',predicate=predicate,period=period)


def test_exact_vs_near_page():
    r=[retrieved(6)];g=[gold()]
    assert match_facts(r,g)['matched_count']==0
    assert match_facts(r,g,page_tolerance=1)['matched_count']==1
    assert match_facts([retrieved(7)],g,page_tolerance=1)['matched_count']==0
    assert match_facts([retrieved(predicate='Revenue')],g)['matched_count']==1
    assert match_facts([retrieved(period='FY2024')],g)['matched_count']==0
    assert match_facts([retrieved(period=None)],[gold(period=None)])['matched_count']==1
    for field,value in [('source_doc','other.pdf'),('company_id','COMP:AAPL'),('predicate','METRIC:NET_INCOME')]:
        f=retrieved();f[field]=value
        assert match_facts([f],g)['matched_count']==0


def test_duplicate_fact_penalty():
    score=match_facts([retrieved(),retrieved()],[gold()])
    assert score['precision']==.5 and score['recall']==1
    assert len(score['extra_facts'])==1


def test_maximum_matching_near_pages():
    # First prediction can match either gold; second can only match page 4.
    score=match_facts([retrieved(5),retrieved(3)],[gold(4),gold(6)],page_tolerance=1)
    assert score['matched_count']==2


def test_macro_micro_and_empty():
    q1=question();q1['gold_supporting_facts']=[gold()]
    p1=prediction(100);p1['retrieved_facts']=[retrieved(),retrieved()]
    q2=question();q2.update(id='Q2',type='multi-hop',gold_supporting_facts=[gold(),gold(6),gold(7)])
    p2=prediction(None,abstained=True)
    report=aggregate([score_question(q1,p1),score_question(q2,p2)])
    overall=report['Overall']
    assert overall['accuracy']==.5
    assert overall['strict']['precision_macro']==.25
    assert overall['strict']['recall_macro']==.5
    assert overall['strict']['precision_micro']==.5
    assert overall['strict']['recall_micro']==.25
    assert report['single-fact']['strict']['precision_macro']==.5
    assert report['cross-filing']['questions']==0
    assert match_facts([],[])['precision']==0 and match_facts([],[])['recall']==0


def test_failure_writeup_contains_plan_trace():
    from src.eval.run_eval import failure_markdown
    q=question();q['gold_supporting_facts']=[gold()]
    p=prediction(None,abstained=True)
    p.update(reason='Missing revenue',plan={'steps':[]},execution_trace=[{'action':'lookup_metric'}])
    score=score_question(q,p)
    text=failure_markdown([dict(id='Q1',type=q['type'],question=q['question'],golden_answer=q['golden_answer'],prediction=p,score=score)])
    assert 'Missing revenue' in text and 'lookup_metric' in text and 'missed_facts' in text


def test_six_question_offline_evaluation(tmp_path,monkeypatch):
    from pathlib import Path
    from unittest.mock import patch
    from src.eval.run_eval import run
    root=Path(__file__).resolve().parents[1]
    monkeypatch.delenv('LLM_API_KEY',raising=False)
    with patch('httpx.Client',side_effect=AssertionError('Network forbidden in zero-key evaluation')):
        report=run(root/'benchmark/questions_sample_3co.json',output_dir=tmp_path)
    assert report['groups']['Overall']['accuracy']==1
    assert report['groups']['Overall']['strict']['matched_facts']==16
    assert report['planner_source_breakdown']=={'deterministic_fallback':6}
    assert len((tmp_path/'predictions.jsonl').read_text().splitlines())==6
    assert 'Design scope and future improvements' in (tmp_path/'eval_summary.md').read_text()


def test_ingestion_audit_missing_identity(tmp_path):
    import networkx as nx
    from src.graph.builder import write_ingestion_audit
    graph=nx.MultiDiGraph()
    graph.add_node('COMP:X',node_type='Company',ticker='X')
    graph.add_node('FACT:1',node_type='MetricObservation',company_id='COMP:X',status='active',metric_id='METRIC:REVENUE',period='FY2025',value_usd=10,audited=True,section='Item 8',page_num=1)
    report=write_ingestion_audit(graph,tmp_path)
    company=report['companies'][0]
    assert company['core_metrics_extracted']==1
    assert company['balance_sheet_residual_usd'] is None
    assert len(company['balance_sheet_missing_inputs'])==3
    assert company['fact_status_counts']['active']==1
    assert not company['llm_relation_extraction']['recorded']


def test_relation_extraction_stats_distinguish_skipped_and_replay():
    from src.extract.relation_extractor import extract,Candidates,Candidate
    from src.ingest.pdf_parser import ParsedPage
    from src.llm_client import OfflineCacheMiss
    pages=[ParsedPage(source_doc='x',page_num=1,section='Item 1',text='We acquired Acme.',tables=[])]
    class Client:
        offline=True
        def structured(self,*args):
            return Candidates(claims=[Candidate(relation_type='ACQUIRED',target_name='Acme',page_num=1,verbatim_quote='We acquired Acme.'),Candidate(relation_type='AUDITED_BY',target_name='Acme',page_num=1,verbatim_quote='We acquired Acme.')]),'llm_cache'
    stats={}
    assert extract(pages,'COMP:X',Client(),skip_llm=True,stats=stats)==[]
    assert stats['candidate_pages_selected']==1 and stats['candidate_pages_sent']==0
    assert len(extract(pages,'COMP:X',Client(),stats=stats))==1
    assert stats['pages_replayed']==1 and stats['candidate_pages_sent']==0
    assert stats['accepted_claims']==1 and stats['rejected_by_provenance_gate']==1


def test_legal_name_variant():
    assert answer_correct(question('entity','COMP:AAPL',None),prediction('Apple Inc.','entity',None))


@pytest.mark.parametrize('display,node_id', [
    ('Seattle, WA','EXT:SEATTLE_WASHINGTON'),('Oakland, ca','EXT:OAKLAND_CALIFORNIA'),
    ('New York, NY','EXT:NEW_YORK_NEW_YORK'),('Delaware','EXT:DELAWARE'),
    ('Jordan A. Reed','EXT:JORDAN_A_REED'),('Ernst & Young LLP','EXT:EY')])
def test_entity_id_display_and_postal_equivalence(display,node_id):
    assert answer_correct(question('entity',display,None),prediction(node_id,'entity',None))
    assert answer_correct(question('entity',node_id,None),prediction(display,'entity',None))


def test_all_us_postal_states_and_company_ticker_precedence():
    from src.entity_names import US_STATES
    from src.eval.metrics import canonical_entity
    assert len(US_STATES)==51
    for code,name in US_STATES.items():
        assert canonical_entity('EXT:EXAMPLE_CITY_'+code)==canonical_entity('Example City, '+name)
    assert canonical_entity('MS')==canonical_entity('Morgan Stanley')
    assert canonical_entity('EXT:MS')==canonical_entity('Mississippi')


@pytest.mark.parametrize('page', [5,6])
def test_page_diagnostic_checks_relation_target_even_on_same_page(page):
    g=gold(predicate='OPERATES_SEGMENT',period=None);g['expected_value']='Fabric & Home Care'
    r=retrieved(page,predicate='OPERATES_SEGMENT',period=None);r['value']='Beauty'
    assert match_facts([r],[g],page_tolerance=1)['matched_count']==0
    r['value']='EXT:FABRIC_HOME_CARE'
    assert match_facts([r],[g],page_tolerance=1)['matched_count']==1
    # Primary matching remains exact-page, without changing its legacy definition.
    assert match_facts([r],[g])['matched_count']==int(page==5)


def test_relation_target_diagnostic_matches_aliases_and_is_one_to_one():
    g=gold(predicate='HEADQUARTERED_IN',period=None);g['expected_value']='Seattle, WA'
    r=retrieved(6,predicate='HEADQUARTERED_IN',period=None);r['target_id']='EXT:SEATTLE_WASHINGTON'
    result=match_facts([r,r],[g],page_tolerance=1)
    assert result['matched_count']==1 and result['precision']==.5
    del r['target_id']
    assert match_facts([r],[g],page_tolerance=1)['matched_count']==0


def test_report_metadata_is_dynamic_and_has_no_stale_smoke_claims(tmp_path,monkeypatch):
    import hashlib,json
    from src.eval.run_eval import run
    q=question();q['gold_supporting_facts']=[gold()]
    path=tmp_path/'custom_questions.json';path.write_text(json.dumps([q]))
    p=prediction(100);p.update(answer='100 USD',plan={'steps':[]},planner_source='llm_cache',reason=None,citations=['[NVDA.pdf, p. 5]'],execution_trace=[])
    p['retrieved_facts']=[retrieved()]
    monkeypatch.setattr('src.eval.run_eval.ask',lambda *args,**kwargs:p)
    monkeypatch.setattr('src.eval.run_eval.verify_rules',lambda root:'synthetic-freeze-digest')
    report=run(path,offline=True,output_dir=tmp_path/'reports')
    assert report['question_count']==1 and report['extraction_rules_digest']=='synthetic-freeze-digest'
    assert report['benchmark_sha256']==hashlib.sha256(path.read_bytes()).hexdigest()
    for filename in ['eval_summary.md','failure_analysis.md']:
        text=(tmp_path/'reports'/filename).read_text()
        assert str(path) in text and 'Questions: **1**' in text and 'synthetic-freeze-digest' in text
        assert 'page +/- 1' in text and 'relation' in text
        assert 'six-question three-company' not in text and 'production benchmark remains empty' not in text


def test_optional_ext_prefix_still_resolves_known_company_names():
    from src.eval.metrics import canonical_entity
    assert canonical_entity('EXT:APPLE_INC')==canonical_entity('COMP:AAPL')
    assert canonical_entity('EXT:MICROSOFT')==canonical_entity('Microsoft')
