# ADR-0005: Relevance is a measured SLO, not a subjective call

- **Status:** Accepted
- **Date:** 2026-07-24

## Context

"Is the search good?" is the question that decides whether a search service is succeeding, and it is
almost always answered badly — by typing a few queries, eyeballing the results, and declaring victory.
That approach cannot tell you whether a change helped or hurt, cannot catch a regression, and cannot
settle a disagreement about two ranking configurations. It is a mood, not a measurement, and it means
the most important property of the service is the one nobody is actually tracking.

Every other property of the service is measured — latency has percentiles, availability has an SLO —
but relevance, the reason the service exists, is left to impression. That asymmetry is the gap this
decision closes. Relevance can be measured, with a fixed set of queries and judged results and standard
information-retrieval metrics, and once it is, a ranking change becomes a testable hypothesis instead of
a matter of taste.

This is the same discipline the [rag-evaluation-toolkit](https://github.com/prodrigues2023/rag-evaluation-toolkit)
brings to end-to-end RAG, applied one layer down to retrieval relevance specifically.

## Decision

**Search relevance is a measured SLO: quality is defined by information-retrieval metrics computed over
a golden query set, tracked over time, and used to gate ranking changes — not judged subjectively.**

- **A golden query set** of representative queries with judged relevant results is the ground truth
  ([Milestone 4](../../ROADMAP.md)). Without it, "relevance" has nothing to measure against.
- **Standard metrics** — nDCG and recall at k — turn the judged set into numbers, so relevance has a
  value, a trend, and a target, like any other SLO.
- **A ranking change is gated by the measurement.** A change to fusion weights, a new re-ranker
  ([ADR-0003](./0003-hybrid-ranking.md)), a model swap ([ADR-0002](./0002-search-is-a-service.md)) — each
  is run against the golden set and must not regress relevance to ship. This is what makes a model swap
  behind the stable contract safe: the contract holds the shape, the measurement holds the quality.
- **The set is maintained**, because a golden set that drifts from real queries measures the wrong
  thing — the same lesson the evaluation toolkit teaches about golden datasets generally.

## Consequences

**Positive**

- Relevance becomes an engineering quantity: a change is a hypothesis the golden set confirms or
  refutes, so ranking improves deliberately instead of by anecdote.
- Regressions are caught before shipping — a fusion tweak or model swap that quietly degrades relevance
  is stopped by a number, not discovered by a user complaint.
- It makes the swappable model of [ADR-0002](./0002-search-is-a-service.md) safe: you can change the
  model behind the contract *because* the measurement catches any relevance movement it causes.

**Negative**

- Building and judging a golden query set is real, expensive, and expertise-dependent work, and the
  quality of every relevance number rests on it — a weak or biased set gives confident, wrong answers.
- The metrics measure relevance against *judged* results, which can diverge from real user satisfaction;
  nDCG on a golden set is a proxy, and treating the proxy as the whole truth has its own failure mode.
- A golden set decays as the corpus and query patterns change, so the measurement carries an ongoing
  maintenance cost — an unmaintained set gives a green light while real relevance drifts underneath it.
