"""Reciprocal Rank Fusion (docs/ranking.md, ADR-0003).

Combines ranked-position lists, not raw scores, so lexical (ts_rank_cd) and
semantic (cosine) signals -- on incomparable scales -- never have to be
normalised against each other.
"""
from .config import RRF_K


def fuse(lexical_ranked: list[str], semantic_ranked: list[str]) -> dict[str, dict]:
    """Return {chunk_id: {"fused": float, "lexicalRank": int|None, "semanticRank": int|None}}.

    Ranks are 1-based. A chunk absent from a list contributes nothing from
    that list -- it is not penalised beyond simply not gaining that list's
    boost.
    """
    fused: dict[str, dict] = {}

    lists_used = 0
    if lexical_ranked:
        lists_used += 1
    if semantic_ranked:
        lists_used += 1

    for rank, chunk_id in enumerate(lexical_ranked, start=1):
        entry = fused.setdefault(
            chunk_id, {"fused": 0.0, "lexicalRank": None, "semanticRank": None}
        )
        entry["fused"] += 1.0 / (RRF_K + rank)
        entry["lexicalRank"] = rank

    for rank, chunk_id in enumerate(semantic_ranked, start=1):
        entry = fused.setdefault(
            chunk_id, {"fused": 0.0, "lexicalRank": None, "semanticRank": None}
        )
        entry["fused"] += 1.0 / (RRF_K + rank)
        entry["semanticRank"] = rank

    # Normalise into (0, 1]: the maximum possible fused value is a chunk
    # ranked #1 in every list that actually ran.
    max_possible = lists_used * (1.0 / (RRF_K + 1)) if lists_used else 1.0
    for entry in fused.values():
        entry["score"] = min(entry["fused"] / max_possible, 1.0) if max_possible else 0.0

    return fused
