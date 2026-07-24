# ADR-0001: Record architecture decisions in ADRs

- **Status:** Accepted
- **Date:** 2026-07-24

## Context

The decisions that turn a search notebook into a service — draw a contract that hides the store, fuse
two rankings, apply filters with ranking, measure relevance — are exactly the ones a fast follow-up
will want to shortcut. "Just return the raw store score", "just post-filter, it's simpler", "it looks
fine, ship it" are all locally easier and each quietly undoes a decision that was made for a reason. If
the reason lives only in the code, the shortcut looks free.

Recording the decisions with their reasoning is what makes the cost of the shortcut visible to the
person tempted by it.

## Decision

**Record every architecturally significant decision as a numbered ADR**, using the format in
[the index](./README.md): Context, Decision, Consequences — with the negative consequences stated as
plainly as the positive.

- An ADR is immutable once accepted; a changed decision is a new ADR that supersedes the old.
- The service's defining choices — the contract boundary, hybrid ranking, filtering-in-the-query,
  relevance-as-SLO — are ADRs because they are the ones a simplification would erode.

## Consequences

**Positive**

- A reader sees why the service is built the way it is, and can challenge the reasoning rather than just
  the result.
- The record makes the cost of a tempting shortcut explicit, defending the service's quality over time.

**Negative**

- The discipline has a cost, and skipping an ADR for a "small" choice is how the record grows gaps.
- A recorded decision can be treated as settled after the trade-offs behind it have shifted; superseding
  keeps it honest, but only if someone does it.
