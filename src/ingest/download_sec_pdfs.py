"""Fetch latest SEC 10-K HTML and render locally with fixed PDF pagination."""
from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path
import re
import time
from tempfile import TemporaryDirectory

import httpx
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
LOG = logging.getLogger(__name__)
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class SECClient:
    """Serial SEC HTTP access at at most four requests per second."""

    def __init__(self, user_agent: str) -> None:
        if not re.search(r'[^\s@]+@[^\s@]+\.[^\s@]+', user_agent) or 'example.com' in user_agent:
            raise ValueError('Set SEC_USER_AGENT to your name and real contact email')
        self.user_agent = user_agent
        self.client = self._new_client()
        self.last_request = 0.0

    def _new_client(self) -> httpx.Client:
        """Avoid stale pooled SEC sockets between downloads and PDF rendering."""
        return httpx.Client(
            headers={'User-Agent': self.user_agent}, timeout=60.0,
            limits=httpx.Limits(max_keepalive_connections=0),
            http2=False, follow_redirects=True,
        )

    def get(self, url: str) -> httpx.Response:
        """Retry transient failures at most five times, using a fresh client each time."""
        for attempt in range(5):
            time.sleep(max(0, .25 - (time.monotonic() - self.last_request)))
            self.last_request = time.monotonic()
            try:
                response = self.client.get(url)
                response.raise_for_status()
                return response
            except (httpx.TransportError, httpx.HTTPStatusError) as error:
                if isinstance(error, httpx.HTTPStatusError):
                    if error.response.status_code not in RETRYABLE_STATUS_CODES:
                        raise
                    error.response.close()
                if attempt == 4:
                    raise
                delay = 2 ** (attempt + 1)
                LOG.warning('SEC fetch failed (%s); retry %d/4 in %ds: %s',
                            type(error).__name__, attempt + 1, delay, url)
                self.client.close()
                time.sleep(delay)
                self.client = self._new_client()
        raise RuntimeError('Unreachable retry state')

    def close(self) -> None:
        self.client.close()


def existing_pdf(ticker: str, output: Path) -> Path | None:
    """Find the newest nonempty local filing; --force opts into checking SEC again."""
    return next((p for p in sorted(output.glob(f'{ticker}_10K_*.pdf'), reverse=True)
                 if p.is_file() and p.stat().st_size > 0), None)


def download(company: dict[str, str], client: SECClient, output: Path, *, force: bool = False) -> Path:
    """Render the latest original 10-K; preserve accession and content hashes."""
    import hashlib
    if not force and (existing := existing_pdf(company['ticker'], output)) is not None:
        return existing
    cik = company['cik']
    submission = client.get(f'https://data.sec.gov/submissions/CIK{cik}.json').json()
    recent = submission['filings']['recent']
    indices = [i for i, form in enumerate(recent['form']) if form == '10-K']
    if not indices:
        raise ValueError(f"No recent 10-K for {company['ticker']}")
    i = max(indices, key=lambda j: recent['filingDate'][j])
    accession = recent['accessionNumber'][i]
    url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace('-', '')}/{recent['primaryDocument'][i]}"
    output.mkdir(parents=True, exist_ok=True)
    path = output / f"{company['ticker']}_10K_{recent['reportDate'][i][:4]}.pdf"
    if not force and path.is_file() and path.stat().st_size > 0:
        return path
    html = client.get(url).text
    # A local document and blocked remote resources keep rendering reproducible and
    # prevent Chromium from bypassing the SEC HTTP throttle via assets or scripts.
    with TemporaryDirectory(prefix='sec-10k-', dir=output) as temp_dir, sync_playwright() as p:
        html_path = Path(temp_dir).resolve() / 'filing.html'
        rendered_pdf = Path(temp_dir) / 'filing.pdf'
        html_path.write_text(html, encoding='utf-8')
        browser = p.chromium.launch()
        try:
            page = browser.new_page(java_script_enabled=False, service_workers='block')
            page.route('**/*', lambda route: (
                route.abort() if route.request.url.lower().startswith(('http://', 'https://'))
                else route.continue_()))
            page.goto(html_path.as_uri(), wait_until='load')
            page.pdf(path=str(rendered_pdf), format='Letter', print_background=True,
                     margin={'top': '.5in', 'bottom': '.5in', 'left': '.5in', 'right': '.5in'},
                     prefer_css_page_size=False)
        finally:
            browser.close()
        if not rendered_pdf.is_file() or rendered_pdf.stat().st_size == 0:
            raise RuntimeError('Chromium produced an empty PDF')
        rendered_pdf.replace(path)
    path.with_suffix('.source.json').write_text(json.dumps(dict(
        source_url=url, accession=accession, report_date=recent['reportDate'][i],
        filing_date=recent['filingDate'][i], html_sha256=hashlib.sha256(html.encode()).hexdigest(),
        pdf_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        pagination='Chromium Letter, 0.5 inch margins; citations use physical PDF pages'), indent=2))
    return path


def main() -> None:
    load_dotenv(ROOT / '.env')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tickers', nargs='+', default=['NVDA', 'AAPL', 'JPM'])
    parser.add_argument('--force', action='store_true', help='Re-fetch and replace existing local PDFs')
    parser.add_argument('--output', type=Path, default=ROOT / 'data/pdfs')
    args = parser.parse_args()
    companies = json.loads((ROOT / 'config/companies.json').read_text())
    wanted = {t.upper() for t in args.tickers}
    unknown = wanted - {c['ticker'] for c in companies}
    if unknown:
        parser.error(f'Unknown tickers: {sorted(unknown)}')
    logging.basicConfig(level=logging.INFO)
    succeeded: list[str] = []
    skipped: list[str] = []
    failed: list[str] = []
    client: SECClient | None = None
    try:
        for company in companies:
            ticker = company['ticker']
            if ticker not in wanted:
                continue
            try:
                existing = None if args.force else existing_pdf(ticker, args.output)
                if existing is not None:
                    skipped.append(ticker)
                    print(f'SKIPPED {ticker}: {existing}', flush=True)
                    continue
                if client is None:
                    client = SECClient(os.getenv('SEC_USER_AGENT', ''))
                path = download(company, client, args.output, force=args.force)
                succeeded.append(ticker)
                print(f'SUCCEEDED {ticker}: {path}', flush=True)
            except Exception as error:
                failed.append(ticker)
                LOG.error('FAILED %s: %s: %s', ticker, type(error).__name__, error)
    finally:
        if client is not None:
            client.close()
    print(json.dumps({'succeeded': succeeded, 'skipped': skipped, 'failed': failed}, indent=2), flush=True)
    if failed:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
