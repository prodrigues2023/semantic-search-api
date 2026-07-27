"""nDCG and recall at k (ADR-0005) over a graded golden query set.

Both metrics take the "zero relevant documents" query (docs/relevance-set-format.md's
required blind spot) as a special case: with nothing to find, there is nothing to
miss, so a query with no judged-relevant chunks scores 1.0 rather than 0.0 or NaN --
scoring it 0 would make "the corpus correctly has nothing to say" look like a ranking
failure every time the harness runs.
"""
import math


def _dcg(grades: list[int]) -> float:
    return sum(grade / math.log2(i + 2) for i, grade in enumerate(grades))


def ndcg_at_k(ranked_chunk_ids: list[str], judgments: dict[str, int], k: int) -> float:
    if not judgments:
        return 1.0
    ranked_grades = [judgments.get(cid, 0) for cid in ranked_chunk_ids[:k]]
    ideal_grades = sorted(judgments.values(), reverse=True)[:k]
    ideal_dcg = _dcg(ideal_grades)
    if ideal_dcg == 0:
        return 1.0
    return _dcg(ranked_grades) / ideal_dcg


def recall_at_k(ranked_chunk_ids: list[str], judgments: dict[str, int], k: int) -> float:
    relevant = {cid for cid, grade in judgments.items() if grade > 0}
    if not relevant:
        return 1.0
    retrieved = set(ranked_chunk_ids[:k])
    return len(retrieved & relevant) / len(relevant)
