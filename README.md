# SEC Context Graph

A financial knowledge graph QA system built over 35 SEC Form 10-K PDFs across five sectors. Instead of using vector search, embeddings, or PDF-chunk RAG, each question is compiled into a validated query-plan AST and answered directly through NetworkX lookups, graph traversals, and Python arithmetic. Every answer cites its retrieved fact IDs and exact **1-indexed physical PDF pages**, or explicitly abstains if the data is missing.

**Frozen v2 results:** 80.00% accuracy, 86.67% macro precision, and 79.34% macro recall. You can reproduce these exact numbers offline with no API key. For the full breakdown, see the [Report](results/Genloop_TakeHome_Results.pdf).

## Quickstart: offline evaluation (no API key needed)

From the repository root, using Python 3.11+:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Next, export the model names used by the shipped cache. These only select cache keys and will not make any network calls. You do not need a `.env` file, raw PDFs, Chromium, or an API key for offline mode:

```sh
export LLM_MODEL=gemini-3.5-flash-lite LLM_FALLBACK_MODELS=gemini-3.6-flash,gemini-3.1-flash-lite
LLM_API_KEY="" python -m src.eval.run_eval --offline
LLM_API_KEY="" python scripts/ask.py --offline "What was Microsoft (MSFT) total revenue in FY2025?"
```

Both [kg.json](data/graph/kg.json) and [llm_cache.sqlite](.cache/llm_cache.sqlite) must be present for this to work. Offline mode never calls an LLM endpoint: it replays validated cached query plans and falls back to the deterministic planner on cache misses. The frozen run uses **29 cached plans + 1 deterministic fallback**. Changing the model names or rewording questions can change cache hits and fallback behavior.

| Question type | N | Accuracy | Macro P | Macro R | Micro P | Micro R |
|---|---:|---:|---:|---:|---:|---:|
| Single-fact | 10 | 70.00% | 70.00% | 70.00% | 31.82% | 50.00% |
| Multi-hop | 10 | 90.00% | 90.00% | 81.84% | 100.00% | 74.36% |
| Cross-filing | 10 | 80.00% | 100.00% | 86.19% | 100.00% | 79.55% |
| **Overall** | **30** | **80.00%** | **86.67%** | **79.34%** | **82.56%** | **73.20%** |

Accuracy uses a 1% numeric tolerance and normalized entity matching. Primary precision and recall require an exact match on document, page, company, predicate, and period. Page +/- 1 is tracked as a separate diagnostic that also checks relation targets. Missing facts trigger an abstention, though relation counts still carry a closed-world completeness limitation.

## Live mode and full rebuild

If you want to run live LLM queries or rebuild the graph from scratch:

```sh
cp .env.example .env
python -m playwright install chromium
```

Fill in `.env` (see [.env.example](.env.example)) and keep it private:

| Variable | Purpose |
|---|---|
| `SEC_USER_AGENT` | Your name and real contact email for SEC EDGAR requests. |
| `LLM_BASE_URL` | Any OpenAI-compatible chat-completions endpoint. |
| `LLM_API_KEY` | Your provider API key. Leaving this empty forces offline mode. |
| `LLM_MODEL` | Primary model. The submission cache uses `gemini-3.5-flash-lite`. |
| `LLM_FALLBACK_MODELS` | Optional comma-separated fallback models for HTTP 429/503 errors. Cached replay also searches these models. The submission uses `gemini-3.1-flash-lite`. |

Optional settings include `LLM_REASONING_EFFORT=low`, `LLM_MIN_INTERVAL_SECONDS`, and `PLANNER_ALLOW_LIVE_FALLBACK=false` (the default). Live planner errors fail closed unless fallback is explicitly enabled. Also note that shell environment variables override `.env`, so update or unset the quickstart exports before switching providers.

Keep in mind that the submission graph, benchmark, and extraction rules are frozen. Rebuilding is meant for separate experiments: downloading today's latest filings can shift fiscal years and page numbers, so it will not reproduce the original PDF-verified benchmark.

```sh
# Download all 35 latest filings (existing non-empty PDFs are skipped).
python -m src.ingest.download_sec_pdfs
# Run full live extraction into a separate graph file.
python scripts/build_kg.py --output data/graph/kg_rebuild.json
# Or rebuild using only the extraction cache, with no LLM calls.
python scripts/build_kg.py --offline --output data/graph/kg_rebuild.json
# Check gold evidence against the original local PDFs, then run the test suite.
python scripts/validate_benchmark.py
python -m pytest -q
# Run live query planning against the frozen submission graph.
python -m src.eval.run_eval
```

For smaller test runs, `build_kg.py` supports `--tickers NVDA AAPL JPM`, `--limit N`, and `--skip-llm`. The builder writes to `data/graph/kg.json` by default, so only omit `--output` if you intentionally want to overwrite it. SEC downloads use a compliant User-Agent, stay at or below 4 requests/second, and retry transient errors. Chromium renders local HTML with remote network requests blocked.

## How it works and how it was verified

- **Graph structure:** The graph stores 979 `MetricObservation` nodes, 579 `RelationClaim` nodes, and 291 canonical `ExternalEntity` nodes. Duplicate disclosures are linked with 202 `CORROBORATES` edges so secondary evidence is preserved without double-counting. Queries only read active claims and ignore superseded or corroborating edges.
- **Hybrid extraction:** Deterministic parsers handle financial statements, unit scales, cover pages, and auditor signatures. For qualitative relations, an LLM checks at most 10 ranked pages per filing and only keeps claims whose normalized quote appears word-for-word on that page. CAPEX keeps its reported sign alongside a positive analytical magnitude, and EPS is stored as unscaled USD/share.
- **Independent benchmark:** 30 questions (10 single-fact, 10 multi-hop, 10 cross-filing) cover all 35 companies. Gold answers were pulled directly from raw PDFs without looking at the graph, coverage stats, or caches: 85 unique evidence records, 97 fact annotations, and 64 physical PDF pages. Cross-filing financial comparisons use issuer-reported FY2025 numbers.
- **Extraction freeze:** All extraction rules were locked in [extraction lock v3](config/extraction_rules.lock.json) before the benchmark was written, and builds check this lock before running. Its canonical extraction-manifest digest is `d1cd573dffd1ad457748f377d98b45c160710ccb807ee9f2e89f7da6b2c4010e` (note that this is the manifest digest, not the file hash of `kg.json`).

You can inspect the full evidence trail in the [gold verification sheet](results/benchmark_verification.md). If you have the original PDFs locally, you can check any source page directly with `python -m src.eval.verify_helper MSFT_10K_2026.pdf --page 82`. Raw PDFs are not checked into git, and neither graph QA nor offline evaluation requires them.

**Known gaps:** The frozen run still has a few visible gaps: mixing P&G's reportable segments with product lines (Q10), missing bank EPS values (Q28), a missed BAC incorporation claim causing a count of 6 instead of 7 (Q30), and some planner over-abstentions or provider variance. Because the gold benchmark conservatively includes excluded-candidate classification facts, correct relation-filtered answers can also take a small hit on strict recall. See [failure analysis](results/failure_analysis.md) for the exact traces. No extraction rules or gold answers were touched to boost v2 scores.

## Repository layout

| Path | Purpose |
|---|---|
| [`config/`](config/) | Company catalog, ontology, and frozen extraction manifest. |
| [`src/ingest/`](src/ingest/), [`src/extract/`](src/extract/), [`src/graph/`](src/graph/) | SEC downloader, PDF parsing, quote-verified extraction, entity resolution, and NetworkX graph storage. |
| [`src/query/`](src/query/), [`src/eval/`](src/eval/) | Concept grounding, validated AST planning, deterministic execution, scoring, and verification tools. |
| [`benchmark/questions.json`](benchmark/questions.json) | Frozen 30-question independent benchmark. |
| [`data/graph/kg.json`](data/graph/kg.json) | Frozen, portable submission graph. |
| [`.cache/llm_cache.sqlite`](.cache/llm_cache.sqlite) | Cached extraction responses and query plans for offline replay. |
| [`results/eval_summary.md`](results/eval_summary.md) | Overall and per-type scores, planner sources, and run metadata. |
| [`results/failure_analysis.md`](results/failure_analysis.md) | Detailed failures, missed/extra facts, query plans, and execution traces. |
| [`results/Genloop_TakeHome_Results.pdf`](results/Genloop_TakeHome_Results.pdf) | Two-page technical results report. |
| [`scripts/render_results_pdf.py`](scripts/render_results_pdf.py), [`tests/`](tests/) | Script to regenerate the PDF report with Chromium, plus the regression test suite. |

## AI Tool Usage

- **Claude Sonnet 5.5:** code generation and resolving doubts
- **Gemini Flash-3.8:** report generation and editing, README generation