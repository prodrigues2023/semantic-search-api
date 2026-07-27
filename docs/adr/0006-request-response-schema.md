# ADR-0006: Request/response schema and filter grammar

- **Status:** Accepted
- **Date:** 2026-07-27

## Context

[ADR-0002](./0002-search-is-a-service.md) decided the contract carries query, filters, pagination,
and options in, and a ranked list with defined scores and provenance out — but named the shape
without fixing the fields, the filter operators, or what a score actually means numerically. Two
teams building a client and a service independently need the exact schema, not the intent behind
it; that is the gap [Milestone 2](../../ROADMAP.md) exists to close.

Three sub-decisions carry real weight:

1. **How rich is the filter grammar?** Rich enough to be useful, cheap enough to specify and
   optimize ([ADR-0004](./0004-filtering-in-the-query.md) already named this tension).
2. **What does a score mean?** [ADR-0003](./0003-hybrid-ranking.md)'s fused rank produces a number;
   the contract must state what that number promises and — as important — what it does not.
3. **How does pagination stay stable** over an index that keeps changing underneath it?

## Decision

**The request and response below are the contract. The filter grammar is deliberately small:
equality, set membership, and range, composed by AND only — no OR, no NOT, no nested groups.**

### Request

```json
{
  "query": "why is my payment failing",
  "filters": [
    { "field": "category", "op": "eq", "value": "billing" },
    { "field": "status", "op": "in", "value": ["open", "pending"] },
    { "field": "created_at", "op": "gte", "value": "2026-01-01T00:00:00Z" }
  ],
  "pagination": { "cursor": null, "limit": 10 },
  "options": { "profile": "hybrid", "min_score": null }
}
```

- **`filters`** is a flat list, ANDed together. Operators: `eq`, `in`, `gte`, `lte`. No `or`, `not`,
  or nesting — a real scope cut ([Milestone 2](../../ROADMAP.md)'s roadmap already flagged the
  richness/cost tension), documented in [filter-grammar.md](../filter-grammar.md).
- **`options.profile`** selects `hybrid` (default), `semantic`, or `lexical` — the one dial the
  caller has into ranking internals, useful for the A/B comparison
  [ADR-0005](./0005-relevance-as-slo.md) requires, without exposing fusion parameters themselves.
- **`pagination.cursor`** is opaque (never an offset the caller constructs) and is bound to the
  exact query, filters, and profile that produced it — see below.

### Response

```json
{
  "results": [
    {
      "documentId": "doc-042",
      "chunkId": "doc-042:3",
      "text": "...declined transactions are retried automatically for up to...",
      "score": 0.83,
      "provenance": { "sourceUri": "kb/billing/retries.md", "chunkIndex": 3 },
      "diagnostics": { "lexicalRank": 2, "semanticRank": 11, "lexicalScore": 4.1, "semanticScore": 0.71 }
    }
  ],
  "pagination": { "nextCursor": "eyJvIjoxMCwicSI6ImE3ZjMifQ==" },
  "diagnostics": { "filterApplied": true, "filterExcludedAll": false, "candidatesLexical": 214, "candidatesSemantic": 500 }
}
```

- **`score` is a fused-rank-derived quantity in `(0, 1]`**, monotonically decreasing with rank
  within *this response*. It is explicitly **not** a probability and **not comparable across
  different queries or different filters** — Reciprocal Rank Fusion's score depends on what else
  was retrieved for *this* query, so "0.83 here" and "0.83 there" answer different questions. A
  caller may threshold and compare *within* one result set; comparing across queries is a misuse
  the contract calls out rather than silently permits.
- **`diagnostics.lexicalRank`/`semanticRank`** are per-result: which position this result held in
  each underlying ranking before fusion, `null` if it did not appear in that ranking at all —
  exactly the "why did this rank here" explainability [ranking.md](../ranking.md) promises.
- **Top-level `diagnostics`** answers the question [ADR-0004](./0004-filtering-in-the-query.md)
  raised: `filterExcludedAll: true` distinguishes "the filter excluded everything" from "the query
  matched nothing" — both would otherwise look like an empty `results` list.
- **`pagination.nextCursor`** is opaque and encodes the offset plus a hash of the exact query,
  filters, and profile that produced it. A request with a cursor whose hash does not match its own
  query/filters/profile is a client error (`400`), not a silent restart — paging must mean "the
  next page of *this* search," never "the next page of whatever this cursor happens to decode to."

## Consequences

**Positive**

- A client and a service can be built independently against this document and interoperate on the
  first try — [Milestone 2](../../ROADMAP.md)'s exit criterion, met by specification rather than
  by both sides guessing the same way.
- The deliberately small filter grammar (AND of `eq`/`in`/`gte`/`lte`) covers the large majority of
  real constrained-search needs — tenant, category, status, date range — without the
  specification, validation, and query-planning cost of a general boolean expression language.
- Naming the score's real semantics (fused-rank-derived, not cross-query-comparable) prevents the
  single most common contract misuse: a caller silently treating scores as an absolute relevance
  probability and building a global threshold that breaks the moment the query mix shifts.

**Negative**

- **No OR, NOT, or nested filter groups is a real capability gap.** "Category A or category B"
  cannot be expressed as one request; a caller needing it must issue multiple searches and merge —
  extra work pushed to every client that needs it, in exchange for a grammar cheap to specify,
  validate, and optimize against the store today.
- **The score's cross-query incomparability is easy to forget and expensive to get wrong.** A
  product that stores scores and compares them across sessions or users has quietly reintroduced
  the exact misuse this ADR warns against; the contract can document the rule, not enforce it.
- **A cursor bound to the exact query is inflexible on purpose** — changing so much as a filter
  value invalidates it. That is deliberate (a cursor for a different query would page through the
  wrong result set), but it means no "keep paging while I refine my filters" UX without restarting
  from page one.
