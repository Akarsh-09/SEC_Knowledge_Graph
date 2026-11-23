# Evaluation summary

Benchmark: `/Users/akarshjain/Desktop/genloop-th-assignment/benchmark/questions.json`

| Question type | N | Accuracy | Precision macro | Recall macro | Precision micro | Recall micro |
|---|---:|---:|---:|---:|---:|---:|
| single-fact | 10 | 70.00% | 70.00% | 70.00% | 31.82% | 50.00% |
| multi-hop | 10 | 90.00% | 90.00% | 81.84% | 100.00% | 74.36% |
| cross-filing | 10 | 80.00% | 100.00% | 86.19% | 100.00% | 79.55% |
| Overall | 30 | 80.00% | 86.67% | 79.34% | 82.56% | 73.20% |

## Secondary page +/- 1 diagnostic

This never replaces exact-page primary scoring.

| Question type | Precision macro | Recall macro | Precision micro | Recall micro |
|---|---:|---:|---:|---:|
| single-fact | 70.00% | 70.00% | 31.82% | 50.00% |
| multi-hop | 90.00% | 81.84% | 100.00% | 74.36% |
| cross-filing | 100.00% | 86.19% | 100.00% | 79.55% |
| Overall | 86.67% | 79.34% | 82.56% | 73.20% |

## Planner sources

| Source | Questions |
|---|---:|
| deterministic_fallback | 1 |
| llm_cache | 29 |

## Run metadata

Benchmark: `/Users/akarshjain/Desktop/genloop-th-assignment/benchmark/questions.json`
Questions: **30**
Frozen extraction digest: `d1cd573dffd1ad457748f377d98b45c160710ccb807ee9f2e89f7da6b2c4010e`
Benchmark SHA-256: `10c2422456a5efdb3b29cb6844e0a04daefde3a308f778cc9770d143e5454add`
Methodology: exact-page strict primary scoring; separate page +/- 1 diagnostic with relation-target matching.

## Design scope and future improvements

- **Graph completeness:** missing relations do not establish absence. Counts/rankings are over recorded graph evidence; future work needs extraction coverage and completeness certificates before exhaustive claims.
- **Historical audit scope:** auditor metadata is filing-level, without effective-period/audit-period modeling. Historical-year metrics do not independently prove that year's auditor. Add temporal relation scope before historical auditor comparisons.
- **Comparability:** revenue/debt definitions and CAPEX scope differ across issuers. Positive analytical CAPEX fixes signs, not definitions. Reported label differences are surfaced; future work needs definition/scope tags and comparison eligibility rules.
- **Entailment:** normalized quote matching proves original-page textual presence, not that a claimed relationship follows from the quote. Add human sampling, negative examples and semantic checks for live extraction.

## Interpretation

Strict primary fact matching requires exact document/page/company/predicate/period and preserves the original scoring definition (it does not compare expected_value). The separate page +/- 1 diagnostic relaxes only page distance for metrics; relation claims must additionally match the normalized gold expected_value against the retrieved target/value, including on the same page. The diagnostic never replaces primary scoring and can be lower when unrelated same-page relation targets would otherwise match. Duplicate retrieved facts consume precision denominator slots and cannot reuse a gold match. Empty retrieved/gold denominators score zero. Numeric tolerance is 1% relative (1e-12 absolute near zero); ratio/percent conversion requires explicit units. Unordered entity lists use sets; ranking questions preserve order. Entity answers normalize EXT IDs, punctuation and US postal state abbreviations.

Fallback guards cover recognized unsupported constraints and unresolved named qualifiers, not every possible modifier. Offline cache misses use deterministic planning; live failures remain closed unless PLANNER_ALLOW_LIVE_FALLBACK is explicitly enabled. Every prediction records its planner_source. Ingestion audits expose missing coverage and unavailable balance identities rather than inventing values. Run metadata identifies the benchmark, question count and active frozen-rule digest. Query-engine revisions do not change extraction.
