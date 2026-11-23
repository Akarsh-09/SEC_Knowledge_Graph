"""Evaluate structured graph answers and strict provenance; no PDF retrieval at runtime."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Any, Literal
import httpx
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, model_validator
from src.eval.metrics import aggregate, score_question, TYPES
from src.query.synthesizer import ask
from src.extract.freeze import verify_rules

ROOT=Path(__file__).resolve().parents[2]

SCOPE = '''## Design scope and future improvements

- **Graph completeness:** missing relations do not establish absence. Counts/rankings are over recorded graph evidence; future work needs extraction coverage and completeness certificates before exhaustive claims.
- **Historical audit scope:** auditor metadata is filing-level, without effective-period/audit-period modeling. Historical-year metrics do not independently prove that year's auditor. Add temporal relation scope before historical auditor comparisons.
- **Comparability:** revenue/debt definitions and CAPEX scope differ across issuers. Positive analytical CAPEX fixes signs, not definitions. Reported label differences are surfaced; future work needs definition/scope tags and comparison eligibility rules.
- **Entailment:** normalized quote matching proves original-page textual presence, not that a claimed relationship follows from the quote. Add human sampling, negative examples and semantic checks for live extraction.

## Interpretation

Strict primary fact matching requires exact document/page/company/predicate/period and preserves the original scoring definition (it does not compare expected_value). The separate page +/- 1 diagnostic relaxes only page distance for metrics; relation claims must additionally match the normalized gold expected_value against the retrieved target/value, including on the same page. The diagnostic never replaces primary scoring and can be lower when unrelated same-page relation targets would otherwise match. Duplicate retrieved facts consume precision denominator slots and cannot reuse a gold match. Empty retrieved/gold denominators score zero. Numeric tolerance is 1% relative (1e-12 absolute near zero); ratio/percent conversion requires explicit units. Unordered entity lists use sets; ranking questions preserve order. Entity answers normalize EXT IDs, punctuation and US postal state abbreviations.

Fallback guards cover recognized unsupported constraints and unresolved named qualifiers, not every possible modifier. Offline cache misses use deterministic planning; live failures remain closed unless PLANNER_ALLOW_LIVE_FALLBACK is explicitly enabled. Every prediction records its planner_source. Ingestion audits expose missing coverage and unavailable balance identities rather than inventing values. Run metadata identifies the benchmark, question count and active frozen-rule digest. Query-engine revisions do not change extraction.
'''


def run_metadata(report: dict) -> str:
    count=report.get('question_count',report.get('groups',{}).get('Overall',{}).get('questions',0))
    return '\n'.join([
        '## Run metadata','',f"Benchmark: `{report.get('benchmark','not supplied')}`",
        f"Questions: **{count}**",f"Frozen extraction digest: `{report.get('extraction_rules_digest') or 'unavailable'}`",
        f"Benchmark SHA-256: `{report.get('benchmark_sha256') or 'unavailable'}`",
        'Methodology: exact-page strict primary scoring; separate page +/- 1 diagnostic with relation-target matching.',''])

class GoldFact(BaseModel):
    model_config=ConfigDict(extra='forbid')
    doc_id: str
    page_num: int = Field(ge=1)
    company_id: str
    predicate: str
    period: str | None
    expected_value: str | float | None = None
class Question(BaseModel):
    model_config=ConfigDict(extra='forbid')
    id: str
    type: Literal['single-fact','multi-hop','cross-filing']
    question: str
    answer_type: Literal['numeric','entity','entity_list','boolean']
    golden_answer: Any
    unit: str | None
    gold_supporting_facts: list[GoldFact]
    order_sensitive: bool=False
    @model_validator(mode='after')
    def answer(self):
        from src.query.synthesizer import AnswerContract
        value=self.golden_answer
        if self.answer_type=='numeric' and isinstance(value,(float,int)) and not isinstance(value,bool):value=float(value)
        AnswerContract(structured_answer=value,answer_type=self.answer_type)
        return self

def summary_markdown(report: dict) -> str:
    lines=['# Evaluation summary','',f"Benchmark: `{report['benchmark']}`",'',
        '| Question type | N | Accuracy | Precision macro | Recall macro | Precision micro | Recall micro |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for name,group in report['groups'].items():
        s=group['strict']
        lines.append(f"| {name} | {group['questions']} | {group['accuracy']:.2%} | {s['precision_macro']:.2%} | {s['recall_macro']:.2%} | {s['precision_micro']:.2%} | {s['recall_micro']:.2%} |")
    lines.extend(['','## Secondary page +/- 1 diagnostic','','This never replaces exact-page primary scoring.','',
        '| Question type | Precision macro | Recall macro | Precision micro | Recall micro |','|---|---:|---:|---:|---:|'])
    for name,group in report['groups'].items():
        s=group['page_plus_minus_1']
        lines.append(f"| {name} | {s['precision_macro']:.2%} | {s['recall_macro']:.2%} | {s['precision_micro']:.2%} | {s['recall_micro']:.2%} |")
    lines.extend(['','## Planner sources','', '| Source | Questions |','|---|---:|'])
    lines.extend(f'| {source} | {count} |' for source,count in sorted(report['planner_source_breakdown'].items()))
    return '\n'.join(lines)+'\n\n'+run_metadata(report)+'\n'+SCOPE

def failure_markdown(records: list[dict], report: dict | None=None) -> str:
    lines=['# Failure analysis','']
    groups={
        'Incorrect answers':lambda r:not r['score']['correct'],
        'Abstentions':lambda r:r['prediction']['abstained'],
        'Missing supporting facts':lambda r:bool(r['score']['strict']['missed_facts']),
        'Extra or duplicate supporting facts':lambda r:bool(r['score']['strict']['extra_facts'])}
    for name,predicate in groups.items():
        rows=[r for r in records if predicate(r)]
        lines.extend(['## '+name,'',f'{len(rows)} case(s).',''])
        for r in rows:
            p=r['prediction'];s=r['score']['strict']
            lines.extend([f"### {r['id']} — {r['type']}",'',r['question'],'',
                '```json',json.dumps(dict(gold=r['golden_answer'],predicted=p['structured_answer'],
                    abstention_reason=p.get('reason'),missed_facts=s['missed_facts'],extra_facts=s['extra_facts'],
                    plan=p['plan'],execution_trace=p.get('execution_trace',[])),indent=2),'```',''])
    return '\n'.join(lines)+'\n'+run_metadata(report or {'question_count':len(records)})+'\n'+SCOPE

def run(benchmark: Path, *, offline: bool=False, output_dir: Path | None=None) -> dict:
    raw=json.loads(benchmark.read_text())
    if not isinstance(raw,list) or not raw:raise ValueError('Benchmark must be a nonempty question list; populate the hand-verified benchmark or use questions_sample_3co.json')
    questions=[Question.model_validate(q).model_dump() for q in raw]
    if len({q['id'] for q in questions})!=len(questions):raise ValueError('Duplicate benchmark question IDs')
    rules_digest=verify_rules(ROOT)
    records=[];scores=[]
    for q in questions:
        try:prediction=ask(q['question'],offline=offline)
        except (ValueError, httpx.HTTPError) as error:
            prediction=dict(structured_answer=None,answer_type=q['answer_type'],answer='Evaluation error',unit=None,
                abstained=True,reason=f'{type(error).__name__}: {error}',plan=None,planner_source=None,
                citations=[],retrieved_facts=[],execution_trace=[],comparability_notes=[])
        score=score_question(q,prediction);scores.append(score)
        records.append(dict(id=q['id'],type=q['type'],question=q['question'],golden_answer=q['golden_answer'],
            gold_supporting_facts=q['gold_supporting_facts'],prediction=prediction,score=score,
            matched_facts=score['strict']['matched_facts'],missed_facts=score['strict']['missed_facts'],
            extra_facts=score['strict']['extra_facts'],citations=prediction['citations'],abstention_reason=prediction.get('reason')))
    report=dict(benchmark=str(benchmark),question_count=len(questions),extraction_rules_digest=rules_digest,
                benchmark_sha256=hashlib.sha256(benchmark.read_bytes()).hexdigest(),
                requested_offline=offline,groups=aggregate(scores),
                planner_source_breakdown=dict(Counter(r['prediction'].get('planner_source') or 'evaluation_error' for r in records)),
                abstentions=sum(r['prediction']['abstained'] for r in records),questions=scores)
    output_dir=output_dir or ROOT/'results';output_dir.mkdir(parents=True,exist_ok=True)
    (output_dir/'eval_report.json').write_text(json.dumps(report,indent=2)+'\n')
    (output_dir/'predictions.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in records))
    (output_dir/'eval_summary.md').write_text(summary_markdown(report))
    (output_dir/'failure_analysis.md').write_text(failure_markdown(records,report))
    return report

def main() -> None:
    load_dotenv(ROOT/'.env')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--benchmark',type=Path,default=ROOT/'benchmark/questions.json')
    parser.add_argument('--offline',action='store_true')
    args=parser.parse_args()
    try:report=run(args.benchmark,offline=args.offline)
    except (ValueError,OSError) as error:parser.error(str(error))
    print(json.dumps({k:v for k,v in report.items() if k!='questions'},indent=2))

if __name__=='__main__':main()
