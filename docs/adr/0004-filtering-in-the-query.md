# ADR-0004: Filtering is part of the query, applied with ranking

- **Status:** Accepted
- **Date:** 2026-07-24

## Context

Real search is almost always constrained: search within this tenant, only this document type, only
records from this date range, only what this user is allowed to see. How those filters are applied,
relative to ranking, is a decision that looks like plumbing and quietly determines whether results are
correct.

The tempting-but-wrong approach is **post-filtering**: retrieve the top-k by relevance, then drop the
ones that fail the filter. It is easy to bolt onto a ranker that does not natively filter, and it is
subtly broken. If you retrieve the top 10 and 7 fail the filter, you return 3 — fewer than asked, and
you have no idea whether better matches existed just past position 10 that would have passed. The
result set is silently smaller and worse, with no error to signal it. For an access-control filter, it
is worse than wrong: it is a correctness-and-security problem wearing a relevance costume.

The correct approach is to make the filter part of the query, applied *together with* ranking, so the
top-k is computed over the eligible set — the k best results *that satisfy the filter*, which is what
the caller actually asked for.

Options considered:

1. **Post-filter the ranked results.** Simple to add, silently returns fewer and worse results, and
   cannot guarantee k results even when k eligible documents exist.
2. **Pre-filter then rank the subset.** Correct in result, but a naive implementation scans the whole
   eligible set, which does not scale for a broad filter over a large corpus.
3. **Filter integrated with retrieval.** The store/index applies the filter during the search so the
   top-k is drawn from the eligible set directly — correct and efficient, and the mode a capable vector
   store supports natively.

## Decision

**A filter is part of the query, applied together with ranking so the returned top-k is the k best
results that satisfy the filter — never a post-filter over an already-ranked list.**

- Filters are declared in the request ([api-contract.md](../api-contract.md)) and applied during
  retrieval, so ranking operates over the eligible set and the caller reliably gets up to k eligible
  results.
- **Access-control filters are treated as correctness, not relevance.** A permission filter is applied
  as a hard constraint during retrieval, never as a post-hoc drop that could leak how many results were
  removed or fail to return allowed matches ranked past the cutoff.
- **An empty or reduced result from filtering is reported in diagnostics**
  ([api-contract.md](../api-contract.md)), so a caller can tell "the filter excluded everything" from
  "the query matched nothing" — two very different situations a bare empty list conflates.
- The efficiency of filtered retrieval depends on the store; benchmarking filtered search is explicitly
  part of choosing it ([vector-db-benchmark](https://github.com/prodrigues2023/vector-db-benchmark)).

## Consequences

**Positive**

- The caller gets what it asked for: the best results that satisfy the filter, up to k, instead of a
  silently truncated list.
- Access-control filters become correct and safe, applied as hard constraints during retrieval rather
  than as a leaky afterthought.
- Diagnostics on an empty filtered result remove a whole class of "why did I get nothing" confusion.

**Negative**

- Correct filtered retrieval depends on the store supporting it well; a store with weak filtered-search
  performance forces a hard trade between correctness and latency that the service inherits.
- A highly selective filter over a large corpus can be expensive to evaluate during retrieval, and a
  filter grammar rich enough to be useful is more to specify, validate, and optimise
  ([Milestone 2](../../ROADMAP.md)).
- Integrating filters with ranking couples the service more tightly to the store's filtering
  capabilities, slightly narrowing the "any store behind the contract" ideal of
  [ADR-0002](./0002-search-is-a-service.md).
