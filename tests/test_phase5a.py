"""Scratch graph isolation and optional reasoning-effort request configuration."""
import json
from pathlib import Path
from unittest.mock import patch
import httpx
import pytest
from pydantic import BaseModel
from src.llm_client import LLMClient

class Reply(BaseModel):
    value: int

@pytest.mark.parametrize('effort',[None,'low'])
def test_reasoning_effort_optional_payload(tmp_path,monkeypatch,effort):
    monkeypatch.delenv('LLM_REASONING_EFFORT',raising=False)
    if effort is not None:monkeypatch.setenv('LLM_REASONING_EFFORT',effort)
    captured=[]
    def handle(request):
        captured.append(json.loads(request.content))
        return httpx.Response(200,json={'choices':[{'message':{'content':'{"value":1}'}}]})
    transport=httpx.MockTransport(handle)
    http=httpx.Client(transport=transport)
    client=LLMClient(api_key='unit-test',model='test',cache_path=tmp_path/'cache.sqlite')
    with patch('src.llm_client.httpx.Client',return_value=http):
        assert client.structured('Return JSON','question',Reply)[0].value==1
    assert captured[0].get('reasoning_effort')==effort
    if effort is None:assert 'reasoning_effort' not in captured[0]


def test_scratch_graph_and_reports_do_not_overwrite_main(tmp_path,monkeypatch):
    from scripts import build_kg
    from src.ingest.pdf_parser import ParsedPage
    (tmp_path/'config').mkdir();(tmp_path/'data/pdfs').mkdir(parents=True)
    (tmp_path/'data/graph').mkdir()
    company=dict(ticker='NVDA',name='NVIDIA',cik='0001045810',sector='Semiconductors')
    (tmp_path/'config/companies.json').write_text(json.dumps([company]))
    (tmp_path/'data/pdfs/NVDA_10K_2026.pdf').write_bytes(b'fixture')
    main=tmp_path/'data/graph/kg.json';main.write_text('validated graph sentinel')
    (tmp_path/'results').mkdir();audit=tmp_path/'results/ingestion_audit.json';audit.write_text('validated audit sentinel')
    output=tmp_path/'data/graph/kg_dev.json'
    monkeypatch.setattr(build_kg,'ROOT',tmp_path)
    monkeypatch.setattr('sys.argv',['build_kg.py','--tickers','NVDA','--limit','1','--output',str(output),'--skip-llm','--offline'])
    page=ParsedPage(source_doc='NVDA_10K_2026.pdf',page_num=1,section='Cover',text='Cover',tables=[])
    with patch.object(build_kg,'parse_pdf',return_value=[page]),patch.object(build_kg,'LLMClient'):
        build_kg.main()
    assert main.read_text()=='validated graph sentinel'
    assert audit.read_text()=='validated audit sentinel'
    assert json.loads(output.read_text())['multigraph']
    dev=json.loads((tmp_path/'results/kg_dev/ingestion_audit.json').read_text())
    assert dev['summary']['companies_parsed_cleanly']==1
    assert dev['summary']['auditor_coverage']==0
    assert dev['companies'][0]['coverage_flag']
