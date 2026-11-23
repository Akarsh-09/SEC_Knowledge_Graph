"""Network-free coverage for SEC resets, retries, resumability and batch failures."""
import json
from unittest.mock import MagicMock, patch
import httpx
import pytest
from src.ingest import download_sec_pdfs as downloader

AGENT='SEC tests sec-test@unit.test'

@pytest.mark.parametrize('failure',[
    httpx.ConnectError('[Errno 54] Connection reset by peer'),httpx.ReadError('reset'),
    httpx.RemoteProtocolError('server disconnected'),httpx.ReadTimeout('read timed out'),
    httpx.ConnectTimeout('connect timed out'),429,500,502,503,504])
def test_transient_failures_recreate_client(failure):
    attempts=[];clients=[];settings=[]
    real_client=httpx.Client
    def handle(request):
        attempts.append(request)
        if len(attempts)==1:
            if isinstance(failure,int):return httpx.Response(failure)
            raise failure
        return httpx.Response(200,text='ok')
    def factory(**kwargs):
        settings.append(kwargs)
        client=real_client(**kwargs,transport=httpx.MockTransport(handle));clients.append(client)
        return client
    with patch.object(downloader.httpx,'Client',side_effect=factory), patch.object(downloader.time,'sleep') as sleep:
        client=downloader.SECClient(AGENT)
        try:assert client.get('https://data.sec.gov/test').text=='ok'
        finally:client.close()
    assert len(attempts)==2 and len(clients)==2
    assert all(c.is_closed for c in clients)
    assert 2 in [c.args[0] for c in sleep.call_args_list]
    for config in settings:
        assert config['http2'] is False and config['timeout']==60.0
        assert config['limits'].max_keepalive_connections==0
        assert config['headers']['User-Agent']==AGENT
    assert all(r.headers['User-Agent']==AGENT for r in attempts)

@pytest.mark.parametrize('failure',[httpx.ConnectError('reset'),503])
def test_five_attempt_limit_and_exact_backoff(failure):
    attempts=[];clients=[];real_client=httpx.Client
    def handle(request):
        attempts.append(request)
        if isinstance(failure,int):return httpx.Response(failure)
        raise failure
    def factory(**kwargs):
        c=real_client(**kwargs,transport=httpx.MockTransport(handle));clients.append(c);return c
    with patch.object(downloader.httpx,'Client',side_effect=factory),patch.object(downloader.time,'sleep') as sleep,patch.object(downloader.time,'monotonic',return_value=100):
        client=downloader.SECClient(AGENT)
        try:
            with pytest.raises(httpx.HTTPStatusError if isinstance(failure,int) else httpx.ConnectError):
                client.get('https://www.sec.gov/test')
        finally:client.close()
    assert len(attempts)==5 and len(clients)==5
    assert [c.args[0] for c in sleep.call_args_list if c.args[0]>=1]==[2,4,8,16]
    assert all(c.is_closed for c in clients)

@pytest.mark.parametrize('status',[403,404,501])
def test_non_retryable_http_errors(status):
    real_client=httpx.Client
    http=real_client(transport=httpx.MockTransport(lambda r:httpx.Response(status)))
    with patch.object(downloader.httpx,'Client',return_value=http) as factory,patch.object(downloader.time,'sleep'):
        client=downloader.SECClient(AGENT)
        try:
            with pytest.raises(httpx.HTTPStatusError):client.get('https://www.sec.gov/test')
        finally:client.close()
    assert factory.call_count==1


def test_existing_skip_empty_retry_and_force(tmp_path):
    company=dict(ticker='NVDA',cik='0001045810')
    path=tmp_path/'NVDA_10K_2026.pdf';path.write_bytes(b'existing PDF')
    client=MagicMock();client.get.side_effect=RuntimeError('fetch attempted')
    assert downloader.download(company,client,tmp_path)==path
    client.get.assert_not_called()
    with pytest.raises(RuntimeError,match='fetch attempted'):downloader.download(company,client,tmp_path,force=True)
    assert path.read_bytes()==b'existing PDF'
    path.write_bytes(b'')
    with pytest.raises(RuntimeError,match='fetch attempted'):downloader.download(company,client,tmp_path)


def test_batch_continues_and_summarizes(tmp_path,monkeypatch,capsys,caplog):
    (tmp_path/'config').mkdir()
    companies=[dict(ticker=t,cik='0000000001') for t in ('NVDA','AAPL','JPM')]
    (tmp_path/'config/companies.json').write_text(json.dumps(companies))
    monkeypatch.setattr(downloader,'ROOT',tmp_path)
    monkeypatch.setattr('sys.argv',['download','--tickers','NVDA','AAPL','JPM','--output',str(tmp_path/'pdfs')])
    with patch.object(downloader,'SECClient') as client,patch.object(downloader,'download',side_effect=[httpx.ConnectError('reset'),tmp_path/'a.pdf',tmp_path/'j.pdf']) as fetch:
        with pytest.raises(SystemExit) as error:downloader.main()
    assert error.value.code==1 and fetch.call_count==3
    client.return_value.close.assert_called_once()
    output=capsys.readouterr().out
    summary=json.loads(output[output.index('{'):])
    assert summary==dict(succeeded=['AAPL','JPM'],skipped=[],failed=['NVDA'])
    assert 'FAILED NVDA' in caplog.text


def test_skip_all_requires_no_client(tmp_path,monkeypatch,capsys):
    (tmp_path/'config').mkdir()
    (tmp_path/'config/companies.json').write_text(json.dumps([dict(ticker='NVDA',cik='0001045810')]))
    output=tmp_path/'pdfs';output.mkdir();(output/'NVDA_10K_2026.pdf').write_bytes(b'PDF')
    monkeypatch.setattr(downloader,'ROOT',tmp_path)
    monkeypatch.setattr('sys.argv',['download','--tickers','NVDA','--output',str(output)])
    with patch.object(downloader,'SECClient',side_effect=AssertionError('no network client expected')):
        downloader.main()
    assert 'SKIPPED NVDA' in capsys.readouterr().out
