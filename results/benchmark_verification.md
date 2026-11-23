# Independent 30-question benchmark verification

**Status: source-verified draft awaiting human sign-off. Evaluation has not been run.**

All gold values, targets, and physical page numbers were derived directly from the 35 local PDFs using PyMuPDF, not from the graph, metric coverage report, extraction cache, or query predictions. Company configuration and ontology supply identifiers and sector membership only. The frozen extraction files, main graph, and LLM cache were not changed.

There are 10 single-fact, 10 multi-hop, and 10 cross-filing questions. Supporting evidence spans all 35 companies and five configured sectors: 85 unique fact records, 97 fact annotations across questions, and 63 physical question-evidence pages, plus WFC p. 2 for the corpus diagnostic. Single-fact means a direct lookup; Q10 returns five segment targets in one hop.

## Review conventions

- Page numbers below are **1-indexed physical PDF pages**, not the printed annual-report folios. Each evidence heading gives the exact filename. Separate fenced blocks are separate exact contiguous excerpts; they must not be read as one stitched quote. The machine-readable evidence preserves original whitespace.
- All cross-company financial comparisons use **issuer-reported FY2025**, not filename year or a common calendar window. FY2026 documents supply their FY2025 comparative columns. Home Depot’s FY2025 ends February 1, 2026 despite the PDF filename ending 2026. FY2024 appears only as the base for TXN growth.
- Financial amounts are converted from the statement’s millions to USD. EPS is USD/share, multiplier 1. Percent answers use the 0–100 percent scale (0.15 becomes 15%); ratios are dimensionless times. Gold JSON retains full floating-point arithmetic precision; display rounding below is for review only.
- CAPEX supporting facts retain the signed cash-flow figure. Expenditure answers and free cash flow use its absolute value. Free cash flow here excludes acquisitions, lease principal, supplemental noncash additions, and proceeds from disposals.
- “Net income” uses the explicit consolidated line before parent/noncontrolling-interest attribution or preferred dividends. Q11 and Q22 state that scope expressly. Auditor and CEO relations describe the **supplied filing**, not an inferred effective-date history or current-day officeholder.
- Rankings include every metric in the named candidate set. Exhaustive auditor filters include classifications for **all candidates**, including exclusions; headquarters selection includes all three cover addresses. This conservative annotation policy makes the population checkable. A query returning only matching-company facts can answer correctly while losing recall on the omitted candidate-classification evidence.
- Strict evaluator provenance compares document/page/company/predicate/period. It does not compare expected_value or relation target. Each named segment in Q10 is nevertheless annotated as a distinct claim. An equivalent valid fact cited on another PDF page may lose strict fact credit; these source pages were chosen independently of graph provenance.

## Corpus limitation discovered from the PDFs

`WFC_10K_2025.pdf` contains 36 pages and incorporates its financial statements by reference rather than reproducing them. Q28 therefore explicitly names six Financials companies and makes no seven-company numeric claim. WFC participates in Q30 using its cover-page incorporation evidence. No missing financial value was inferred or fetched externally.

Exact WFC p. 2 incorporation-by-reference excerpt:

```text
1. Portions of the Company’s Annual Report to Shareholders for the year ended December 31,     Part I – Items 1, 1A, 1C and 3; Part II – Items 5, 7, 7A, 8 and 9A; and
  2025 (“2025 Annual Report to Shareholders”)                                                  Part IV– Item 15
```

## Quick review: all questions

| ID | Type | Question | Golden answer |
|---|---|---|---|
| [Q01](#q01) | single-fact | What was Microsoft (MSFT) total revenue in FY2025? | USD 281,724,000,000 |
| [Q02](#q02) | single-fact | What was Eli Lilly (LLY) net income in FY2025? | USD 20,640,000,000 |
| [Q03](#q03) | single-fact | What were AMD diluted earnings per share in FY2025, including discontinued operations? | USD 2.65/share |
| [Q04](#q04) | single-fact | What were UnitedHealth Group (UNH) total assets at December 31, 2025? | USD 309,581,000,000 |
| [Q05](#q05) | single-fact | According to the supplied filings, which company completed the acquisition of Preqin Holding Limited (Preqin)? | COMP:BLK |
| [Q06](#q06) | single-fact | What was Pfizer (PFE) FY2025 cash spending on purchases of property, plant and equipment, expressed as a positive USD amount? | USD 2,629,000,000 |
| [Q07](#q07) | single-fact | What was Merck (MRK) research and development expense in FY2025? | USD 15,789,000,000 |
| [Q08](#q08) | single-fact | Which independent registered public accounting firm signed the financial-statement audit report in the supplied Goldman Sachs (GS) 10-K? | EXT:PWC |
| [Q09](#q09) | single-fact | In which city and state are Costco (COST) principal executive offices located, as printed on the supplied 10-K cover? | Issaquah, WA |
| [Q10](#q10) | single-fact | List the five US GAAP reportable segments of Procter & Gamble (PG) named in its supplied segment-information note. | Beauty, Grooming, Health Care, Fabric & Home Care, Baby, Feminine & Family Care |
| [Q11](#q11) | multi-hop | What was Thermo Fisher Scientific (TMO) FY2025 net margin, using consolidated net income before attribution to noncontrolling interests divided by total revenues, as a percent? | 15.084388186% |
| [Q12](#q12) | multi-hop | What was Oracle (ORCL) operating margin in FY2025, defined as operating income divided by total revenues, as a percent? | 30.798445966% |
| [Q13](#q13) | multi-hop | What was Intel (INTC) FY2025 R&D intensity, defined as research and development expense divided by net revenue, as a percent? | 26.060961535% |
| [Q14](#q14) | multi-hop | What was Home Depot (HD) free cash flow in FY2025, defined as operating cash flow minus the absolute value of cash capital expenditures? | USD 12,646,000,000 |
| [Q15](#q15) | multi-hop | What was Texas Instruments (TXN) revenue growth from FY2024 to FY2025, as a percent? | 13.049037785% |
| [Q16](#q16) | multi-hop | At December 31, 2025, what was JPMorgan Chase (JPM) ratio of reported long-term debt to total stockholders’ equity? | 1.20077364956 times |
| [Q17](#q17) | multi-hop | Among the seven Semiconductors companies in the corpus, using the auditor identified in each supplied filing, which PwC-audited company had the highest FY2025 consolidated net income? | COMP:NVDA |
| [Q18](#q18) | multi-hop | Among Costco (COST), Home Depot (HD) and Target (TGT), what was the FY2025 operating margin of the company whose supplied cover lists principal executive offices in Issaquah, WA? Give a percent using total revenue. | 3.772412666% |
| [Q19](#q19) | multi-hop | Among Eli Lilly (LLY), Pfizer (PFE) and Merck (MRK), who is identified as CEO in the supplied filing of the company with the highest FY2025 research and development expense? | Robert M. Davis |
| [Q20](#q20) | multi-hop | Among Apple (AAPL), Microsoft (MSFT) and Alphabet (GOOGL), using the auditor identified in each supplied filing, which EY-audited company had the highest FY2025 free cash flow, defined as operating cash flow minus cash purchases of property, plant and equipment? | COMP:AAPL |
| [Q21](#q21) | cross-filing | What was the FY2025 revenue difference, Coca-Cola (KO) minus PepsiCo (PEP), in USD? | USD -45,984,000,000 |
| [Q22](#q22) | cross-filing | What was the FY2025 net income difference, JPMorgan Chase (JPM) minus Bank of America (BAC), before preferred dividends, in USD? | USD 26,539,000,000 |
| [Q23](#q23) | cross-filing | What was the ratio of NVIDIA (NVDA) FY2025 research and development expense to AMD FY2025 research and development expense? | 1.59609442591 times |
| [Q24](#q24) | cross-filing | Which company had higher total revenue in FY2025: Eli Lilly (LLY) or Pfizer (PFE)? | COMP:LLY |
| [Q25](#q25) | cross-filing | What was the FY2025 operating cash flow difference, Walmart (WMT) minus Costco (COST), in USD? | USD 23,108,000,000 |
| [Q26](#q26) | cross-filing | Which of the seven Healthcare & Pharma companies in the corpus had the highest reported total revenue in FY2025? | COMP:UNH |
| [Q27](#q27) | cross-filing | Rank the top 3 companies in the Big Tech & Cloud sector of the corpus by FY2025 net income, highest first. | COMP:GOOGL, COMP:AAPL, COMP:MSFT |
| [Q28](#q28) | cross-filing | Among JPMorgan Chase (JPM), Bank of America (BAC), Goldman Sachs (GS), Morgan Stanley (MS), Citigroup (C) and BlackRock (BLK), which had the lowest FY2025 diluted earnings per share? | COMP:BAC |
| [Q29](#q29) | cross-filing | List all companies in the corpus Semiconductors sector whose supplied financial-statement audit report is signed by Ernst & Young (EY). | COMP:AMD, COMP:INTC, COMP:TXN |
| [Q30](#q30) | cross-filing | How many of the seven Financials companies in the corpus identify Delaware as their state of incorporation on the supplied 10-K cover? | 7 count |

## Exact source evidence and arithmetic

For each question, the fact descriptions below give canonical predicate, period, and expected source value. Source values remain signed where printed. Repeated source pages are shown again where needed so each question is independently reviewable.

### Q01

**Gold: USD 281,724,000,000**

**Verification:** 281,724 million × 1,000,000.

**[MSFT_10K_2026.pdf, p. 82](../data/pdfs/MSFT_10K_2026.pdf#page=82)**

- `COMP:MSFT` · `METRIC:REVENUE` · `FY2025` · expected source value: `281724000000` (raw `281,724`, scale `1,000,000`).

```text
(In millions, except per share amounts)
```

```text
Year Ended June 30,                                                                       2026            2025            2024
```

```text
   Total revenue                                                     331,839      281,724      245,122
```

---

### Q02

**Gold: USD 20,640,000,000**

**Verification:** 20,640 million × 1,000,000.

**[LLY_10K_2025.pdf, p. 86](../data/pdfs/LLY_10K_2025.pdf#page=86)**

- `COMP:LLY` · `METRIC:NET_INCOME` · `FY2025` · expected source value: `20640000000` (raw `20,640`, scale `1,000,000`).

```text
                                           (Dollars and shares in millions, except per-share data)
```

```text
                                                                             2025            2024            2023
```

```text
Net income                                                $     20,640  $     10,590  $      5,240
```

---

### Q03

**Gold: USD 2.65/share**

**Verification:** The total diluted EPS row is 2.65 USD/share; no millions multiplier.

**Scope:** The 2.61 continuing-operations EPS row is not total diluted EPS.

**[AMD_10K_2025.pdf, p. 90](../data/pdfs/AMD_10K_2025.pdf#page=90)**

- `COMP:AMD` · `METRIC:EPS_DILUTED` · `FY2025` · expected source value: `2.65` (raw `2.65`, scale `1`).

```text
                                                                       2025               2024               2023
```

```text
                                                                                                      (In millions, except per share amounts)
```

```text
Diluted earnings per share                              $         2.65  $          1.00  $          0.53
```

---

### Q04

**Gold: USD 309,581,000,000**

**Verification:** 309,581 million × 1,000,000.

**[UNH_10K_2025.pdf, p. 72](../data/pdfs/UNH_10K_2025.pdf#page=72)**

- `COMP:UNH` · `METRIC:TOTAL_ASSETS` · `FY2025` · expected source value: `309581000000` (raw `309,581`, scale `1,000,000`).

```text
 (in millions, except per share data)                                                                           2025             2024
```

```text
Total assets                                                                     $    309,581  $    298,278
```

---

### Q05

**Gold: COMP:BLK**

**Verification:** BlackRock explicitly states that it completed the acquisition of 100% of Preqin on March 3, 2025.

**Scope:** A completed acquisition, not a pending agreement or hypothetical plan. One incoming ACQUIRED traversal identifies the acquirer.

**[BLK_10K_2025.pdf, p. 133](../data/pdfs/BLK_10K_2025.pdf#page=133)**

- `COMP:BLK` · `ACQUIRED` · `filing-level` · expected source value: `Preqin Holding Limited`

```text
On March 3, 2025, BlackRock completed the acquisition of 100% of the shares of Preqin Holding Limited (the "Preqin Transaction" or
"Preqin"), a leading provider of private markets data, for £2.5 billion (or approximately $3.2 billion) in cash.
```

---

### Q06

**Gold: USD 2,629,000,000**

**Verification:** abs(−2,629 million) = 2,629,000,000 USD.

**Scope:** The gold supporting fact preserves the signed cash-flow value; the answer reports expenditure magnitude.

**[PFE_10K_2025.pdf, p. 117](../data/pdfs/PFE_10K_2025.pdf#page=117)**

- `COMP:PFE` · `METRIC:CAPEX` · `FY2025` · expected source value: `-2629000000` (raw `(2,629)`, scale `1,000,000`).

```text
(MILLIONS)                                                                                           2025        2024        2023
```

```text
Purchases of property, plant and equipment                                                                             (2,629)        (2,909)        (3,907)
```

---

### Q07

**Gold: USD 15,789,000,000**

**Verification:** 15,789 million × 1,000,000.

**[MRK_10K_2025.pdf, p. 144](../data/pdfs/MRK_10K_2025.pdf#page=144)**

- `COMP:MRK` · `METRIC:RD_EXPENSE` · `FY2025` · expected source value: `15789000000` (raw `15,789`, scale `1,000,000`).

```text
($ in millions except per share amounts)
```

```text
                                                                                      2025        2024        2023
```

```text
  Research and development                                                                      15,789        17,938        30,531
```

---

### Q08

**Gold: EXT:PWC**

**Verification:** The financial-statement audit report is signed by PricewaterhouseCoopers LLP.

**[GS_10K_2025.pdf, p. 317](../data/pdfs/GS_10K_2025.pdf#page=317)**

- `COMP:GS` · `AUDITED_BY` · `filing-level` · expected source value: `PricewaterhouseCoopers LLP`

```text
                                                                                   /s/ PricewaterhouseCoopers LLP
```

---

### Q09

**Gold: Issaquah, WA**

**Verification:** The statutory cover address is 999 Lake Drive, Issaquah, WA 98027.

**Scope:** Answer uses the printed state abbreviation WA.

**[COST_10K_2026.pdf, p. 1](../data/pdfs/COST_10K_2026.pdf#page=1)**

- `COMP:COST` · `HEADQUARTERED_IN` · `filing-level` · expected source value: `Issaquah, WA`

```text

                                999 Lake Drive, Issaquah, WA 98027
                               (Address of principal executive offices) (Zip Code)
```

---

### Q10

**Gold: Beauty, Grooming, Health Care, Fabric & Home Care, Baby, Feminine & Family Care**

**Verification:** The segment note explicitly enumerates five reportable segments.

**Scope:** Unordered set; Corporate is not a reportable segment. This is one direct relation lookup returning five targets.

**[PG_10K_2026.pdf, p. 82](../data/pdfs/PG_10K_2026.pdf#page=82)**

- `COMP:PG` · `OPERATES_SEGMENT` · `filing-level` · expected source value: `Beauty`
- `COMP:PG` · `OPERATES_SEGMENT` · `filing-level` · expected source value: `Grooming`
- `COMP:PG` · `OPERATES_SEGMENT` · `filing-level` · expected source value: `Health Care`
- `COMP:PG` · `OPERATES_SEGMENT` · `filing-level` · expected source value: `Fabric & Home Care`
- `COMP:PG` · `OPERATES_SEGMENT` · `filing-level` · expected source value: `Baby, Feminine & Family Care`

```text
Under U.S. GAAP, our operating segments are aggregated into five reportable segments: 1) Beauty, 2) Grooming, 3) Health Care,
4) Fabric & Home Care and 5) Baby, Feminine & Family Care. Our five reportable segments are comprised of:
```

---

### Q11

**Gold: 15.084388186%**

**Verification:** 6,721 ÷ 44,556 × 100.

**Scope:** Use consolidated net income of 6,721 million, not parent-attributable net income of 6,704 million.

**[TMO_10K_2025.pdf, p. 62](../data/pdfs/TMO_10K_2025.pdf#page=62)**

- `COMP:TMO` · `METRIC:NET_INCOME` · `FY2025` · expected source value: `6721000000` (raw `6,721`, scale `1,000,000`).
- `COMP:TMO` · `METRIC:REVENUE` · `FY2025` · expected source value: `44556000000` (raw `44,556`, scale `1,000,000`).

```text
(In millions except per share amounts)                                                2025             2024             2023
```

```text
Net income                                                                           6,721              6,338              5,955
```

```text
     Total revenues                                                                  44,556             42,879             42,857
```

---

### Q12

**Gold: 30.798445966%**

**Verification:** 17,678 ÷ 57,399 × 100.

**[ORCL_10K_2026.pdf, p. 116](../data/pdfs/ORCL_10K_2026.pdf#page=116)**

- `COMP:ORCL` · `METRIC:OPERATING_INCOME` · `FY2025` · expected source value: `17678000000` (raw `17,678`, scale `1,000,000`).
- `COMP:ORCL` · `METRIC:REVENUE` · `FY2025` · expected source value: `57399000000` (raw `57,399`, scale `1,000,000`).

```text
                           For the Years Ended May 31, 2026, 2025 and 2024
```

```text
(in millions, except per share data)                                                        2026            2025            2024
```

```text
Operating income                                                                    20,606         17,678         15,353
```

```text
     Total revenues                                                                  67,357         57,399         52,961
```

---

### Q13

**Gold: 26.060961535%**

**Verification:** 13,774 ÷ 52,853 × 100.

**[INTC_10K_2025.pdf, p. 101](../data/pdfs/INTC_10K_2025.pdf#page=101)**

- `COMP:INTC` · `METRIC:RD_EXPENSE` · `FY2025` · expected source value: `13774000000` (raw `13,774`, scale `1,000,000`).
- `COMP:INTC` · `METRIC:REVENUE` · `FY2025` · expected source value: `52853000000` (raw `52,853`, scale `1,000,000`).

```text
Years Ended (In Millions, Except Per Share Amounts)                     Dec 27, 2025   Dec 28, 2024   Dec 30, 2023
```

```text
Research and development                                                        13,774         16,546         16,046
```

```text
Net revenue                                                         $      52,853  $      53,101  $      54,228
```

---

### Q14

**Gold: USD 12,646,000,000**

**Verification:** (16,325 − abs(−3,679)) million.

**Scope:** FY2025 is the statement label and ends February 1, 2026. Excludes noncash capital expenditures of 272 million and acquisition payments.

**[HD_10K_2026.pdf, p. 76](../data/pdfs/HD_10K_2026.pdf#page=76)**

- `COMP:HD` · `METRIC:OPERATING_CASH_FLOW` · `FY2025` · expected source value: `16325000000` (raw `16,325`, scale `1,000,000`).
- `COMP:HD` · `METRIC:CAPEX` · `FY2025` · expected source value: `-3679000000` (raw `(3,679)`, scale `1,000,000`).

```text
in millions                                                                   2025             2024             2023
```

```text
    Net cash provided by operating activities                             16,325         19,810         21,172
```

```text
Capital expenditures                                                        (3,679)         (3,485)         (3,226)
```

---

### Q15

**Gold: 13.049037785%**

**Verification:** (17,682 ÷ 15,641 − 1) × 100.

**[TXN_10K_2025.pdf, p. 41](../data/pdfs/TXN_10K_2025.pdf#page=41)**

- `COMP:TXN` · `METRIC:REVENUE` · `FY2024` · expected source value: `15641000000` (raw `15,641`, scale `1,000,000`).
- `COMP:TXN` · `METRIC:REVENUE` · `FY2025` · expected source value: `17682000000` (raw `17,682`, scale `1,000,000`).

```text
(In millions, except per-share amounts)                                                2025          2024          2023
```

```text
Revenue                                                      $   17,682  $   15,641  $   17,519
```

---

### Q16

**Gold: 1.20077364956 times**

**Verification:** 435,206 ÷ 362,438.

**Scope:** Specifically long-term debt divided by total stockholders’ equity; not total liabilities, regulatory capital or tangible common equity.

**[JPM_10K_2025.pdf, p. 296](../data/pdfs/JPM_10K_2025.pdf#page=296)**

- `COMP:JPM` · `METRIC:LONG_TERM_DEBT` · `FY2025` · expected source value: `435206000000` (raw `435,206`, scale `1,000,000`).
- `COMP:JPM` · `METRIC:SHAREHOLDERS_EQUITY` · `FY2025` · expected source value: `362438000000` (raw `362,438`, scale `1,000,000`).

```text
December 31, (in millions, except share data)                                                                2025          2024
```

```text
Long-term debt (included $134,559 and $100,780 at fair value)                                                   435,206        401,418
```

```text
Total stockholders’ equity                                                                                 362,438        344,758
```

---

### Q17

**Gold: COMP:NVDA**

**Verification:** NVDA: 72880000000 USD; QCOM: 5541000000 USD; AVGO: 23126000000 USD; MU: 8539000000 USD. Maximum: NVDA.

**Scope:** Auditor scope is the supplied filing, not an inferred FY2025 historical auditor relationship. All seven auditor classifications are gold evidence, including excluded companies.

**[NVDA_10K_2026.pdf, p. 86](../data/pdfs/NVDA_10K_2026.pdf#page=86)**

- `COMP:NVDA` · `AUDITED_BY` · `filing-level` · expected source value: `PricewaterhouseCoopers LLP`

```text
/s/PricewaterhouseCoopers LLP
```

**[AMD_10K_2025.pdf, p. 144](../data/pdfs/AMD_10K_2025.pdf#page=144)**

- `COMP:AMD` · `AUDITED_BY` · `filing-level` · expected source value: `Ernst & Young LLP`

```text
/s/ Ernst & Young LLP
```

**[INTC_10K_2025.pdf, p. 99](../data/pdfs/INTC_10K_2025.pdf#page=99)**

- `COMP:INTC` · `AUDITED_BY` · `filing-level` · expected source value: `Ernst & Young LLP`

```text
/s/ Ernst & Young LLP
```

**[QCOM_10K_2026.pdf, p. 93](../data/pdfs/QCOM_10K_2026.pdf#page=93)**

- `COMP:QCOM` · `AUDITED_BY` · `filing-level` · expected source value: `PricewaterhouseCoopers LLP`

```text
/s/ PricewaterhouseCoopers LLP
```

**[AVGO_10K_2025.pdf, p. 84](../data/pdfs/AVGO_10K_2025.pdf#page=84)**

- `COMP:AVGO` · `AUDITED_BY` · `filing-level` · expected source value: `PricewaterhouseCoopers LLP`

```text
/s/ PricewaterhouseCoopers LLP
```

**[TXN_10K_2025.pdf, p. 91](../data/pdfs/TXN_10K_2025.pdf#page=91)**

- `COMP:TXN` · `AUDITED_BY` · `filing-level` · expected source value: `Ernst & Young LLP`

```text
/s/ Ernst & Young LLP
```

**[MU_10K_2026.pdf, p. 162](../data/pdfs/MU_10K_2026.pdf#page=162)**

- `COMP:MU` · `AUDITED_BY` · `filing-level` · expected source value: `PricewaterhouseCoopers LLP`

```text
/s/ PricewaterhouseCoopers LLP
```

**[NVDA_10K_2026.pdf, p. 87](../data/pdfs/NVDA_10K_2026.pdf#page=87)**

- `COMP:NVDA` · `METRIC:NET_INCOME` · `FY2025` · expected source value: `72880000000` (raw `72,880`, scale `1,000,000`).

```text
                                                    (In millions, except per share data)
```

```text
                                                             Jan 25, 2026    Jan 26, 2025    Jan 28, 2024
```

```text
 Net income                                                   $     120,067  $       72,880  $       29,760
```

**[QCOM_10K_2026.pdf, p. 95](../data/pdfs/QCOM_10K_2026.pdf#page=95)**

- `COMP:QCOM` · `METRIC:NET_INCOME` · `FY2025` · expected source value: `5541000000` (raw `5,541`, scale `1,000,000`).

```text
                                                     (In millions, except per share data)
```

```text
                                                                              2026            2025            2024
```

```text
    Net income                                                            $        13,628  $         5,541  $        10,142
```

**[AVGO_10K_2025.pdf, p. 87](../data/pdfs/AVGO_10K_2025.pdf#page=87)**

- `COMP:AVGO` · `METRIC:NET_INCOME` · `FY2025` · expected source value: `23126000000` (raw `23,126`, scale `1,000,000`).

```text
                                                                              2025            2024            2023
```

```text
                                                                                                              (In millions, except per share data)
```

```text
Net income                                                 $     23,126  $      5,895  $     14,082
```

**[MU_10K_2026.pdf, p. 112](../data/pdfs/MU_10K_2026.pdf#page=112)**

- `COMP:MU` · `METRIC:NET_INCOME` · `FY2025` · expected source value: `8539000000` (raw `8,539`, scale `1,000,000`).

```text
(In millions, except per share amounts)
```

```text
For the year ended                                                            2026           2025           2024
```

```text
   Net income                                                           $        84,969 $         8,539 $          778
```

---

### Q18

**Gold: 3.772412666%**

**Verification:** The cover addresses identify COST; 10,383 ÷ 275,235 × 100.

**Scope:** Costco total revenue includes membership fees; net sales alone is not the denominator.

**[COST_10K_2026.pdf, p. 1](../data/pdfs/COST_10K_2026.pdf#page=1)**

- `COMP:COST` · `HEADQUARTERED_IN` · `filing-level` · expected source value: `Issaquah, WA`

```text

                                999 Lake Drive, Issaquah, WA 98027
                               (Address of principal executive offices) (Zip Code)
```

**[HD_10K_2026.pdf, p. 1](../data/pdfs/HD_10K_2026.pdf#page=1)**

- `COMP:HD` · `HEADQUARTERED_IN` · `filing-level` · expected source value: `Atlanta, Georgia`

```text
              2455 Paces Ferry Road
                     Atlanta, Georgia                                                       30339
         (Address of principal executive offices)                                                          (Zip Code)
```

**[TGT_10K_2026.pdf, p. 1](../data/pdfs/TGT_10K_2026.pdf#page=1)**

- `COMP:TGT` · `HEADQUARTERED_IN` · `filing-level` · expected source value: `Minneapolis, Minnesota`

```text
                                                     (State or other jurisdiction of incorporation or organization)
                                                1000 Nicollet Mall, Minneapolis, Minnesota
                                                        (Address of principal executive offices)
```

**[COST_10K_2026.pdf, p. 56](../data/pdfs/COST_10K_2026.pdf#page=56)**

- `COMP:COST` · `METRIC:OPERATING_INCOME` · `FY2025` · expected source value: `10383000000` (raw `10,383`, scale `1,000,000`).
- `COMP:COST` · `METRIC:REVENUE` · `FY2025` · expected source value: `275235000000` (raw `275,235`, scale `1,000,000`).

```text
                            (amounts in millions, except per share data)
```

```text
                                                      2026                2025                2024
```

```text
        Operating income                                          11,685                10,383                 9,285
```

```text
          Total revenue                                           303,154               275,235               254,453
```

---

### Q19

**Gold: Robert M. Davis**

**Verification:** R&D in millions: LLY 13,337; PFE 10,437; MRK 15,789. The maximum is MRK; its executive-officer table identifies Robert M. Davis.

**Scope:** This asks for the CEO as disclosed in the supplied filing, not today’s CEO or an independently inferred FY2025 appointment.

**[LLY_10K_2025.pdf, p. 86](../data/pdfs/LLY_10K_2025.pdf#page=86)**

- `COMP:LLY` · `METRIC:RD_EXPENSE` · `FY2025` · expected source value: `13337000000` (raw `13,337`, scale `1,000,000`).

```text
                                           (Dollars and shares in millions, except per-share data)
```

```text
                                                                             2025            2024            2023
```

```text
  Research and development                                           13,337        10,991         9,313
```

**[PFE_10K_2025.pdf, p. 109](../data/pdfs/PFE_10K_2025.pdf#page=109)**

- `COMP:PFE` · `METRIC:RD_EXPENSE` · `FY2025` · expected source value: `10437000000` (raw `10,437`, scale `1,000,000`).

```text
(MILLIONS, EXCEPT PER SHARE DATA)                                                         2025         2024         2023
```

```text
   Research and development expenses (a)                                                    10,437        10,822        10,679
```

**[MRK_10K_2025.pdf, p. 144](../data/pdfs/MRK_10K_2025.pdf#page=144)**

- `COMP:MRK` · `METRIC:RD_EXPENSE` · `FY2025` · expected source value: `15789000000` (raw `15,789`, scale `1,000,000`).

```text
($ in millions except per share amounts)
```

```text
                                                                                      2025        2024        2023
```

```text
  Research and development                                                                      15,789        17,938        30,531
```

**[MRK_10K_2025.pdf, p. 84](../data/pdfs/MRK_10K_2025.pdf#page=84)**

- `COMP:MRK` · `HAS_CEO` · `filing-level` · expected source value: `Robert M. Davis`

```text
Executive Officers of the Registrant (ages as of February 1, 2026)
```

```text
Robert M. Davis                      59   Chairman, Chief Executive Officer and President (since December 2022); Chief
                                              Executive Officer and President (July 2021-December 2022); Executive Vice
                                                  President, Global Services, and Chief Financial Officer (April 2016-July 2021)
```

---

### Q20

**Gold: COMP:AAPL**

**Verification:** MSFT is audited by Deloitte and is excluded. AAPL: 111,482 − 12,715 = 98,767 million; GOOGL: 164,713 − 91,447 = 73,266 million. Maximum: AAPL.

**Scope:** Use cash expenditure magnitudes; exclude lease principal, acquisitions and supplemental noncash additions. Auditor scope is filing-level.

**[AAPL_10K_2026.pdf, p. 85](../data/pdfs/AAPL_10K_2026.pdf#page=85)**

- `COMP:AAPL` · `AUDITED_BY` · `filing-level` · expected source value: `Ernst & Young LLP`

```text
/s/ Ernst & Young LLP
```

**[MSFT_10K_2026.pdf, p. 138](../data/pdfs/MSFT_10K_2026.pdf#page=138)**

- `COMP:MSFT` · `AUDITED_BY` · `filing-level` · expected source value: `DELOITTE & TOUCHE LLP`

```text
/s/ DELOITTE & TOUCHE LLP
```

**[GOOGL_10K_2025.pdf, p. 83](../data/pdfs/GOOGL_10K_2025.pdf#page=83)**

- `COMP:GOOGL` · `AUDITED_BY` · `filing-level` · expected source value: `Ernst & Young LLP`

```text
/s/ Ernst & Young LLP
```

**[AAPL_10K_2026.pdf, p. 57](../data/pdfs/AAPL_10K_2026.pdf#page=57)**

- `COMP:AAPL` · `METRIC:OPERATING_CASH_FLOW` · `FY2025` · expected source value: `111482000000` (raw `111,482`, scale `1,000,000`).
- `COMP:AAPL` · `METRIC:CAPEX` · `FY2025` · expected source value: `-12715000000` (raw `(12,715)`, scale `1,000,000`).

```text
                                                                     (In millions)
```

```text
                                                                           2026             2025             2024
```

```text
      Cash generated by operating activities                                  145,097          111,482         118,254
```

```text
  Payments for acquisition of property, plant and equipment                           (9,041)          (12,715)           (9,447)
```

**[GOOGL_10K_2025.pdf, p. 90](../data/pdfs/GOOGL_10K_2025.pdf#page=90)**

- `COMP:GOOGL` · `METRIC:OPERATING_CASH_FLOW` · `FY2025` · expected source value: `164713000000` (raw `164,713`, scale `1,000,000`).
- `COMP:GOOGL` · `METRIC:CAPEX` · `FY2025` · expected source value: `-91447000000` (raw `(91,447)`, scale `1,000,000`).

```text
                                                          (in millions)
```

```text
                                                                               2023           2024           2025
```

```text
       Net cash provided by operating activities                          101,746      125,299      164,713
```

```text
Purchases of property and equipment                                        (32,251)       (52,535)       (91,447)
```

---

### Q21

**Gold: USD -45,984,000,000**

**Verification:** (47,941 − 93,925) million = −45,984,000,000 USD.

**Scope:** Use reported net operating revenues for KO and net revenue for PEP; fiscal calendars differ.

**[KO_10K_2025.pdf, p. 113](../data/pdfs/KO_10K_2025.pdf#page=113)**

- `COMP:KO` · `METRIC:REVENUE` · `FY2025` · expected source value: `47941000000` (raw `47,941`, scale `1,000,000`).

```text
                                                  (In millions except per share data)
```

```text
Year Ended December 31,                                                                           2025            2024            2023
```

```text
Net Operating Revenues                                               $      47,941 $      47,061 $      45,754
```

**[PEP_10K_2025.pdf, p. 110](../data/pdfs/PEP_10K_2025.pdf#page=110)**

- `COMP:PEP` · `METRIC:REVENUE` · `FY2025` · expected source value: `93925000000` (raw `93,925`, scale `1,000,000`).

```text
Fiscal years ended December 27, 2025, December 28, 2024 and December 30, 2023
```

```text
(in millions except per share amounts)
```

```text
                                                            2025        2024        2023
```

```text
Net Revenue                                           $   93,925  $   91,854  $   91,471
```

---

### Q22

**Gold: USD 26,539,000,000**

**Verification:** (57,048 − 30,509) million = 26,539,000,000 USD.

**Scope:** Use net income before preferred dividends, not income applicable to common shareholders.

**[JPM_10K_2025.pdf, p. 294](../data/pdfs/JPM_10K_2025.pdf#page=294)**

- `COMP:JPM` · `METRIC:NET_INCOME` · `FY2025` · expected source value: `57048000000` (raw `57,048`, scale `1,000,000`).

```text
Year ended December 31, (in millions, except per share data)                                   2025           2024           2023
```

```text
Net income                                                                $       57,048  $       58,471  $       49,552
```

**[BAC_10K_2025.pdf, p. 186](../data/pdfs/BAC_10K_2025.pdf#page=186)**

- `COMP:BAC` · `METRIC:NET_INCOME` · `FY2025` · expected source value: `30509000000` (raw `30,509`, scale `1,000,000`).

```text
(In millions, except per share information)                                                                2025             2024             2023
```

```text
   Net income                                                                          $         30,509   $         26,973   $         26,305
```

---

### Q23

**Gold: 1.59609442591 times**

**Verification:** 12,914 ÷ 8,091.

**Scope:** A ratio in times, not a percent; use each issuer’s reported FY2025.

**[NVDA_10K_2026.pdf, p. 87](../data/pdfs/NVDA_10K_2026.pdf#page=87)**

- `COMP:NVDA` · `METRIC:RD_EXPENSE` · `FY2025` · expected source value: `12914000000` (raw `12,914`, scale `1,000,000`).

```text
                                                    (In millions, except per share data)
```

```text
                                                             Jan 25, 2026    Jan 26, 2025    Jan 28, 2024
```

```text
      Research and development                                            18,497          12,914           8,675
```

**[AMD_10K_2025.pdf, p. 90](../data/pdfs/AMD_10K_2025.pdf#page=90)**

- `COMP:AMD` · `METRIC:RD_EXPENSE` · `FY2025` · expected source value: `8091000000` (raw `8,091`, scale `1,000,000`).

```text
                                                                       2025               2024               2023
```

```text
                                                                                                      (In millions, except per share amounts)
```

```text
Research and development                                          8,091            6,456            5,872
```

---

### Q24

**Gold: COMP:LLY**

**Verification:** 65,179 million > 62,579 million.

**[LLY_10K_2025.pdf, p. 86](../data/pdfs/LLY_10K_2025.pdf#page=86)**

- `COMP:LLY` · `METRIC:REVENUE` · `FY2025` · expected source value: `65179000000` (raw `65,179`, scale `1,000,000`).

```text
                                           (Dollars and shares in millions, except per-share data)
```

```text
                                                                             2025            2024            2023
```

```text
Revenue                                                  $     65,179  $     45,043  $     34,124
```

**[PFE_10K_2025.pdf, p. 109](../data/pdfs/PFE_10K_2025.pdf#page=109)**

- `COMP:PFE` · `METRIC:REVENUE` · `FY2025` · expected source value: `62579000000` (raw `62,579`, scale `1,000,000`).

```text
(MILLIONS, EXCEPT PER SHARE DATA)                                                         2025         2024         2023
```

```text
Total revenues                                                                             62,579        63,627        59,553
```

---

### Q25

**Gold: USD 23,108,000,000**

**Verification:** (36,443 − 13,335) million = 23,108,000,000 USD.

**Scope:** Issuer-reported FY2025: Walmart year ended January 31, 2025 versus Costco year ended August 31, 2025; not identical calendar windows.

**[WMT_10K_2026.pdf, p. 90](../data/pdfs/WMT_10K_2026.pdf#page=90)**

- `COMP:WMT` · `METRIC:OPERATING_CASH_FLOW` · `FY2025` · expected source value: `36443000000` (raw `36,443`, scale `1,000,000`).

```text
(Amounts in millions)                                                                          2026            2025            2024
```

```text
Net cash provided by operating activities                                                                  41,565           36,443           35,726
```

**[COST_10K_2026.pdf, p. 60](../data/pdfs/COST_10K_2026.pdf#page=60)**

- `COMP:COST` · `METRIC:OPERATING_CASH_FLOW` · `FY2025` · expected source value: `13335000000` (raw `13,335`, scale `1,000,000`).

```text
                                      (amounts in millions)
```

```text
                                                                          2026             2025              2024
```

```text
    Net cash provided by operating activities                                        15,817             13,335              11,339
```

---

### Q26

**Gold: COMP:UNH**

**Verification:** LLY: 65179000000 USD; JNJ: 94193000000 USD; PFE: 62579000000 USD; MRK: 65011000000 USD; ABBV: 61160000000 USD; UNH: 447567000000 USD; TMO: 44556000000 USD. Maximum: UNH.

**Scope:** Revenue totals reflect each issuer’s business model and reported revenue scope; this is a size comparison, not an economic profitability comparison.

**[LLY_10K_2025.pdf, p. 86](../data/pdfs/LLY_10K_2025.pdf#page=86)**

- `COMP:LLY` · `METRIC:REVENUE` · `FY2025` · expected source value: `65179000000` (raw `65,179`, scale `1,000,000`).

```text
                                           (Dollars and shares in millions, except per-share data)
```

```text
                                                                             2025            2024            2023
```

```text
Revenue                                                  $     65,179  $     45,043  $     34,124
```

**[JNJ_10K_2025.pdf, p. 52](../data/pdfs/JNJ_10K_2025.pdf#page=52)**

- `COMP:JNJ` · `METRIC:REVENUE` · `FY2025` · expected source value: `94193000000` (raw `94,193`, scale `1,000,000`).

```text
(Dollars and Shares in Millions Except Per Share Amounts) (Note 1)
```

```text
                                                                                                  2025          2024          2023
```

```text
Sales to customers                                                                         $94,193        88,821        85,159
```

**[PFE_10K_2025.pdf, p. 109](../data/pdfs/PFE_10K_2025.pdf#page=109)**

- `COMP:PFE` · `METRIC:REVENUE` · `FY2025` · expected source value: `62579000000` (raw `62,579`, scale `1,000,000`).

```text
(MILLIONS, EXCEPT PER SHARE DATA)                                                         2025         2024         2023
```

```text
Total revenues                                                                             62,579        63,627        59,553
```

**[MRK_10K_2025.pdf, p. 144](../data/pdfs/MRK_10K_2025.pdf#page=144)**

- `COMP:MRK` · `METRIC:REVENUE` · `FY2025` · expected source value: `65011000000` (raw `65,011`, scale `1,000,000`).

```text
($ in millions except per share amounts)
```

```text
                                                                                      2025        2024        2023
```

```text
Sales                                                                              $    65,011  $    64,168  $    60,115
```

**[ABBV_10K_2025.pdf, p. 96](../data/pdfs/ABBV_10K_2025.pdf#page=96)**

- `COMP:ABBV` · `METRIC:REVENUE` · `FY2025` · expected source value: `61160000000` (raw `61,160`, scale `1,000,000`).

```text
years ended December 31 (in millions, except per share data)                       2025             2024             2023
```

```text
Net revenues                                             $     61,160  $     56,334  $     54,318
```

**[UNH_10K_2025.pdf, p. 73](../data/pdfs/UNH_10K_2025.pdf#page=73)**

- `COMP:UNH` · `METRIC:REVENUE` · `FY2025` · expected source value: `447567000000` (raw `447,567`, scale `1,000,000`).

```text
 (in millions, except per share data)                                                              2025            2024           2023
```

```text
Total revenues                                                                  447,567      400,278      371,622
```

**[TMO_10K_2025.pdf, p. 62](../data/pdfs/TMO_10K_2025.pdf#page=62)**

- `COMP:TMO` · `METRIC:REVENUE` · `FY2025` · expected source value: `44556000000` (raw `44,556`, scale `1,000,000`).

```text
(In millions except per share amounts)                                                2025             2024             2023
```

```text
     Total revenues                                                                  44,556             42,879             42,857
```

---

### Q27

**Gold: COMP:GOOGL, COMP:AAPL, COMP:MSFT**

**Verification:** GOOGL: 132170000000 USD; AAPL: 112010000000 USD; MSFT: 101832000000 USD; AMZN: 77670000000 USD; META: 60458000000 USD; ORCL: 12443000000 USD; CRM: 6197000000 USD. Top three: GOOGL, AAPL, MSFT.

**Scope:** Ranking uses all seven sector companies and issuer fiscal-year labels; ordering is required.

**[AAPL_10K_2026.pdf, p. 52](../data/pdfs/AAPL_10K_2026.pdf#page=52)**

- `COMP:AAPL` · `METRIC:NET_INCOME` · `FY2025` · expected source value: `112010000000` (raw `112,010`, scale `1,000,000`).

```text
                     (In millions, except number of shares, which are reflected in thousands, and per-share amounts)
```

```text
                                                                           2026             2025             2024
```

```text
Net income                                                     $      132,175  $      112,010  $       93,736
```

**[MSFT_10K_2026.pdf, p. 82](../data/pdfs/MSFT_10K_2026.pdf#page=82)**

- `COMP:MSFT` · `METRIC:NET_INCOME` · `FY2025` · expected source value: `101832000000` (raw `101,832`, scale `1,000,000`).

```text
(In millions, except per share amounts)
```

```text
Year Ended June 30,                                                                       2026            2025            2024
```

```text
Net income                                                  $   133,749  $   101,832  $    88,136
```

**[GOOGL_10K_2025.pdf, p. 87](../data/pdfs/GOOGL_10K_2025.pdf#page=87)**

- `COMP:GOOGL` · `METRIC:NET_INCOME` · `FY2025` · expected source value: `132170000000` (raw `132,170`, scale `1,000,000`).

```text
                                          (in millions, except per share amounts)
```

```text
                                                                               2023           2024           2025
```

```text
Net income                                                  $    73,795  $   100,118  $   132,170
```

**[AMZN_10K_2025.pdf, p. 61](../data/pdfs/AMZN_10K_2025.pdf#page=61)**

- `COMP:AMZN` · `METRIC:NET_INCOME` · `FY2025` · expected source value: `77670000000` (raw `77,670`, scale `1,000,000`).

```text
                                                 (in millions, except per share data)
```

```text
                                                                                      2023              2024              2025
```

```text
Net income                                                      $      30,425  $      59,248  $      77,670
```

**[META_10K_2025.pdf, p. 150](../data/pdfs/META_10K_2025.pdf#page=150)**

- `COMP:META` · `METRIC:NET_INCOME` · `FY2025` · expected source value: `60458000000` (raw `60,458`, scale `1,000,000`).

```text
                                                (In millions, except per share amounts)
```

```text
                                                                                    2025               2024               2023
```

```text
Net income                                                    $       60,458  $       62,360  $       39,098
```

**[ORCL_10K_2026.pdf, p. 116](../data/pdfs/ORCL_10K_2026.pdf#page=116)**

- `COMP:ORCL` · `METRIC:NET_INCOME` · `FY2025` · expected source value: `12443000000` (raw `12,443`, scale `1,000,000`).

```text
                           For the Years Ended May 31, 2026, 2025 and 2024
```

```text
(in millions, except per share data)                                                        2026            2025            2024
```

```text
Net income                                                              $     17,087   $     12,443   $     10,467
```

**[CRM_10K_2026.pdf, p. 104](../data/pdfs/CRM_10K_2026.pdf#page=104)**

- `COMP:CRM` · `METRIC:NET_INCOME` · `FY2025` · expected source value: `6197000000` (raw `6,197`, scale `1,000,000`).

```text
                                                       (in millions, except per share data)
```

```text
                                                                                         2026              2025              2024
```

```text
Net income                                                         $        7,457  $        6,197  $        4,136
```

---

### Q28

**Gold: COMP:BAC**

**Verification:** JPM: 20.02 USD/share; BAC: 3.81 USD/share; GS: 51.32 USD/share; MS: 10.21 USD/share; C: 6.99 USD/share; BLK: 35.31 USD/share. Minimum: BAC.

**Scope:** Explicit six-company Financials comparison, not an exhaustive bank-sector claim. WFC’s local PDF omits the incorporated financial statements. EPS per share is affected by share structure; this is not a valuation or profitability recommendation.

**[JPM_10K_2025.pdf, p. 294](../data/pdfs/JPM_10K_2025.pdf#page=294)**

- `COMP:JPM` · `METRIC:EPS_DILUTED` · `FY2025` · expected source value: `20.02` (raw `20.02`, scale `1`).

```text
Year ended December 31, (in millions, except per share data)                                   2025           2024           2023
```

```text
Diluted earnings per share                                                                    20.02            19.75            16.23
```

**[BAC_10K_2025.pdf, p. 186](../data/pdfs/BAC_10K_2025.pdf#page=186)**

- `COMP:BAC` · `METRIC:EPS_DILUTED` · `FY2025` · expected source value: `3.81` (raw `3.81`, scale `1`).

```text
(In millions, except per share information)                                                                2025             2024             2023
```

```text
  Diluted earnings                                                                                               3.81                3.19                3.05
```

**[GS_10K_2025.pdf, p. 318](../data/pdfs/GS_10K_2025.pdf#page=318)**

- `COMP:GS` · `METRIC:EPS_DILUTED` · `FY2025` · expected source value: `51.32` (raw `51.32`, scale `1`).

```text
in millions, except per share amounts                                                                2025      2024      2023
```

```text
Earnings per common share

Basic                                                                                $  51.95  $  41.07  $  23.05

Diluted                                                                               $  51.32  $  40.54  $  22.87
```

**[MS_10K_2025.pdf, p. 208](../data/pdfs/MS_10K_2025.pdf#page=208)**

- `COMP:MS` · `METRIC:EPS_DILUTED` · `FY2025` · expected source value: `10.21` (raw `10.21`, scale `1`).

```text
  in millions, except per share data                                                           2025          2024          2023
```

```text
 Earnings per common share
 Basic                                                                      $         10.32 $          8.04 $          5.24
 Diluted                                                                                      10.21            7.95            5.18
```

**[C_10K_2025.pdf, p. 190](../data/pdfs/C_10K_2025.pdf#page=190)**

- `COMP:C` · `METRIC:EPS_DILUTED` · `FY2025` · expected source value: `6.99` (raw `6.99`, scale `1`).

```text
Diluted earnings per share (4)
Income from continuing operations                                $                  6.99 $                  5.95 $                  4.04
Income (loss) from discontinued operations, net of taxes                 —          —          —
Net income                                                   $                  6.99 $                  5.94 $                  4.04
```

Column/scale context on preceding source page **C_10K_2025.pdf, p. 189** (the EPS fact remains on p. 190):

```text
In millions of dollars, except per share amounts                                           2025                 2024                 2023
```

**[BLK_10K_2025.pdf, p. 117](../data/pdfs/BLK_10K_2025.pdf#page=117)**

- `COMP:BLK` · `METRIC:EPS_DILUTED` · `FY2025` · expected source value: `35.31` (raw `35.31`, scale `1`).

```text
(in millions, except per share data)                                                          2025              2024              2023
```

```text
Earnings per share attributable to BlackRock, Inc. common stockholders:
  Basic                                                                    $          35.83   $          42.45   $          36.85
   Diluted                                                                   $          35.31   $          42.01   $          36.51
```

---

### Q29

**Gold: COMP:AMD, COMP:INTC, COMP:TXN**

**Verification:** The seven signatures classify AMD, INTC and TXN as EY; NVDA, QCOM, AVGO and MU are PwC.

**Scope:** Unordered set. All seven source signatures are included so the sector-wide membership claim is independently checkable.

**[NVDA_10K_2026.pdf, p. 86](../data/pdfs/NVDA_10K_2026.pdf#page=86)**

- `COMP:NVDA` · `AUDITED_BY` · `filing-level` · expected source value: `PricewaterhouseCoopers LLP`

```text
/s/PricewaterhouseCoopers LLP
```

**[AMD_10K_2025.pdf, p. 144](../data/pdfs/AMD_10K_2025.pdf#page=144)**

- `COMP:AMD` · `AUDITED_BY` · `filing-level` · expected source value: `Ernst & Young LLP`

```text
/s/ Ernst & Young LLP
```

**[INTC_10K_2025.pdf, p. 99](../data/pdfs/INTC_10K_2025.pdf#page=99)**

- `COMP:INTC` · `AUDITED_BY` · `filing-level` · expected source value: `Ernst & Young LLP`

```text
/s/ Ernst & Young LLP
```

**[QCOM_10K_2026.pdf, p. 93](../data/pdfs/QCOM_10K_2026.pdf#page=93)**

- `COMP:QCOM` · `AUDITED_BY` · `filing-level` · expected source value: `PricewaterhouseCoopers LLP`

```text
/s/ PricewaterhouseCoopers LLP
```

**[AVGO_10K_2025.pdf, p. 84](../data/pdfs/AVGO_10K_2025.pdf#page=84)**

- `COMP:AVGO` · `AUDITED_BY` · `filing-level` · expected source value: `PricewaterhouseCoopers LLP`

```text
/s/ PricewaterhouseCoopers LLP
```

**[TXN_10K_2025.pdf, p. 91](../data/pdfs/TXN_10K_2025.pdf#page=91)**

- `COMP:TXN` · `AUDITED_BY` · `filing-level` · expected source value: `Ernst & Young LLP`

```text
/s/ Ernst & Young LLP
```

**[MU_10K_2026.pdf, p. 162](../data/pdfs/MU_10K_2026.pdf#page=162)**

- `COMP:MU` · `AUDITED_BY` · `filing-level` · expected source value: `PricewaterhouseCoopers LLP`

```text
/s/ PricewaterhouseCoopers LLP
```

---

### Q30

**Gold: 7 count**

**Verification:** JPM, BAC, GS, MS, WFC, C and BLK each state Delaware: count = 7.

**Scope:** Incorporation jurisdiction, not headquarters location. All seven cover pages provide affirmative evidence.

**[JPM_10K_2025.pdf, p. 1](../data/pdfs/JPM_10K_2025.pdf#page=1)**

- `COMP:JPM` · `INCORPORATED_IN` · `filing-level` · expected source value: `Delaware`

```text

                                         Delaware                                          13-2624428
                                       (State or other jurisdiction of                                         (I.R.S. employer
                                    incorporation or organization)                                   identification no.)

```

**[BAC_10K_2025.pdf, p. 1](../data/pdfs/BAC_10K_2025.pdf#page=1)**

- `COMP:BAC` · `INCORPORATED_IN` · `filing-level` · expected source value: `Delaware`

```text
                                        State or other jurisdiction of incorporation or organization:
                                                           Delaware
                                              IRS Employer Identification No.:
                                                          56-0906609
                                          Address of principal executive offices:
```

**[GS_10K_2025.pdf, p. 1](../data/pdfs/GS_10K_2025.pdf#page=1)**

- `COMP:GS` · `INCORPORATED_IN` · `filing-level` · expected source value: `Delaware`

```text
                                            (Exact name of registrant as specified in its charter)
                     Delaware                                         13-4019460
                       (State or other jurisdiction of                                                      (I.R.S. Employer
                     incorporation or organization)                                                    Identification No.)

```

**[MS_10K_2025.pdf, p. 1](../data/pdfs/MS_10K_2025.pdf#page=1)**

- `COMP:MS` · `INCORPORATED_IN` · `filing-level` · expected source value: `Delaware`

```text

         Delaware                1585 Broadway                 36-3145972                (212) 761-4000
      (State or other jurisdiction of      New York, NY  10036             (I.R.S. Employer Identification No.)     (Registrant’s telephone number,
     incorporation or organization)                                                                                               including area code)
                                      (Address of principal executive offices,
```

**[WFC_10K_2025.pdf, p. 1](../data/pdfs/WFC_10K_2025.pdf#page=1)**

- `COMP:WFC` · `INCORPORATED_IN` · `filing-level` · expected source value: `Delaware`

```text

                        Delaware                                                     No. 41-0449260
       (State or other jurisdiction of incorporation or organization)                                (I.R.S. Employer Identification No.)

                                      333 Market Street, San Francisco, California 94105
```

**[C_10K_2025.pdf, p. 1](../data/pdfs/C_10K_2025.pdf#page=1)**

- `COMP:C` · `INCORPORATED_IN` · `filing-level` · expected source value: `Delaware`

```text

                                    Delaware                                          52-1568099
                     (State or other jurisdiction of incorporation or organization)              (I.R.S. Employer Identification No.)
                       388 Greenwich Street, New York  NY                               10013
                           (Address of principal executive offices)                                  (Zip code)
```

**[BLK_10K_2025.pdf, p. 1](../data/pdfs/BLK_10K_2025.pdf#page=1)**

- `COMP:BLK` · `INCORPORATED_IN` · `filing-level` · expected source value: `Delaware`

```text

                        Delaware                                                 99-1116001
                         (State or Other Jurisdiction of                                                                  (I.R.S. Employer
                       Incorporation or Organization)                                                           Identification No.)
                                    50 Hudson Yards, New York, NY 10001
```

---

## Reproduce the checks

```bash
python scripts/validate_benchmark.py
python -m src.eval.verify_helper MSFT_10K_2026.pdf --page 82
python -m src.eval.verify_helper MRK_10K_2025.pdf --page 84
```

The validator checks the evaluator’s exact Pydantic question schema, source PDF SHA-256/page counts, every quoted substring, every selected year-column token and scale, all numeric arithmetic and entity/ranking selections, canonical IDs/predicates, the 10/10/10 split, and the frozen-rule lock. It blocks graph/coverage/cache reads and network connections. It does not execute query planning, load the graph, or run evaluation.

Machine evidence: `results/benchmark_pdf_evidence.json`. Validation result: `results/benchmark_validation.json`. Final benchmark: `benchmark/questions.json`.

## Human approval

- [ ] Reviewed all 30 questions, source pages, values, scopes, and gold answers.
- [ ] Approved the explicit candidate-classification and strict provenance annotation policy.
- [ ] Approved benchmark for the first live query-planning/evaluation run.

Reviewer: ____________________  Date: ____________________
