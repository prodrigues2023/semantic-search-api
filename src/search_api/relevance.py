"""The Milestone 4 harness: run the golden query set (relevance/golden-set.jsonl)
against a running profile, compute nDCG@10 and recall@10 per query and averaged,
and optionally gate on a regression against relevance/baseline.json.

Also runs the ranking A/B (hybrid vs semantic vs lexical) and the freshness
check named in ROADMAP.md's Milestone 4.
"""
import json
import os
import sys
import time
from pathlib import Path

from .db import SessionLocal
from .embedder import embed
from .metrics import ndcg_at_k, recall_at_k
from .schemas import FilterCondition, Options, Pagination, SearchRequest
from .search import search as run_search

_GOLDEN_SET_PATH = Path(os.environ.get("GOLDEN_SET_PATH", "relevance/golden-set.jsonl"))
_BASELINE_PATH = Path(os.environ.get("BASELINE_PATH", "relevance/baseline.json"))
_RESULTS_DIR = Path(os.environ.get("RESULTS_DIR", "relevance/results"))
_K = 10
# A ranking change may move relevance a little without being a regression;
# this is the tolerance before the harness calls it one.
_REGRESSION_TOLERANCE = 0.02


def load_golden_set() -> list[dict]:
    queries = []
    with _GOLDEN_SET_PATH.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                queries.append(json.loads(line))
    return queries


def run_profile(profile: str) -> dict:
    session = SessionLocal()
    per_query = []
    try:
        for entry in load_golden_set():
            filters = [FilterCondition(**f) for f in entry.get("filters", [])]
            request = SearchRequest(
                query=entry["query"],
                filters=filters,
                pagination=Pagination(limit=_K),
                options=Options(profile=profile),
            )
            response = run_search(session, request)
            ranked_ids = [r.chunkId for r in response.results]
            judgments = {j["chunkId"]: j["grade"] for j in entry["judgments"]}
            per_query.append(
                {
                    "queryId": entry["queryId"],
                    "query": entry["query"],
                    "note": entry["note"],
                    "ndcg": ndcg_at_k(ranked_ids, judgments, _K),
                    "recall": recall_at_k(ranked_ids, judgments, _K),
                }
            )
    finally:
        session.close()

    avg_ndcg = sum(q["ndcg"] for q in per_query) / len(per_query)
    avg_recall = sum(q["recall"] for q in per_query) / len(per_query)
    return {"profile": profile, "queries": per_query, "avgNdcg": avg_ndcg, "avgRecall": avg_recall}


def print_report(report: dict) -> None:
    print(f"\n=== profile: {report['profile']} ===")
    for q in report["queries"]:
        print(f"  {q['queryId']:22s} nDCG@{_K}={q['ndcg']:.3f}  recall@{_K}={q['recall']:.3f}  ({q['note'][:60]})")
    print(f"  {'AVERAGE':22s} nDCG@{_K}={report['avgNdcg']:.3f}  recall@{_K}={report['avgRecall']:.3f}")


def run_ab() -> dict:
    reports = {p: run_profile(p) for p in ("hybrid", "semantic", "lexical")}
    for report in reports.values():
        print_report(report)
    print("\n=== ranking A/B (average nDCG@10) ===")
    for profile, report in reports.items():
        print(f"  {profile:10s} {report['avgNdcg']:.3f}")
    return reports


def check_freshness() -> float:
    """Insert one new chunk and confirm it is findable by an exact-term query
    immediately after. This is a lower bound, not the freshness SLO of a real
    indexing pipeline: the write and the read hit the same synchronous
    Postgres transaction here, with none of the ingest/embed/index latency
    that document-ingestion-pipeline's freshness model accounts for.
    """
    from sqlalchemy import text as sql_text

    session = SessionLocal()
    marker = f"zzqfreshnessmarker{int(time.time())}"
    try:
        started = time.monotonic()
        session.execute(
            sql_text("INSERT INTO documents (id, source_uri) VALUES (:id, :uri)"),
            {"id": "freshness-probe", "uri": "kb/freshness-probe.md"},
        )
        vector = embed(f"the {marker} freshness probe document")
        vec_literal = "[" + ",".join(repr(v) for v in vector) + "]"
        session.execute(
            sql_text(
                """
                INSERT INTO chunks (id, document_id, chunk_index, text, metadata, embedding)
                VALUES (:id, :doc_id, 0, :text, '{}'::jsonb, CAST(:vec AS vector))
                """
            ),
            {
                "id": "freshness-probe:0",
                "doc_id": "freshness-probe",
                "text": f"The {marker} freshness probe document.",
                "vec": vec_literal,
            },
        )
        session.commit()

        request = SearchRequest(query=marker, options=Options(profile="lexical"))
        response = run_search(session, request)
        elapsed = time.monotonic() - started

        found = any(r.chunkId == "freshness-probe:0" for r in response.results)
        if not found:
            raise AssertionError("freshly indexed chunk was not findable")
        print(f"freshness check: found within {elapsed*1000:.1f}ms of insert")
        return elapsed
    finally:
        session.execute(sql_text("DELETE FROM chunks WHERE document_id = 'freshness-probe'"))
        session.execute(sql_text("DELETE FROM documents WHERE id = 'freshness-probe'"))
        session.commit()
        session.close()


def check_regression(profile: str = "hybrid") -> bool:
    report = run_profile(profile)
    print_report(report)

    if not _BASELINE_PATH.exists():
        print(f"\nno baseline at {_BASELINE_PATH}; writing this run as the new baseline")
        _BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
        _BASELINE_PATH.write_text(json.dumps({"avgNdcg": report["avgNdcg"], "avgRecall": report["avgRecall"]}, indent=2))
        return True

    baseline = json.loads(_BASELINE_PATH.read_text())
    ndcg_drop = baseline["avgNdcg"] - report["avgNdcg"]
    recall_drop = baseline["avgRecall"] - report["avgRecall"]

    print(f"\nbaseline nDCG@{_K}={baseline['avgNdcg']:.3f}  recall@{_K}={baseline['avgRecall']:.3f}")
    print(f"current  nDCG@{_K}={report['avgNdcg']:.3f}  recall@{_K}={report['avgRecall']:.3f}")

    regressed = ndcg_drop > _REGRESSION_TOLERANCE or recall_drop > _REGRESSION_TOLERANCE
    if regressed:
        print(f"\nREGRESSION: nDCG dropped {ndcg_drop:.3f}, recall dropped {recall_drop:.3f} (tolerance {_REGRESSION_TOLERANCE})")
    else:
        print("\nno regression beyond tolerance")
    return not regressed


if __name__ == "__main__":
    _RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    cmd = sys.argv[1] if len(sys.argv) > 1 else "report"

    if cmd == "report":
        report = run_profile("hybrid")
        print_report(report)
        (_RESULTS_DIR / f"hybrid-{int(time.time())}.json").write_text(json.dumps(report, indent=2))
    elif cmd == "ab":
        reports = run_ab()
        (_RESULTS_DIR / f"ab-{int(time.time())}.json").write_text(
            json.dumps({p: r for p, r in reports.items()}, indent=2)
        )
    elif cmd == "freshness":
        check_freshness()
    elif cmd == "check":
        ok = check_regression("hybrid")
        sys.exit(0 if ok else 1)
    else:
        print(f"unknown command: {cmd} (expected: report | ab | freshness | check)")
        sys.exit(2)
