# Architecture Decision Records

Decisions are numbered, immutable once accepted, and superseded rather than edited.
See [ADR-0001](./0001-record-architecture-decisions.md) for the process itself.

| ADR | Title | Status |
| --- | --- | --- |
| [0001](./0001-record-architecture-decisions.md) | Record architecture decisions in ADRs | Accepted |
| [0002](./0002-search-is-a-service.md) | Search is a service with a stable API contract | Accepted |
| [0003](./0003-hybrid-ranking.md) | Ranking is hybrid — lexical and semantic, fused | Accepted |
| [0004](./0004-filtering-in-the-query.md) | Filtering is part of the query, applied with ranking | Accepted |
| [0005](./0005-relevance-as-slo.md) | Relevance is a measured SLO, not a subjective call | Accepted |
| 0006 | Request/response schema and filter grammar | Planned — Milestone 2 |

## How the accepted decisions fit together

They are the four things that separate a search service from a search notebook:

- **0002** gives it a **contract** — a stable API that hides the model and store, so callers depend on
  the promise, not the implementation.
- **0003** gives it **ranking that works** — lexical and semantic fused, so exact terms and meaning
  both succeed, not just the demo-friendly semantic case.
- **0004** gives it **real filtering** — applied with ranking, so a constrained search returns what the
  caller asked for instead of a silently shrunken list.
- **0005** gives it a **quality bar** — relevance measured against a golden set, so a regression is
  caught with a number instead of noticed by a complaint.

The load-bearing decision is **0002**: the contract is what makes everything else swappable and
therefore evolvable. Ranking can go hybrid (0003), the store can change, the model can improve — all
behind the contract, invisible to callers — precisely because the contract was drawn to hide them. Lose
the contract and every internal change becomes a breaking change.

## Template

```markdown
# ADR-XXXX: Title

- **Status:** Proposed | Accepted | Superseded by ADR-YYYY
- **Date:** YYYY-MM-DD

## Context

The forces at play: the requirement, the constraints, the options considered and why each
was or was not viable.

## Decision

What was decided, in the active voice. What was deliberately deferred.

## Consequences

**Positive** — what this buys.

**Negative** — what it costs, and what you will have to live with. An ADR with no negative
consequences has not been thought through.
```

## Disagreeing with a decision

Open an issue titled `ADR-XXXX: <your objection>`. Experience from running a search service in
production — especially a query class where hybrid ranking helped or hurt — is the most useful kind.
