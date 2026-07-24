# Context and scope

## The problem

Semantic search demos are easy and semantic search services are not, and the gap between them is where
most projects get stuck. The demo is a notebook: embed the corpus, embed the query, return the nearest
vectors, marvel at how it understands meaning. It is genuinely impressive and it is not a service. The
moment a product needs to *depend* on it, four things the notebook ignored become the whole job.

First, there is no contract. A product needs a stable interface — a defined request, a defined response
with scores and provenance, pagination, error semantics — that will not change when someone swaps the
embedding model. The notebook has a function signature and a vibe.

Second, pure semantic ranking is subtly bad at things users actually search for. Ask for an exact error
code, a product SKU, a person's name, a rare technical term, and nearest-vector search will happily
return things that are *about* the same topic while missing the exact string the user typed. Meaning is
half the signal; the literal terms are the other half, and a service needs both.

Third, filtering is treated as an afterthought and breaks quietly. "Search these docs, but only from
this tenant, only this document type" — if the filter is applied *after* retrieving the top-k, the
result is fewer and worse hits than the caller asked for, and no error says so. Filtering has to be
part of the query, applied together with ranking.

Fourth, "is it good?" is answered by eyeballing a handful of queries. That is not a quality bar; it is
a mood. A service defines relevance as a measured objective against a fixed query set, so a change that
degrades it is caught the way any regression is.

This repository is the design for crossing that gap: semantic search as a production service with a
contract, hybrid ranking, real filtering, and measured relevance.

## Users

| User | Need |
| --- | --- |
| Product engineer | A stable search API to call, that does not break when the model changes |
| Search / ML engineer | Ranking that handles exact terms and meaning, and relevance they can measure |
| Platform team | A service with latency, freshness, and relevance SLOs, not a notebook in production |
| RAG builder | A retrieval stage with a clean contract to sit in front of generation |

## In scope

- A stable search API contract, decoupled from the model and store
  ([ADR-0002](./adr/0002-search-is-a-service.md))
- Hybrid ranking: lexical and semantic signal fused ([ADR-0003](./adr/0003-hybrid-ranking.md))
- Filtering as part of the query, applied with ranking
  ([ADR-0004](./adr/0004-filtering-in-the-query.md))
- Relevance as a measured SLO against a golden query set
  ([ADR-0005](./adr/0005-relevance-as-slo.md))
- The operational concerns a service has and a notebook does not: latency budget, index freshness

## Explicitly out of scope

Deliberate exclusions:

- **Choosing the vector store.** Which store backs the service is decided on a recall-versus-latency
  curve by the [vector-db-benchmark](https://github.com/prodrigues2023/vector-db-benchmark); this
  service sits above whatever store that choice lands on.
- **Choosing the embedding model.** The model is behind the contract and swappable
  ([ADR-0002](./adr/0002-search-is-a-service.md)); selecting it is a separate decision this service is
  designed to be independent of.
- **Indexing and freshness plumbing.** Turning documents into an index and keeping it current is the
  [document-ingestion-pipeline](https://github.com/prodrigues2023/document-ingestion-pipeline)'s
  subject; this service searches what that pipeline produced.
- **Generation.** Turning search results into an answer is RAG, the
  [rag-reference-architecture](https://github.com/prodrigues2023/rag-reference-architecture)'s subject.
  This service is the retrieval stage, not the generation stage.
- **A UI.** Search boxes, result rendering, and autocomplete are a client concern; this is the API
  behind them.

## Key constraints

1. **A stable contract in front.** Callers depend on a defined request/response, unaffected by changes
   to the model or store behind it — see [ADR-0002](./adr/0002-search-is-a-service.md).
2. **Hybrid ranking.** Lexical and semantic signal are fused, so exact terms and meaning both work —
   see [ADR-0003](./adr/0003-hybrid-ranking.md).
3. **Filtering in the query.** Filters are applied with ranking, never as a post-filter that shrinks
   the result set silently — see [ADR-0004](./adr/0004-filtering-in-the-query.md).
4. **Relevance is measured.** Quality is an SLO tracked against a golden query set, not a subjective
   impression — see [ADR-0005](./adr/0005-relevance-as-slo.md).
5. **Provider-neutral.** The design names no specific model or store; both live behind the contract.

## Related documents

- [API contract](./api-contract.md) — the request, the response, scores, and provenance
- [Ranking](./ranking.md) — why hybrid, and how the two rankings are fused
- [Diagrams](./diagrams) — the request path and the fusion of rankings
- [ADRs](./adr) — the decisions and their reasoning
