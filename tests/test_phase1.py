"""Network-free Phase 1 checks."""
import hashlib
import sqlite3
from unittest.mock import patch
import pymupdf
import httpx
import pytest
from pydantic import BaseModel
from src.llm_client import LLMClient, OfflineCacheMiss
from src.ingest.pdf_parser import parse_pdf

class Reply(BaseModel):
    value: int

def test_offline(tmp_path):
    client = LLMClient(api_key='', model='test', cache_path=tmp_path / 'cache.sqlite')
    with patch('httpx.Client', side_effect=AssertionError('network forbidden')):
        with pytest.raises(OfflineCacheMiss):
            client.structured('s', 'u', Reply)
        with sqlite3.connect(client.cache_path) as db:
            db.execute('INSERT INTO responses VALUES (?, ?, ?)',
                       (hashlib.sha256(b'testsu').hexdigest(), 'test', '{"value":7}'))
        value, source = client.structured('s', 'u', Reply)
        assert value.value == 7 and source == 'llm_cache'

def test_live_retry(tmp_path, monkeypatch):
    monkeypatch.delenv('LLM_FALLBACK_MODELS', raising=False)
    monkeypatch.delenv('LLM_BASE_URL', raising=False)
    responses = iter([httpx.Response(429), httpx.Response(503), httpx.Response(200,
        json={'choices': [{'message': {'content': '{"value":9}'}}]})])
    transport = httpx.MockTransport(lambda request: next(responses))
    mock = httpx.Client(transport=transport)
    client = LLMClient(api_key='test', model='test', cache_path=tmp_path / 'c.sqlite')
    with patch('httpx.Client', return_value=mock), patch('time.sleep') as sleep:
        assert client.structured('s', 'u', Reply)[1] == 'llm_live'
        assert sleep.call_count == 2
    assert client.structured('s', 'u', Reply)[1] == 'llm_cache'

def test_pdf_pages(tmp_path):
    path = tmp_path / 'fixture.pdf'
    with pymupdf.open() as doc:
        for text in ['Cover', 'ITEM 1. Business\nBusiness description',
                     'ITEM 8. Financial Statements\nRevenue',
                     'Report of Independent Registered Public Accounting Firm']:
            doc.new_page().insert_text((72, 72), text)
        doc.save(path)
    pages = parse_pdf(path)
    assert [p.page_num for p in pages] == [1, 2, 3, 4]
    assert [p.section for p in pages] == ['Cover', 'Item 1', 'Item 8', 'Auditor Report']


def test_sec_headers_and_local_render(tmp_path):
    """Exercise both SEC hosts using a mock transport; Chromium is also mocked."""
    from pathlib import Path
    from unittest.mock import MagicMock
    from src.ingest.download_sec_pdfs import SECClient, download

    requests = []
    def handle(request):
        requests.append(request)
        if request.url.host == 'data.sec.gov':
            return httpx.Response(200, json={'filings': {'recent': {
                'form': ['10-K'], 'filingDate': ['2026-02-01'],
                'reportDate': ['2025-12-31'], 'accessionNumber': ['0001-26-01'],
                'primaryDocument': ['filing.htm']}}})
        return httpx.Response(200, text='<html><body>Local filing</body></html>')

    user_agent = 'SEC Test sec-test@unit.test'
    transport_client = httpx.Client(transport=httpx.MockTransport(handle),
                                   headers={'User-Agent': user_agent})
    with patch('src.ingest.download_sec_pdfs.httpx.Client', return_value=transport_client):
        client = SECClient(user_agent)
    playwright = MagicMock()
    page = playwright.chromium.launch.return_value.new_page.return_value
    def check_local(url, **kwargs):
        from urllib.parse import urlparse, unquote
        assert url.startswith('file://')
        assert 'Local filing' in Path(unquote(urlparse(url).path)).read_text()
    page.goto.side_effect = check_local
    page.pdf.side_effect = lambda **kwargs: Path(kwargs['path']).write_bytes(b'PDF fixture')
    with patch('src.ingest.download_sec_pdfs.sync_playwright') as factory:
        factory.return_value.__enter__.return_value = playwright
        target = tmp_path / 'NVDA_10K_2025.pdf'
        target.write_bytes(b'previous PDF')
        download({'cik': '0001045810', 'ticker': 'NVDA'}, client, tmp_path, force=True)
        assert target.read_bytes() == b'PDF fixture'
    assert {r.url.host for r in requests} == {'data.sec.gov', 'www.sec.gov'}
    assert all(r.headers['User-Agent'] == user_agent for r in requests)
    route_handler = page.route.call_args.args[1]
    for url in ['https://www.sec.gov/image.png', 'http://other.test/style.css']:
        route = MagicMock()
        route.request.url = url
        route_handler(route)
        route.abort.assert_called_once()
        route.continue_.assert_not_called()
    route = MagicMock()
    route.request.url = 'file:///tmp/filing.html'
    route_handler(route)
    route.continue_.assert_called_once()
    client.close()


def test_running_toc_and_multiline_heading(tmp_path):
    path=tmp_path/'headings.pdf'
    with pymupdf.open() as doc:
        for text in ['Cover', 'Table of Contents\nITEM 1. Business   1\nITEM 1A. Risk Factors   2\nITEM 7. MD&A   3\nITEM 8. Statements   4',
                     'Table of Contents\nITEM 1.\nBusiness\nOur business description.',
                     'Table of Contents\nITEM 1A.\nRisk Factors\nRisks apply.',
                     "MANAGEMENT'S DISCUSSION AND ANALYSIS\nAnalysis text",
                     'CONSOLIDATED STATEMENTS OF INCOME\n(in millions)\n2026 2025\nRevenue    100 90']:
            doc.new_page().insert_text((72,72),text)
        doc.save(path)
    pages=parse_pdf(path)
    assert [p.section for p in pages]==['Cover','Table of Contents','Item 1','Item 1A','Item 7','Item 8']
    assert 'Financial Statements' in pages[-1].signals
