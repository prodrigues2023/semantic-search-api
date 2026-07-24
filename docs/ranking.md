# Ranking — hybrid and fused

The single most consequential internal decision in a search service is how it ranks, and the notebook's
answer — pure semantic similarity — is wrong often enough to matter. This document is why ranking is
hybrid and how the two signals combine ([ADR-0003](./adr/0003-hybrid-ranking.md)).

## Why pure semantic ranking fails

Semantic (vector) search ranks by similarity of *meaning*. That is powerful and it has a blind spot: it
does not privilege the *literal terms* the user typed. In practice this fails on exactly the queries
where the user was most precise:

| Query kind | Example | What pure-semantic does |
| --- | --- | --- |
| Exact identifier | `error code E-4021` | Returns docs about errors generally; may miss the one containing the exact code |
| Rare / technical term | `idempotency key collision` | Dilutes the rare term into its general topic |
| Proper noun | `the Henderson contract` | Ranks on "contract" semantics, loses the specific name |
| Short keyword | `refund` | Little semantic signal in one word; lexical would nail it |

The mirror image is also true: pure *lexical* search (exact term matching, BM25) nails those cases and
fails at meaning — "why is my payment failing" will not match a document titled "declined transaction
troubleshooting" because they share few words. **Each signal is strong exactly where the other is
weak.** That is the whole argument for fusing them.

## How the two are fused

The service retrieves two ranked lists — one lexical, one semantic — and combines them into one. The
key design choice is *how* to combine, and the robust answer is **rank-based fusion** rather than
score-based:

- **Score-based fusion** (add the two scores) is fragile: lexical scores (BM25) and semantic scores
  (cosine) are on different, incomparable scales, so adding them lets one signal silently dominate, and
  the blend shifts whenever either scorer's distribution changes.
- **Rank-based fusion** (e.g. Reciprocal Rank Fusion) combines the *positions* in each list, not the
  raw scores. A document ranked highly by either signal rises; one ranked highly by both rises most.
  It needs no score normalisation and is stable across scorers — which is why it is the default here.

The result is a single ranked list where an exact-identifier query is carried by its lexical rank, a
meaning query is carried by its semantic rank, and a query that is both gets the best of each.

## Scores the caller can use

Fusion produces an internal ranking; the contract exposes a *score with stated semantics*
([api-contract.md](./api-contract.md)), not the raw fusion number. The service commits to what the
score means — its range, whether it is comparable across queries, what a threshold implies — because a
caller that thresholds or displays confidence needs a defined quantity, not a leaked internal. The
optional diagnostics can expose each signal's contribution, so ranking is explainable rather than
magic.

## Re-ranking, deliberately deferred

A cross-encoder re-ranker over the fused top-k can lift relevance further, at a latency and cost price.
It is deliberately **not** in the baseline: hybrid fusion is the robust default that fixes the
pure-semantic blind spot cheaply, and re-ranking is an enhancement to weigh against its cost once
relevance is *measured* ([ADR-0005](./adr/0005-relevance-as-slo.md)) — you add a re-ranker because the
golden set shows it helps, not on faith. This mirrors the layered retrieval in the
[rag-reference-architecture](https://github.com/prodrigues2023/rag-reference-architecture).

## The rule

> Rank on meaning **and** terms, fused by rank not raw score, exposed as a defined score, and improved
> only by what the relevance measurement justifies. Pure semantic similarity is a demo default, not a
> ranking strategy.
