"""Validate benchmark schema and raw-PDF evidence without loading the KG or running QA.

Requires the local PDFs and results/benchmark_pdf_evidence.json. This deliberately
imports only the evaluator's question contract; it never calls its run() function.
"""
from __future__ import annotations

from collections import Counter
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path
import re
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def source_only_guard(event: str, args: tuple[Any, ...]) -> None:
    """Fail before reading graph/coverage/cache files or connecting to a provider."""
    if event in {"socket.connect", "sqlite3.connect"}:
        raise RuntimeError("Benchmark verification prohibits network and LLM-cache access")
    if event == "open" and isinstance(args[0], (str, bytes, Path)):
        path = Path(args[0].decode() if isinstance(args[0], bytes) else args[0]).resolve()
        if (
            path.is_relative_to(ROOT / "data/graph")
            or path.is_relative_to(ROOT / ".cache")
            or path == ROOT / "results/metric_coverage.md"
        ):
            raise RuntimeError(f"Benchmark verification prohibits reading {path.name}")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> None:
    sys.addaudithook(source_only_guard)
    import pymupdf
    from config.ontology import CanonicalMetric, RELATION_TYPES
    from src.eval.run_eval import Question  # Contract only; do not invoke run()/ask().
    from src.extract.freeze import verify_rules

    questions_path = ROOT / "benchmark/questions.json"
    questions = json.loads(questions_path.read_text())
    proof = json.loads((ROOT / "results/benchmark_pdf_evidence.json").read_text())
    companies = json.loads((ROOT / "config/companies.json").read_text())
    company_ids = {"COMP:" + c["ticker"] for c in companies}
    facts = proof["facts"]
    counts = Counter(q["type"] for q in questions)
    require(counts == {"single-fact": 10, "multi-hop": 10, "cross-filing": 10}, "Question mix must be 10/10/10")
    require([q["id"] for q in questions] == [f"Q{i:02d}" for i in range(1, 31)], "IDs must be Q01-Q30")
    pages: dict[tuple[str, int], str] = {}
    for filename, source in proof["source_pdfs"].items():
        path = ROOT / "data/pdfs" / filename
        require(hashlib.sha256(path.read_bytes()).hexdigest() == source["sha256"], f"PDF changed: {filename}")
        needed = {f["page_num"] for f in facts.values() if f["doc_id"] == filename}
        needed.update(c["page_num"] for f in facts.values() for c in f.get("context_sources", []) if c["doc_id"] == filename)
        needed.update(c["page_num"] for c in proof.get("corpus_diagnostics", []) if c["doc_id"] == filename)
        with pymupdf.open(path) as doc:
            require(len(doc) == source["pages"], f"Page count changed: {filename}")
            for page in sorted(needed):
                require(1 <= page <= len(doc), f"Invalid physical PDF page: {filename}:{page}")
                pages[filename, page] = doc[page - 1].get_text(sort=True)

    for diagnostic in proof.get("corpus_diagnostics", []):
        for quote in diagnostic["quotes"]:
            require(quote in pages[diagnostic["doc_id"], diagnostic["page_num"]], "Invalid corpus diagnostic quote")

    public_fields = ("doc_id", "page_num", "company_id", "predicate", "period", "expected_value")
    valid_predicates = {"METRIC:" + m.value for m in CanonicalMetric} | set(RELATION_TYPES)
    for key, fact in facts.items():
        require(fact["company_id"] in company_ids, f"Unknown company: {key}")
        require(fact["doc_id"].split("_", 1)[0] == fact["company_id"].removeprefix("COMP:"), f"Company/document mismatch: {key}")
        require(fact["predicate"] in valid_predicates, f"Unknown predicate: {key}")
        require(bool(fact["quotes"]), f"Missing evidence: {key}")
        page_text = pages[fact["doc_id"], fact["page_num"]]
        for quote in fact["quotes"]:
            require(bool(quote) and quote in page_text, f"Quote is not an exact contiguous PDF substring: {key}")
        for context in fact.get("context_sources", []):
            for quote in context["quotes"]:
                require(quote in pages[context["doc_id"], context["page_num"]], f"Invalid continuation context: {key}")
        if fact["predicate"].startswith("METRIC:"):
            raw = fact["value_raw"]
            normalized = Decimal(raw.replace(",", "").replace("(", "-").replace(")", ""))
            require(normalized * fact["scale_multiplier"] == Decimal(fact["expected_value"]), f"Scale/value mismatch: {key}")
            require(fact["period"] in {"FY2024", "FY2025"}, f"Unexpected fiscal period: {key}")
            require(raw in fact["quotes"][-1], f"Raw token absent from quoted row: {key}")
            # Independently locate the table cells following the complete source row label.
            row = fact["quotes"][-1].splitlines()[-1].strip()
            label = fact["raw_label"]
            require(row.startswith(label), f"Row-label mismatch: {key}")
            tokens = re.findall(r"\(?-?\d[\d,]*(?:\.\d+)?\)?|—", row[len(label):])
            years = fact["column_order"]
            require(len(tokens) == len(years), f"Ambiguous table columns: {key}")
            require(tokens[years.index(int(fact["period"][2:]))] == raw, f"Wrong fiscal-year column: {key}")
            context_quotes = [quote for c in fact.get("context_sources", []) for quote in c["quotes"]]
            require(any(all(str(y) in quote for y in years) for quote in fact["quotes"] + context_quotes), f"Missing year-heading evidence: {key}")
            if fact["predicate"] == "METRIC:EPS_DILUTED":
                require(fact["scale_multiplier"] == 1, f"EPS must be unscaled: {key}")
        else:
            require(fact["period"] is None, f"Metadata/qualitative period must be null: {key}")
            require(fact["expected_value"].casefold() in page_text.casefold(), f"Target absent from source page: {key}")

    used = set()
    for question in questions:
        Question.model_validate(question)
        keys = proof["questions"][question["id"]]["evidence_keys"]
        used.update(keys)
        require(question["gold_supporting_facts"] == [{field: facts[key][field] for field in public_fields} for key in keys], f"Gold/source mismatch: {question['id']}")
        if question["type"] == "cross-filing":
            require(all(f["period"] in (None, "FY2025") for f in question["gold_supporting_facts"]), "Cross-filing periods must be FY2025")
        if question["answer_type"] == "numeric":
            require(math.isfinite(question["golden_answer"]), "Nonfinite answer")

    def value(key: str) -> Decimal:
        return Decimal(facts[key]["expected_value"])

    expected_numeric = {
        "Q01": value("MSFT_REV"), "Q02": value("LLY_NI"), "Q03": value("AMD_EPS"),
        "Q04": value("UNH_ASSETS"), "Q06": abs(value("PFE_CAPEX")),
        "Q07": value("MRK_RD"), "Q11": value("TMO_NI") / value("TMO_REV") * 100,
        "Q12": value("ORCL_OP") / value("ORCL_REV") * 100,
        "Q13": value("INTC_RD") / value("INTC_REV") * 100,
        "Q14": value("HD_OCF") - abs(value("HD_CAPEX")),
        "Q15": (value("TXN_REV25") / value("TXN_REV24") - 1) * 100,
        "Q16": value("JPM_DEBT") / value("JPM_EQUITY"),
        "Q18": value("COST_OP") / value("COST_REV") * 100,
        "Q21": value("KO_REV") - value("PEP_REV"), "Q22": value("JPM_NI") - value("BAC_NI"),
        "Q23": value("NVDA_RD") / value("AMD_RD"), "Q25": value("WMT_OCF") - value("COST_OCF"),
        "Q30": Decimal(sum(facts[t + "_INC"]["expected_value"] == "Delaware" for t in ["JPM", "BAC", "GS", "MS", "WFC", "C", "BLK"])),
    }
    for question in questions:
        if question["id"] in expected_numeric:
            require(math.isclose(question["golden_answer"], float(expected_numeric[question["id"]]), rel_tol=1e-12), f"Arithmetic mismatch: {question['id']}")
    semi = ["NVDA", "AMD", "INTC", "QCOM", "AVGO", "TXN", "MU"]
    pwc = [t for t in semi if facts[t + "_AUDIT"]["expected_value"] == "PricewaterhouseCoopers LLP"]
    ey_tech = [t for t in ["AAPL", "MSFT", "GOOGL"] if facts[t + "_AUDIT"]["expected_value"] == "Ernst & Young LLP"]
    health = ["LLY", "JNJ", "PFE", "MRK", "ABBV", "UNH", "TMO"]
    tech = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "ORCL", "CRM"]
    financials_with_eps = ["JPM", "BAC", "GS", "MS", "C", "BLK"]
    rd_winner = max(["LLY", "PFE", "MRK"], key=lambda t: value(t + "_RD"))
    # Recompute selection/ranking before resolving the selected company's relation.
    expected_entities = {
        "Q05": facts["BLK_ACQUIRED"]["company_id"] if facts["BLK_ACQUIRED"]["expected_value"] == "Preqin Holding Limited" else None,
        "Q08": "EXT:PWC" if facts["GS_AUDIT"]["expected_value"] == "PricewaterhouseCoopers LLP" else None,
        "Q09": facts["COST_HQ"]["expected_value"],
        "Q10": [facts[f"PG_SEG{i}"]["expected_value"] for i in range(1, 6)],
        "Q17": "COMP:" + max(pwc, key=lambda t: value(t + "_NI")),
        "Q19": facts[rd_winner + "_CEO"]["expected_value"],
        "Q20": "COMP:" + max(ey_tech, key=lambda t: value(t + "_OCF") - abs(value(t + "_CAPEX"))),
        "Q24": "COMP:" + max(["LLY", "PFE"], key=lambda t: value(t + "_REV")),
        "Q26": "COMP:" + max(health, key=lambda t: value(t + "_REV")),
        "Q27": ["COMP:" + t for t in sorted(tech, key=lambda t: value(t + "_NI"), reverse=True)[:3]],
        "Q28": "COMP:" + min(financials_with_eps, key=lambda t: value(t + "_EPS")),
        "Q29": ["COMP:" + t for t in semi if facts[t + "_AUDIT"]["expected_value"] == "Ernst & Young LLP"],
    }
    require([t for t in ["COST", "HD", "TGT"] if facts[t + "_HQ"]["expected_value"] == "Issaquah, WA"] == ["COST"], "Ambiguous headquarters selection")
    for question in questions:
        if question["id"] in expected_entities:
            require(question["golden_answer"] == expected_entities[question["id"]], f"Entity/ranking mismatch: {question['id']}")
    require(used == set(facts), "Unused or missing evidence records")
    covered = {f["company_id"] for f in facts.values()}
    require(covered == company_ids, "Evidence should span all 35 companies")
    rules_digest = verify_rules(ROOT)
    require(bool(rules_digest), "Active extraction lock missing")
    report = {
        "status": "passed", "review_status": "awaiting human sign-off", "questions": len(questions),
        "question_types": dict(counts), "companies": len(covered), "sectors": len({c["sector"] for c in companies}),
        "unique_evidence_records": len(facts), "supporting_fact_annotations": sum(len(q["gold_supporting_facts"]) for q in questions),
        "source_pages_checked": len(pages), "numeric_answers_recomputed": len(expected_numeric),
        "entity_or_list_answers_recomputed": len(expected_entities),
        "benchmark_sha256": hashlib.sha256(questions_path.read_bytes()).hexdigest(),
        "extraction_rules_digest": rules_digest, "graph_loaded": False, "evaluation_run": False,
        "llm_cache_accessed": False, "network_calls": 0,
    }
    (ROOT / "results/benchmark_validation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
