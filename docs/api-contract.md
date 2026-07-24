# The API contract

The contract is what makes search a service instead of a function call. It is the promise a product
depends on, and — crucially — it is drawn so that the embedding model and vector store behind it can
change without any caller noticing ([ADR-0002](./adr/0002-search-is-a-service.md)). This document
describes the shape of that promise; the exact schema is [Milestone 2](../ROADMAP.md).

## The request

A search request carries four things, no more:

| Part | What it is | Why it is in the contract |
| --- | --- | --- |
| **Query** | The user's search text | The thing being searched for |
| **Filters** | Constraints on which documents are eligible | Part of the query, not applied afterward ([ADR-0004](./adr/0004-filtering-in-the-query.md)) |
| **Pagination** | Page size and a stable cursor | A service returns results in pages; a notebook returns a list |
| **Options** | e.g. ranking profile, minimum score | Explicit knobs, so behaviour is chosen by the caller, not hidden |

Notably **absent** from the request: anything about the embedding model, the vector store, the index,
or the ranking internals. The caller says *what* it wants, never *how* the service finds it. That
absence is the decoupling ([ADR-0002](./adr/0002-search-is-a-service.md)) — the "how" can change freely
because it was never in the contract.

## The response

A response is a ranked list of results plus the metadata a caller needs to reason about them:

| Part | What it is | Why a caller needs it |
| --- | --- | --- |
| **Ranked results** | Documents in relevance order | The core output |
| **Score** | A relevance score per result | Lets a caller threshold, compare, and display confidence |
| **Provenance** | Which document, which chunk, where from | Lets a caller cite, link, and debug — essential for RAG |
| **Pagination cursor** | How to get the next page | Stable paging over a possibly-changing index |
| **Diagnostics** | Optional: why this ranked here (lexical vs semantic contribution) | Makes ranking explainable, not magic |

**Scores are part of the contract and must be reasoned-about, not raw.** A caller needs to know whether
a score of 0.7 is good, whether scores are comparable across queries, and what a threshold means.
Leaking a raw cosine distance or a store-specific score breaks the decoupling and confuses callers;
the service defines a score with stated semantics ([ranking.md](./ranking.md)).

## What the contract hides, deliberately

The contract is a wall, and these live behind it:

- **The embedding model.** Swappable — a better model is an internal upgrade, not an API change. (A
  model change *does* re-embed the corpus and can shift relevance, which is why relevance is measured;
  see [ADR-0005](./adr/0005-relevance-as-slo.md).)
- **The vector store.** Chosen and re-chosen on its own merits
  ([vector-db-benchmark](https://github.com/prodrigues2023/vector-db-benchmark)) without touching the
  API.
- **The ranking internals.** How lexical and semantic are fused ([ranking.md](./ranking.md)) can be
  tuned freely; the caller sees a ranked list with scores either way.

## Error and edge semantics

A service defines what a notebook leaves undefined:

- **Empty results** are a valid, successful response — not an error. A query with no matches, or a
  filter that excludes everything, returns an empty ranked list, so the caller can distinguish "nothing
  matched" from "something broke".
- **A filter that removes all candidates** is reported as such in diagnostics, so a caller is not left
  guessing whether the query or the filter emptied the results ([ADR-0004](./adr/0004-filtering-in-the-query.md)).
- **Pagination is stable enough to page through** even as the index changes underneath, within stated
  limits — a cursor, not an offset that shifts as documents are added.
