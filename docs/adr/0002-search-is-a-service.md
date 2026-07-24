# ADR-0002: Search is a service with a stable API contract

- **Status:** Accepted
- **Date:** 2026-07-24

## Context

Semantic search is usually born as code embedded in an application or a notebook: the app embeds the
query, calls the vector store directly, and formats the nearest neighbours. It works, and it welds the
application to the embedding model and the store. Swapping the model means touching the app; changing
the store means touching the app; the store's score format leaks into the app's logic. Every internal
improvement becomes an application change, which means improvements stop happening.

The alternative is to make search a service behind a contract: the application sends a query and
receives ranked results, and everything about *how* those results were found — model, store, ranking —
lives behind the contract where it can change freely. This is ordinary service design, applied to
search, and it is what the notebook skipped.

Options considered:

1. **Embedded search — app calls the store directly.** Simplest to start, and it couples the
   application to the model and store, so neither can change without an app change and the store's
   internals leak upward.
2. **A thin passthrough — an endpoint that forwards to the store.** Looks like a service, but if it
   exposes the store's query shape and scores, it is coupling with an HTTP hop — the contract has to
   actually abstract, not just relay.
3. **A service with an abstracting contract.** A defined request (query, filters, pagination) and
   response (ranked results, defined scores, provenance) that hides the model, store, and ranking. The
   application depends on the promise, not the implementation.

## Decision

**Search is a service fronted by a stable API contract that hides the embedding model, the vector
store, and the ranking internals; callers depend on the contract, and those internals can change
without a breaking change.**

- The request carries *what* is wanted — query, filters, pagination, options — and nothing about *how*
  it is found ([api-contract.md](../api-contract.md)).
- The response carries ranked results with **scores of defined semantics** and provenance — never a raw
  store-specific distance, because that would leak the store into the contract.
- The model and store live behind the wall: a better embedding model or a different store
  ([vector-db-benchmark](https://github.com/prodrigues2023/vector-db-benchmark)) is an internal upgrade.
- Because a model change re-embeds the corpus and can shift relevance, the contract's *stability* is
  paired with relevance *measurement* ([ADR-0005](./0005-relevance-as-slo.md)) — the API shape is
  stable even when a model swap moves quality, and the measurement catches the movement.

## Consequences

**Positive**

- The model and store become swappable, so the service can improve continuously without breaking any
  caller — the thing embedded search makes impossible.
- A defined score and provenance make the service usable for real products and for RAG, which need to
  threshold, cite, and debug results.
- One well-defined contract lets many callers share one search service, instead of each re-implementing
  embedded search.

**Negative**

- A contract is a commitment: once products depend on it, its shape is expensive to change, so the
  request/response must be designed with care up front rather than evolved casually.
- Defining score semantics that are stable across model and store changes is genuinely hard — a naive
  score will shift when the model does, so the abstraction takes real thought to hold.
- A service adds an operational surface — deployment, latency, availability — that embedded search did
  not have. The decoupling is worth it, but it is not free.
