"""Render the frozen submission report as exactly two Letter pages with Chromium.

Reads existing result artifacts; never invokes ingestion, QA, or evaluation.
Run: python scripts/render_results_pdf.py
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
from html import escape
import json
from pathlib import Path
from tempfile import NamedTemporaryFile

import pymupdf
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def load_report() -> tuple[str, dict]:
    """Cross-check the printed Markdown scores against their full-precision JSON."""
    report = json.loads((ROOT / 'results/eval_report.json').read_text())
    summary = (ROOT / 'results/eval_summary.md').read_text()
    rows = []
    for line in summary.splitlines():
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        if len(cells) == 7 and cells[0] in report['groups']:
            group = report['groups'][cells[0]]
            strict = group['strict']
            expected = [cells[0], str(group['questions']), f"{group['accuracy']:.2%}"] + [
                f'{strict[k]:.2%}' for k in ('precision_macro', 'recall_macro', 'precision_micro', 'recall_micro')]
            if cells != expected:
                raise ValueError('Markdown/JSON result mismatch: ' + cells[0])
            rows.append('<tr' + (' class="overall"' if cells[0] == 'Overall' else '') + '>' +
                        ''.join(f'<td>{escape(c)}</td>' for c in cells) + '</tr>')
    if len(rows) != 4 or report['groups']['Overall']['questions'] != 30:
        raise ValueError('Expected the final 30-question, four-group report')
    baseline = json.loads((ROOT / 'results/eval_report_v1_baseline.json').read_text())
    graph_bytes = (ROOT / 'data/graph/kg.json').read_bytes()
    graph = json.loads(graph_bytes)
    lock = json.loads((ROOT / 'config/extraction_rules.lock.json').read_text())
    digest = hashlib.sha256(json.dumps(lock, sort_keys=True).encode()).hexdigest()
    if digest != report['extraction_rules_digest'] or graph['graph']['extraction_rules_digest'] != digest:
        raise ValueError('Graph, extraction manifest and evaluation digest disagree')
    for name, expected in lock['files'].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            raise ValueError('Frozen extraction file changed: ' + name)
    counts = Counter(n['node_type'] for n in graph['nodes'])
    context = dict(report=report, baseline=baseline, counts=counts, digest=digest,
                   graph_sha256=hashlib.sha256(graph_bytes).hexdigest(),
                   corroborates=sum(e.get('relation') == 'CORROBORATES' for e in graph['edges']))
    return ''.join(rows), context


def build_html() -> str:
    rows, c = load_report()
    g = c['report']['groups']['Overall']
    v1 = c['baseline']['groups']['Overall']['accuracy'] * 100
    v2 = g['accuracy'] * 100
    counts = c['counts']
    # Static prose describes the frozen experiment, not newly inferred KG answers.
    html = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Genloop | Financial Knowledge Graph QA</title>
<style>
@page { size: Letter; margin: 0; }
* { box-sizing: border-box; }
body { margin: 0; color: #182633; background: white; font: 12px/1.43 Arial, Helvetica, sans-serif; }
.sheet { width: 8.5in; height: 11in; padding: .47in .55in .48in; position: relative; break-after: page; }
.sheet:last-child { break-after: auto; }
.eyebrow { color: #147477; text-transform: uppercase; letter-spacing: 1.65px; font-size: 9.3px; font-weight: 700; }
h1 { font-size: 28px; line-height: 1.12; letter-spacing: -.6px; margin: 8px 0 7px; color: #102737; }
.subtitle { margin: 0 0 16px; color: #536470; font-size: 11px; }
h2 { color: #103849; font-size: 14px; margin: 17px 0 8px; padding-bottom: 5px; border-bottom: 1px solid #c9d9dd; }
h2 .number { font-size: 10px; color: #147477; margin-right: 7px; }
p { margin: 0 0 8px; }
strong { color: #17364a; }
code { font: 10.1px/1.35 Menlo, Consolas, monospace; overflow-wrap: anywhere; }
.stats { display: flex; gap: 25px; padding: 10px 14px; background: #edf6f5; border-left: 3px solid #147477; margin-bottom: 11px; }
.stats b { display: block; font-size: 21px; line-height: 1.12; color: #125d65; }
.stats span { font-size: 10px; color: #4c646c; }
table { width: 100%; border-collapse: collapse; font-size: 11px; table-layout: fixed; }
th, td { padding: 7px 6px; text-align: right; border-bottom: 1px solid #dce5e8; white-space: nowrap; }
th { background: #173c4c; color: white; font-size: 10px; font-weight: 600; }
th:first-child, td:first-child { text-align: left; width: 22%; }
th:nth-child(2), td:nth-child(2) { width: 6%; }
.overall td { font-weight: 700; background: #edf6f5; }
.caption { margin-top: 7px; font-size: 10px; color: #556a76; }
.ablation { padding: 9px 12px; background: #f4f6f8; margin: 10px 0 12px; font-size: 10.7px; }
.ablation-line { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.ablation-label { width: 255px; }
.track { width: 210px; background: #dfe7eb; height: 8px; }
.bar { display: block; height: 8px; background: #92a8b3; }
.bar.final { background: #147477; }
.ablation-note { font-size: 9.6px; color: #4c626c; margin: 5px 0 0; }
.method p { margin-bottom: 9px; }
.method strong { display: inline; }
.pipeline { padding: 8px 11px; background: #f3f6f8; font-size: 10.8px; color: #274c5e; margin: 8px 0; }
.failure { border-left: 2px solid #b3c7cf; padding-left: 11px; margin: 0 0 12px; }
.failure h3, .improvement h3 { font-size: 12px; margin: 0 0 4px; color: #183e50; }
.failure p { margin-bottom: 5px; }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 13px 17px; }
.improvement { padding: 10px 11px; border: 1px solid #d7e2e6; background: #f9fbfc; break-inside: avoid; }
.improvement p { margin: 0; font-size: 11.5px; }
.reproduce { padding: 9px 12px; border-left: 3px solid #147477; background: #edf6f5; margin: 15px 0 8px; font-size: 10.5px; }
.sources { font-size: 9.6px; line-height: 1.5; color: #526875; margin-top: 10px; }
.footer { position: absolute; left: .55in; right: .55in; bottom: .28in; display: flex; justify-content: space-between; border-top: 1px solid #cedce2; padding-top: 6px; font-size: 9px; color: #617780; }
</style></head><body>
<section class="sheet"><div class="content">
<div class="eyebrow">Genloop take-home / Results v2 / Extraction lock v3</div>
<h1>Financial Knowledge Graph QA</h1>
<p class="subtitle">35 SEC Form 10-K filings across five sectors | Reified NetworkX graph | Physical-page provenance</p>
<h2><span class="number">01</span>Final Results</h2>
<div class="stats"><div><b>__ACC__</b><span>Answer accuracy</span></div><div><b>__MACROP__</b><span>Macro fact precision</span></div><div><b>__MACROR__</b><span>Macro fact recall</span></div></div>
<table><thead><tr><th>Question type</th><th>N</th><th>Accuracy</th><th>Macro P</th><th>Macro R</th><th>Micro P</th><th>Micro R</th></tr></thead><tbody>__ROWS__</tbody></table>
<p class="caption">Strict exact-page scores. Multi-hop and cross-filing micro precision: 100%. Zero-key offline replay is identical: 29 cached plans + 1 deterministic fallback.</p>
<div class="ablation" aria-label="Software ablation accuracy comparison">
<div class="ablation-line"><span class="ablation-label"><strong>v1: __V1__%</strong> - initial planner/scorer</span><span class="track"><span class="bar" style="width:__V1__%"></span></span></div>
<div class="ablation-line"><span class="ablation-label"><strong>v2: __V2__%</strong> - five general software fixes</span><span class="track"><span class="bar final" style="width:__V2__%"></span></span></div>
<p class="ablation-note">Identical KG and benchmark; no extraction/gold edits. Extraction-lock digest <code>__SHORT_DIGEST__...</code>. Gains include planner, DSL, grounding, formatter and scorer fixes.</p>
</div>
<h2><span class="number">02</span>Methodology</h2>
<div class="method">
<p><strong>Graph architecture.</strong> Typed, reified NetworkX <code>MultiDiGraph</code> over 35 S&amp;P 500 companies in five sectors: __METRICS__ <code>MetricObservation</code> nodes (base USD; unscaled EPS; positive analytical CAPEX), __RELATIONS__ <code>RelationClaim</code> nodes, and __ENTITIES__ canonical <code>ExternalEntity</code> nodes. __CORROBORATES__ <code>CORROBORATES</code> edges retain secondary evidence without double-counting; active-only traversal handles duplicate evidence such as Apple's two audit reports on physical pp. 85-86. Each fact retains document, page, section and original snippet.</p>
<p><strong>Hybrid extraction and freeze.</strong> Deterministic section/table/cover/auditor parsing yields Revenue and Net Income for 34/35 companies, HQ for 35/35 and auditor for 34/35. There are 21 supported zero-residual balance sheets; 13 identities are unavailable and one is nonzero. Separate ASC 480-10-S99-3A mezzanine/redeemable-equity diagnostics cover UNH, BLK, TMO and WMT, without forcing a balance. Qualitative LLM extraction selects at most 10 ranked pages/filing and gates admission on normalized contiguous-quote verification. Extraction lock v3 preceded benchmark authoring.</p>
<div class="pipeline">Concept resolver &rarr; LLM-compiled, Pydantic-validated <code>GraphQueryPlan</code> AST &rarr; deterministic Python/NetworkX executor &rarr; cited answer or explicit abstention.</div>
<p><strong>Query execution.</strong> Zero vector search, embeddings or PDF-chunk RAG. All facts and arithmetic come from structured graph lookups/traversals, with exact fact-level provenance tracking. The provider-agnostic client caches validated responses in SQLite; offline execution makes no model requests. Live failures are fail-closed unless deterministic fallback is explicitly enabled.</p>
<p><strong>Benchmark preparation and verification.</strong> Thirty self-authored questions (10 single-fact, 10 multi-hop, 10 cross-filing) span all 35 companies and five sectors. Cross-filing financial comparisons use issuer-reported FY2025. Gold was derived strictly from raw PDFs with PyMuPDF, without reading <code>kg.json</code>, <code>metric_coverage.md</code> or caches. <code>validate_benchmark.py</code> independently checks 85 unique evidence records, 97 annotations and 64 physical PDF pages; human spot checks used <code>verify_helper.py</code>. All page numbers are 1-indexed physical PDF pages.</p>
</div>
</div><div class="footer"><span>SEC Context Graph | Frozen submission</span><span>1 / 2</span></div></section>
<section class="sheet"><div class="content">
<div class="eyebrow">Failure analysis / Enterprise context-graph roadmap</div>
<h2><span class="number">03</span>Gaps &amp; Failure Analysis</h2>
<div class="failure"><h3>KG extraction and closed-world gaps</h3>
<p><strong>Q10:</strong> P&amp;G's five reportable segments are conflated with ten product categories on p. 83. Fifteen returned targets lower single-fact micro precision to <strong>31.82%</strong>. Contiguous text presence did not establish the correct accounting concept.</p>
<p><strong>Q28:</strong> Missing multi-line diluted EPS for BAC/GS/MS/BLK triggers an honest abstention rather than an unsupported ranking. <strong>Q30:</strong> BAC's vertical cover-page incorporation claim was missed; a closed-world count returns <strong>6 instead of 7</strong>. Corpus limitations also include WFC's financial statements incorporated by reference and MRK's unlabeled asset total.</p></div>
<div class="failure"><h3>Planner over-abstention and fallback variance</h3>
<p><strong>Q08 (GS auditor)</strong> and <strong>Q09 (COST HQ)</strong> over-abstain despite existing relation edges. In the live run, <strong>Q19</strong> exhausted JSON retries after HTTP 429 caused model fallback to <code>gemini-3.1-flash-lite</code>; its zero-key deterministic fallback also abstains. Provider/model variance remains visible rather than being filled with guessed answers.</p></div>
<div class="failure"><h3>Traversal versus exhaustive recall</h3>
<p><strong>Q17, Q18, Q20 and Q29</strong> achieve 100% answer accuracy and 100% retrieved-fact precision. Strict recall loses credit only for conservatively annotated excluded-candidate classification facts that the successful graph traversal did not retrieve. The gold annotation policy and minimal execution trace measure different evidence scopes.</p></div>
<h2><span class="number">04</span>Improvements With More Time</h2>
<div class="grid">
<div class="improvement"><h3>1. Completeness certificates</h3><p>Track company/document/period/predicate coverage and require a completeness certificate before sector counts or rankings. Use open-world abstention when membership evidence is incomplete, addressing Q30. Preserve the evidence set and completeness state as auditable context-graph artifacts.</p></div>
<div class="improvement"><h3>2. Accounting and layout constraints</h3><p>Use accounting-identity-gated semantic learning plus layout-aware <code>pdfplumber</code> cell parsing for multi-line bank EPS and unlabeled totals (Q28/MRK). Distinguish missing evidence from rounding or temporary equity; admit a learned mapping only with original-page evidence and held-out validation.</p></div>
<div class="improvement"><h3>3. Typed segments and entailment</h3><p>Separate ASC 280 reportable/operating segments from product lines in the ontology and validate relation target types. Add NLI entailment checks beyond substring containment to address Q10, while retaining the original quote as the provenance anchor.</p></div>
<div class="improvement"><h3>4. Temporal and access context</h3><p>Add effective-period scope to auditor/CEO relations for historical questions. Extend to quarterly 10-Qs with graph pruning, versioned conflicts and consolidation. Enforce RBAC-scoped subgraph traversal so authorized evidence, temporal context and the decision trace remain linked.</p></div>
</div>
<div class="reproduce"><strong>Reproduce with zero API keys</strong><br><code>LLM_API_KEY="" python -m src.eval.run_eval --offline</code><br>Export the cached primary/fallback model names from README first; neither PDFs nor Chromium are needed to evaluate the committed graph and cache.</div>
<p class="sources"><strong>Scoring and artifacts.</strong> Accuracy uses 1% numeric tolerance and normalized entities. Macro P/R average per-question scores; micro P/R pool matched/retrieved/gold facts (71/86/97). Primary fact matching uses exact document/page/company/predicate/period. Page +/- 1 is diagnostic only and additionally checks relation targets; its final aggregate scores are identical here.<br>Sources: <code>results/eval_summary.md</code>, <code>results/failure_analysis.md</code>, <code>results/ingestion_audit.json</code>, and <code>results/benchmark_verification.md</code>.<br>Extraction-manifest digest: <code>__DIGEST__</code><br>Frozen graph SHA-256: <code>__GRAPH_SHA__</code></p>
</div><div class="footer"><span>SEC Context Graph | Evidence retained; extraction gaps unchanged</span><span>2 / 2</span></div></section>
</body></html>'''
    values = {
        '__ACC__': f"{g['accuracy']:.2%}", '__MACROP__': f"{g['strict']['precision_macro']:.2%}",
        '__MACROR__': f"{g['strict']['recall_macro']:.2%}", '__ROWS__': rows,
        '__V1__': f'{v1:.2f}', '__V2__': f'{v2:.2f}', '__SHORT_DIGEST__': c['digest'][:16],
        '__METRICS__': str(counts['MetricObservation']), '__RELATIONS__': str(counts['RelationClaim']),
        '__ENTITIES__': str(counts['ExternalEntity']), '__CORROBORATES__': str(c['corroborates']),
        '__DIGEST__': c['digest'], '__GRAPH_SHA__': c['graph_sha256'],
    }
    for key, value in values.items():
        html = html.replace(key, value)
    return html


def render(output: Path) -> dict:
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    html = build_html()
    with NamedTemporaryFile(suffix='.pdf', dir=output.parent, delete=False) as temp:
        temporary = Path(temp.name)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            try:
                page = browser.new_page(viewport={'width': 816, 'height': 1056})
                page.route('**/*', lambda route: route.abort())
                page.set_content(html, wait_until='load')
                page.emulate_media(media='print')
                page.evaluate('document.fonts.ready')
                layout = page.evaluate('''() => [...document.querySelectorAll('.sheet')].map(sheet => {
                    const box=sheet.getBoundingClientRect(), content=sheet.querySelector('.content').getBoundingClientRect();
                    const footer=sheet.querySelector('.footer').getBoundingClientRect();
                    return {contentBottom:content.bottom-box.top, footerTop:footer.top-box.top,
                      width:box.width,height:box.height, overflow:sheet.scrollHeight>sheet.clientHeight+1,
                      clippedCells:[...sheet.querySelectorAll('td,th')].filter(cell=>cell.scrollWidth>cell.clientWidth+1).length};
                })''')
                if len(layout) != 2 or any(x['overflow'] or x['clippedCells'] or x['contentBottom'] > x['footerTop'] - 8 for x in layout):
                    raise ValueError('Report content exceeds its page/table bounds: ' + json.dumps(layout))
                page.pdf(path=str(temporary), format='Letter', print_background=True, prefer_css_page_size=True,
                         margin={'top': '0', 'bottom': '0', 'left': '0', 'right': '0'})
            finally:
                browser.close()
        with pymupdf.open(temporary) as doc:
            if len(doc) != 2:
                raise ValueError(f'Expected exactly 2 PDF pages; got {len(doc)}')
            for page in doc:
                if abs(page.rect.width - 612) > 1 or abs(page.rect.height - 792) > 1:
                    raise ValueError('Expected US Letter page dimensions')
                for word in page.get_text('words'):
                    if word[0] < 26 or word[1] < 22 or word[2] > 586 or word[3] > 780:
                        raise ValueError('Text extends beyond safe page margins')
        temporary.replace(output)
        output.with_suffix('.html').write_text(html)
        return dict(pdf=str(output), pages=2, format='US Letter', bytes=output.stat().st_size, layout=layout)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'results/Genloop_TakeHome_Results.pdf')
    args = parser.parse_args()
    print(json.dumps(render(args.output), indent=2))


if __name__ == '__main__':
    main()
