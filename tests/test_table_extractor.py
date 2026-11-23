"""Accounting normalization and conservative statement extraction tests."""
import pytest
from src.extract.table_extractor import detect_scale,parse_number,parse_fiscal_years,extract
from src.ingest.pdf_parser import ParsedPage
from src.extract.relation_extractor import Candidate,verify

@pytest.mark.parametrize('name,expected',[('thousands',1e3),('millions',1e6),('billions',1e9)])
def test_scales(name,expected):
    assert detect_scale('Amounts in '+name)==expected
    assert detect_scale('in '+name,per_share=True)==1

def test_unknown_scale(): assert detect_scale('Revenue') is None

def test_negative(): assert parse_number('(1,234)') == -1234

def test_years():
    assert parse_fiscal_years('2026 2025 2024 2023 2026')==['FY2026','FY2025','FY2024','FY2023']

def test_bank_statement():
    p=ParsedPage(source_doc='bank.pdf',page_num=4,section='Item 8',signals=['Financial Statements'],tables=[],
        text='Consolidated statements of income\n(in millions)\n2025 2024 2023\nTotal net revenue    100 90 80\nNet interest income    70 60 50\nNoninterest revenue    30 30 30\nDiluted earnings per share    2.5 2.0 1.5')
    facts=extract(p,'COMP:JPM')
    assert len(facts)==12
    assert next(f for f in facts if f.metric_id=='METRIC:REVENUE').value_usd==100e6
    assert next(f for f in facts if f.metric_id=='METRIC:EPS_DILUTED').value_usd==2.5
    assert all(f.snippet in p.text for f in facts)

def test_gate():
    p=ParsedPage(source_doc='x.pdf',page_num=1,section='Item 1',text='We acquired Acme.',tables=[])
    c=Candidate(relation_type='ACQUIRED',target_name='Acme',page_num=1,verbatim_quote='We acquired Acme.')
    assert verify(c,p)
    assert not verify(c.model_copy(update={'page_num':2}),p)
    assert not verify(c.model_copy(update={'verbatim_quote':'We acquired Other.'}),p)


def test_balance_subtable_and_long_term_debt():
    p=ParsedPage(source_doc='bank.pdf',page_num=1,section='Item 8',signals=['Financial Statements'],tables=[],
        text='Consolidated balance sheets\n(in millions)\n2025 2024\nTotal assets (a)    1000 900\nLong-term debt (included $2 at fair value)    100 90\n(a) VIE subtable\nTotal assets    20 10')
    facts=extract(p,'COMP:JPM')
    assert len(facts)==4
    assert [f.value_raw for f in facts if f.metric_id=='METRIC:TOTAL_ASSETS']==[1000,900]


def test_no_scale_abstains():
    p=ParsedPage(source_doc='x.pdf',page_num=1,section='Item 8',signals=['Financial Statements'],tables=[],text='2025 2024\nRevenue    10 9')
    assert extract(p,'COMP:X')==[]


def test_conflicts_and_store(tmp_path):
    from src.graph.schema import MetricObservationNode
    from src.graph.builder import build
    from src.graph.store import GraphStore
    a=MetricObservationNode(id='FACT:a',company_id='COMP:X',source_doc='x.pdf',page_num=1,
        section='Item 7',snippet='Revenue 10',metric_id='METRIC:REVENUE',period='FY2026',
        value_raw=10,scale_multiplier=1e6,value_usd=10e6)
    b=a.model_copy(update={'id':'FACT:b','section':'Item 8','audited':True,'value_raw':12,'value_usd':12e6})
    path=tmp_path/'kg.json'
    graph=build([dict(ticker='X',name='Example',sector='Test',cik='0000000001')],[a,b],path)
    assert any(s=='FACT:b' and t=='FACT:a' and d['relation']=='SUPERSEDES' for s,t,d in graph.edges(data=True))
    store=GraphStore(path)
    assert store.resolve_company('Example')=='COMP:X'
    assert store.lookup_metric('COMP:X','METRIC:REVENUE','FY2026')[0]['id']=='FACT:b'


def test_quote_normalization_and_original():
    from src.extract.relation_extractor import verified_snippet
    page=ParsedPage(source_doc='x',page_num=1,section='Item 1',tables=[],text='We acquired “Taiwan Semiconductor Manu-\nfacturing”\xa0 in  2025.')
    c=Candidate(relation_type='ACQUIRED',target_name='TSMC',page_num=1,verbatim_quote='we acquired "Taiwan Semiconductor Manufacturing" in 2025.')
    assert verified_snippet(c,page)==page.text
    assert not verify(c.model_copy(update={'relation_type':'AUDITED_BY'}),page)


def test_capex_analytical():
    p=ParsedPage(source_doc='x',page_num=1,section='Item 8',signals=['Financial Statements'],tables=[],text='Consolidated statements of cash flows\n(in millions)\n2025 2024\nCapital expenditures    (10) 9')
    facts=extract(p,'COMP:X')
    assert [f.analytical_value_usd for f in facts]==[10e6,9e6]
    assert facts[0].value_usd==-10e6
    assert facts[0].raw_label=='Capital expenditures'


def test_corroboration(tmp_path):
    from src.graph.builder import build
    from src.graph.schema import RelationClaimNode
    from src.graph.store import GraphStore
    base=dict(company_id='COMP:X',source_doc='x',section='Auditor Report',snippet='EY',relation_type='AUDITED_BY',target_id='EXT:EY',target_name='EY')
    internal=RelationClaimNode(id='FACT:i',page_num=1,audit_scope='internal_control',**base)
    financial=RelationClaimNode(id='FACT:f',page_num=2,audit_scope='financial_statements',**base)
    p=tmp_path/'kg.json'
    g=build([dict(ticker='X',name='X',sector='Test',cik='0000000001')],[internal,financial],p)
    assert g.nodes['FACT:i']['status']=='corroborating'
    assert any(d['relation']=='CORROBORATES' for *_,d in g.edges(data=True))
    store=GraphStore(p)
    assert len(store.lookup_relation('COMP:X','AUDITED_BY'))==1
    assert len(store.lookup_relation('COMP:X','AUDITED_BY',active_only=False))==2


def test_candidate_page_cap():
    from src.extract.relation_extractor import select_candidate_pages
    pages=[ParsedPage(source_doc='x',page_num=i+1,section='Item 1' if i<3 else 'Item 1A',text=('Overview' if i<2 else 'supplier acquisition risk factor '*(i+1)),tables=[]) for i in range(20)]
    selected=select_candidate_pages(pages)
    assert len(selected)==10
    assert {1,2}.issubset({p.page_num for p in selected})
    assert [p.page_num for p in selected]==[p.page_num for p in select_candidate_pages(pages)]
