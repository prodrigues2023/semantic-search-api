from sqlalchemy import text

from .config import CANDIDATE_POOL_MIN, CANDIDATE_POOL_MULTIPLIER
from .cursor import CursorMismatchError, decode_cursor, encode_cursor
from .embedder import embed
from .filters import build_filter_clause
from .ranking import fuse
from .schemas import (
    ResponseDiagnostics,
    ResponsePagination,
    ResultDiagnostics,
    SearchRequest,
    SearchResponse,
    SearchResult,
)


class CursorError(ValueError):
    pass


def _pool_size(limit: int) -> int:
    return max(limit * CANDIDATE_POOL_MULTIPLIER, CANDIDATE_POOL_MIN)


def _run_lexical(session, query: str, filters: list[dict], pool: int):
    where_sql, where_params = build_filter_clause(filters, "lf")
    sql = text(
        f"""
        SELECT c.id, c.document_id, c.chunk_index, c.text, c.metadata,
               ts_rank_cd(c.tsv, plainto_tsquery('english', :q)) AS score
        FROM chunks c
        WHERE c.tsv @@ plainto_tsquery('english', :q) AND {where_sql}
        ORDER BY score DESC, c.id ASC
        LIMIT :pool
        """
    )
    rows = session.execute(sql, {"q": query, "pool": pool, **where_params}).mappings().all()
    return rows


def _run_semantic(session, query: str, filters: list[dict], pool: int):
    where_sql, where_params = build_filter_clause(filters, "sf")
    query_embedding = embed(query)
    sql = text(
        f"""
        SELECT c.id, c.document_id, c.chunk_index, c.text, c.metadata,
               1 - (c.embedding <=> (:qvec)::vector) AS score
        FROM chunks c
        WHERE {where_sql}
        ORDER BY c.embedding <=> (:qvec)::vector ASC, c.id ASC
        LIMIT :pool
        """
    )
    vec_literal = "[" + ",".join(repr(v) for v in query_embedding) + "]"
    rows = session.execute(
        sql, {"qvec": vec_literal, "pool": pool, **where_params}
    ).mappings().all()
    return rows


def search(session, request: SearchRequest) -> SearchResponse:
    filters = [f.model_dump() for f in request.filters]
    profile = request.options.profile
    limit = request.pagination.limit

    try:
        offset = (
            decode_cursor(request.pagination.cursor, request.query, filters, profile)
            if request.pagination.cursor
            else 0
        )
    except CursorMismatchError as exc:
        raise CursorError(str(exc)) from exc

    pool = _pool_size(limit)

    lexical_rows = (
        _run_lexical(session, request.query, filters, pool)
        if profile in ("hybrid", "lexical")
        else []
    )
    semantic_rows = (
        _run_semantic(session, request.query, filters, pool)
        if profile in ("hybrid", "semantic")
        else []
    )

    by_id = {}
    for row in lexical_rows:
        by_id[row["id"]] = row
    for row in semantic_rows:
        by_id.setdefault(row["id"], row)

    lexical_ranked = [row["id"] for row in lexical_rows]
    semantic_ranked = [row["id"] for row in semantic_rows]
    fused = fuse(lexical_ranked, semantic_ranked)

    lexical_score_by_id = {row["id"]: float(row["score"]) for row in lexical_rows}
    semantic_score_by_id = {row["id"]: float(row["score"]) for row in semantic_rows}

    ranked_ids = sorted(
        fused.keys(), key=lambda cid: (-fused[cid]["score"], cid)
    )

    if request.options.minScore is not None:
        ranked_ids = [cid for cid in ranked_ids if fused[cid]["score"] >= request.options.minScore]

    page_ids = ranked_ids[offset : offset + limit]

    results = []
    for cid in page_ids:
        row = by_id[cid]
        entry = fused[cid]
        results.append(
            SearchResult(
                documentId=row["document_id"],
                chunkId=row["id"],
                text=row["text"],
                score=round(entry["score"], 4),
                provenance={
                    "sourceUri": row["metadata"].get("sourceUri", ""),
                    "chunkIndex": row["chunk_index"],
                },
                diagnostics=ResultDiagnostics(
                    lexicalRank=entry["lexicalRank"],
                    semanticRank=entry["semanticRank"],
                    lexicalScore=lexical_score_by_id.get(cid),
                    semanticScore=semantic_score_by_id.get(cid),
                ),
            )
        )

    next_offset = offset + limit
    next_cursor = (
        encode_cursor(next_offset, request.query, filters, profile)
        if next_offset < len(ranked_ids)
        else None
    )

    ran_counts = []
    if profile in ("hybrid", "lexical"):
        ran_counts.append(len(lexical_rows))
    if profile in ("hybrid", "semantic"):
        ran_counts.append(len(semantic_rows))

    filter_excluded_all = bool(filters) and bool(ran_counts) and all(c == 0 for c in ran_counts)

    return SearchResponse(
        results=results,
        pagination=ResponsePagination(nextCursor=next_cursor),
        diagnostics=ResponseDiagnostics(
            filterApplied=bool(filters),
            filterExcludedAll=filter_excluded_all,
            candidatesLexical=len(lexical_rows),
            candidatesSemantic=len(semantic_rows),
        ),
    )
