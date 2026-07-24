# ADR-0003: Ranking is hybrid — lexical and semantic, fused

- **Status:** Accepted
- **Date:** 2026-07-24

## Context

The default that comes with a vector store is to rank purely by embedding similarity, and it has a
blind spot serious enough to define the ranking design around. Semantic similarity ranks on *meaning*,
which is exactly what you want for "why is my payment failing" matching "declined transaction
troubleshooting" — and exactly what fails for an exact error code, a rare technical term, a proper
noun, or a one-word keyword, where the user was precise and the ranker rewards topical resemblance over
the literal string they typed.

Lexical ranking (BM25-style term matching) is the mirror image: superb at exact terms and identifiers,
weak at meaning. The two signals are strong precisely where the other is weak, which is the textbook
setup for combining them rather than choosing one ([ranking.md](../ranking.md)).

The subtlety is in *how* to combine. Lexical and semantic scores live on different, incomparable scales
— a BM25 score and a cosine similarity are not addends — so naively summing them lets one silently
dominate and makes the blend lurch whenever either scorer's distribution shifts.

Options considered:

1. **Pure semantic.** The store's default; fails the exact-term, identifier, and rare-word queries
   where users are most precise.
2. **Pure lexical.** Fails meaning-based queries — the whole reason semantic search was wanted.
3. **Score-based fusion.** Combine the raw scores. Fragile, because the scales are incomparable and the
   blend depends on unstable score distributions.
4. **Rank-based fusion (e.g. Reciprocal Rank Fusion).** Combine the *positions* in each list, not the
   scores. Needs no normalisation, is stable across scorers, and rewards documents ranked well by
   either or both signals.

## Decision

**Ranking is hybrid: the service retrieves a lexical ranking and a semantic ranking and fuses them by
rank, not by raw score, into one result list.**

- Both signals are always computed; a query carried by exact terms rises on its lexical rank and a
  meaning query rises on its semantic rank, so neither query class is left to the ranker that fails it.
- **Fusion is rank-based** (Reciprocal Rank Fusion as the default), because it needs no score
  normalisation and stays stable when a scorer's distribution changes — unlike adding incomparable
  scores.
- The fused ranking is exposed through a **defined score** ([ADR-0002](./0002-search-is-a-service.md)),
  not the raw fusion value, so callers get a quantity with stated meaning.
- A cross-encoder re-ranker is deliberately deferred to an enhancement justified by measurement
  ([ADR-0005](./0005-relevance-as-slo.md)), not baked into the baseline — hybrid fusion is the robust,
  cheap default.

## Consequences

**Positive**

- Both major query classes work: exact identifiers and rare terms via lexical, meaning via semantic —
  eliminating pure-semantic's most damaging blind spot.
- Rank-based fusion is robust and low-maintenance: no score normalisation to tune, and stability when
  the model or scorer changes, which pairs well with a swappable model.
- It is a strong baseline that keeps the door open to a measured re-ranking upgrade without depending on
  one.

**Negative**

- Running two retrieval paths and fusing them costs more per query — latency and compute — than a single
  semantic lookup.
- Fusion has parameters (the weighting of the two signals, RRF's constant) that need tuning, and tuning
  them well requires the relevance measurement to exist ([ADR-0005](./0005-relevance-as-slo.md)) — so
  the ranking is only as good as the query set behind it.
- Maintaining both a lexical index and a vector index is more operational surface than one, a standing
  cost for the coverage hybrid ranking buys.
