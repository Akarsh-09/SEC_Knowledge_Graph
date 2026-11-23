"""Issuer-independent primary statements, cover layouts and audit evidence."""
from pathlib import Path
import json
import pymupdf
import pytest
from src.ingest.pdf_parser import parse_pdf,STATEMENT,primary_heading,is_contents_page
from src.extract.table_extractor import extract,mezzanine_diagnostics,detect_scale
from src.extract.metadata_extractor import extract as metadata,headquarters
from src.ingest.pdf_parser import ParsedPage


def page(text,kind='income',**kwargs):
    return ParsedPage(source_doc='EXAMPLE_10K_2025.pdf',page_num=1,section='Item 8',signals=['Financial Statements'],statement_kind=kind,text=text,tables=kwargs.pop('tables',[]),**kwargs)

@pytest.mark.parametrize('title',[
 'Statements of Income','Income Statements','Statements of Operations','Statements of Earnings',
 'Consolidated Statements of Income For Years Ended December 31,',
 'Condensed Consolidated\nStatements of Financial Position','Statements of Financial Condition',
 'Balance Sheets','Consolidated Balance Sheet','Statements of Cash Flows','Cash Flow Statements',
 'Consolidated Cash Flow Statement          Image20.jpg',
 'Example Issuer and subsidiaries consolidated statements of\ncash flows'])
def test_primary_title_variants(title):
    text=title+'\n(in millions)\n2025 2024\nRevenue    100 90'
    match=STATEMENT.search(text)
    assert match is not None and primary_heading(text,match)
    assert not is_contents_page(text)


def test_toc_running_links_and_notes_do_not_poison_primary_pages(tmp_path):
    path=tmp_path/'fixture.pdf'
    texts=[
        'Index to Financial Statements\nConsolidated Statements of Income    51\nConsolidated Balance Sheets    52\nConsolidated Statements of Cash Flows    53\nNotes to Consolidated Financial Statements    54',
        'Table of Contents\nIndex to Financial Statements\nIncome Statements\n(in millions)\n2025 2024\nRevenue    100 90',
        'The discussion refers to Note 14 of\nNotes to Consolidated Financial Statements.\nDiscussion continues.',
        'Consolidated Balance Sheets\n(in millions)\n2025 2024\nTotal assets    100 90',
        'Notes to Consolidated Financial Statements\n1. Policies\nConsolidated Balance Sheets\n(in millions)\n2025 2024\nTotal assets    10 9']
    with pymupdf.open() as doc:
        for text in texts:doc.new_page().insert_text((40,40),text)
        doc.save(path)
    pages=parse_pdf(path)
    assert pages[0].section=='Table of Contents' and 'Financial Statements' not in pages[0].signals
    assert 'Financial Statements' in pages[1].signals and 'Financial Statements' in pages[3].signals
    assert 'Financial Statements' not in pages[4].signals

@pytest.mark.parametrize('text',['(MILLIONS, EXCEPT PER SHARE DATA)','($ in millions except per share amounts)','(Dollars and Shares in Millions Except Per Share Amounts)'])
def test_scale_header_forms(text):assert detect_scale(text)==1e6


def test_generic_synonyms_wrapped_rows_and_aggregate_preference():
    p=page('Statements of Income\n(in millions)\n2025 2024\nNet sales    100 90\nTotal revenues    105 95\nNet income (loss)    (4) 3\nNet income attributable to\nExample Parent Corporation    (5) 2')
    facts=extract(p,'COMP:EXAMPLE')
    assert [f.value_raw for f in facts if f.metric_id=='METRIC:REVENUE']==[105,95]
    assert [f.value_raw for f in facts if f.metric_id=='METRIC:NET_INCOME']==[-4,3]
    p=page('Statements of Income\n(in millions)\n2025 2024\nNet income attributable to\nExample Parent Corporation    5 2')
    facts=extract(p,'COMP:EXAMPLE')
    assert len(facts)==2 and all(f.snippet in p.text for f in facts)


def test_numeric_line_below_label_and_ambiguity_rejection():
    p=page('Income Statements\n(in millions)\n2025 2024\nTotal revenues\n$ 100 90\nNet income    5 4\nNet income    7 6')
    facts=extract(p,'COMP:EXAMPLE')
    assert len(facts)==2 and all(f.metric_id=='METRIC:REVENUE' for f in facts)
    assert not extract(page('Income Statements\n(in millions)\n2025 2024\nRevenue    10 9 8 7'), 'COMP:EXAMPLE')


def test_mezzanine_diagnostic_preserves_three_term_residual(tmp_path):
    import networkx as nx
    from src.graph.builder import write_ingestion_audit
    p=page('Balance Sheets\n(in millions)\n2025 2024\nTotal assets    110 100\nTotal liabilities    70 60\nRedeemable noncontrolling interests    10 8\nTotal equity    30 32',kind='balance')
    diagnostics=mezzanine_diagnostics(p)
    assert diagnostics[0]['values'][0]['value_usd']==10e6
    graph=nx.MultiDiGraph();graph.add_node('COMP:EXAMPLE',node_type='Company',ticker='EXAMPLE')
    for f in extract(p,'COMP:EXAMPLE'):graph.add_node(f.id,**f.model_dump())
    report=write_ingestion_audit(graph,tmp_path,balance_diagnostics={'COMP:EXAMPLE':diagnostics})
    assert report['companies'][0]['balance_sheet_residual_usd']==10e6
    assert 'NOT adjusted' in (tmp_path/'ingestion_audit.md').read_text()

@pytest.mark.parametrize('block',[
 '9 Example Street\nSpringfield, IL    62701\n(Address of principal executive offices)    (Zip Code)',
 'Address of principal executive offices:\nExample Corporate Center\n9 Example Street\nSpringfield, Illinois 62701',
 '9 Example Street, Springfield, Illinois\n(Address and zip code of principal executive offices)',
 'Exact name of registrant as specified in its charter\nState or other jurisdiction\n9 Example Street\nSpringfield, IL 62701\n(Address of principal executive offices)'])
def test_cover_caption_blocks(block):
    p=page(block);p.section='Cover'
    result=headquarters(p)
    assert [name for name,_ in result]==['Springfield, Illinois']
    assert all(snippet in p.text for _,snippet in result)


def test_captionless_cover_requires_unique_street_zip_not_sec_address():
    p=page('UNITED STATES\nWashington, DC 20549\nFORM 10-K\n9 Example Street\nSpringfield, IL 62701\nSecurities registered pursuant to Section 12(b)')
    assert [name for name,_ in headquarters(p)]==['Springfield, Illinois']


def test_auditor_wrapped_header_scope_and_signature_assets(tmp_path):
    path=tmp_path/'audit.pdf'
    with pymupdf.open() as doc:
        for text in ['Report of Independent Registered Public\nAccounting Firm\nOpinion on the Financial Statements',
                     '/s/ PricewaterhouseCoopers LLP\nWe have served as auditor since 1980.',
                     'Report of Independent Registered Public Accounting Firm\nOpinion on Internal Control Over Financial Reporting\n/s/ PricewaterhouseCoopers LLP']:
            doc.new_page().insert_text((40,40),text)
        doc.save(path)
    pages=parse_pdf(path);facts=metadata(pages,'COMP:EXAMPLE')
    audits=[f for f in facts if f.relation_type=='AUDITED_BY']
    assert len(audits)==2 and audits[0].audit_scope=='financial_statements' and audits[1].audit_scope=='internal_control'
    p=page('kpmgsignatureq4201\nWe have served as auditor since 1942.');p.section='Auditor Report';p.audit_scope='financial_statements'
    facts=metadata([p],'COMP:EXAMPLE')
    assert any(f.target_id=='EXT:KPMG' and f.snippet in p.text for f in facts)


def test_pdfplumber_fallback_requires_original_numeric_evidence():
    text='Statements of Cash Flows\n(in millions)\n2025 2024\nNet cash\nprovided by\noperating\nactivities\n100 90'
    table=[['2025','2024'],['Net cash provided by operating activities','100','90']]
    p=page(text,kind='cash_flow',tables=[table])
    facts=extract(p,'COMP:EXAMPLE')
    assert len(facts)==2 and all(f.snippet in text for f in facts)
    # A table value not present in the page cannot be admitted.
    p.tables[0][1][1]='999'
    assert not extract(p,'COMP:EXAMPLE')


def test_narrative_reference_is_not_primary_statement():
    text='Such loans are included in trading assets in our consolidated\nbalance sheets.\n(in millions)\n2025 2024'
    match=STATEMENT.search(text)
    assert match is not None and not primary_heading(text,match)


def test_cover_registration_rows_are_not_hq():
    p=page('FORM 10-K\nEXAMPLE CO\n(Exact name of registrant as specified in its charter)\nState or other jurisdiction of incorporation\n9 Example Street\nSpringfield, IL 62701\n(Address of principal executive offices)\nSecurities registered: EXAMPLE  NY  Exchange')
    assert [n for n,_ in headquarters(p)]==['Springfield, Illinois']


def test_unlabeled_numbers_are_not_fabricated_as_total_assets():
    p=page('Balance Sheets\n(in millions)\n2025 2024\nAssets\nOther assets    100 90\n$ 110 100\nLiabilities and Equity',kind='balance')
    assert not extract(p,'COMP:EXAMPLE')


def test_comprehensive_statement_is_not_an_income_continuation(tmp_path):
    path=tmp_path/'comprehensive.pdf'
    with pymupdf.open() as doc:
        for text in ['Income Statements\n(in millions)\n2025 2024\nNet income    10 9',
                     'Consolidated statements of\ncomprehensive income\n(in millions)\n2025 2024\nNet income    10 9']:
            doc.new_page().insert_text((40,40),text)
        doc.save(path)
    pages=parse_pdf(path)
    assert 'Financial Statements' in pages[0].signals
    assert 'Financial Statements' not in pages[1].signals


def test_freeze_detects_rule_changes(tmp_path):
    import hashlib
    from src.extract.freeze import verify_rules,RULE_FILES
    for name in RULE_FILES:
        path=tmp_path/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('frozen')
    manifest={'version':1,'files':{name:hashlib.sha256((tmp_path/name).read_bytes()).hexdigest() for name in RULE_FILES}}
    (tmp_path/'config/extraction_rules.lock.json').write_text(json.dumps(manifest))
    assert verify_rules(tmp_path)
    (tmp_path/RULE_FILES[0]).write_text('changed')
    with pytest.raises(RuntimeError,match='Frozen extraction rules changed'):verify_rules(tmp_path)


def test_wrapped_combined_income_statement_is_primary(tmp_path):
    title='Consolidated Statements of Operations and Comprehensive\nIncome'
    text=title+'\n(In millions, except per share amounts)\n2025 2024\nRevenue    100 90\nNet income    10 9'
    match=STATEMENT.search(text)
    assert match is not None and primary_heading(text,match)
    path=tmp_path/'combined.pdf'
    with pymupdf.open() as doc:
        doc.new_page().insert_text((40,40),text);doc.save(path)
    p=parse_pdf(path)[0]
    assert p.statement_kind=='income' and 'Financial Statements' in p.signals
    assert {f.metric_id for f in extract(p,'COMP:EXAMPLE')}=={'METRIC:REVENUE','METRIC:NET_INCOME'}
