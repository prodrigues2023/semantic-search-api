# Semantic Search API

> Semantic search is a service with an API contract, not a notebook. A clean query-to-ranked-results
> contract, hybrid ranking that respects exact terms as well as meaning, filtering as part of the
> query, and relevance measured as an SLO. Documented first, provider-neutral, implemented in the
> open.

[![Phase](https://img.shields.io/badge/phase-1%20design-blue)](./ROADMAP.md)
[![ADRs](https://img.shields.io/badge/ADRs-5-green)](./docs/adr)
[![License](https://img.shields.io/badge/license-MIT-lightgrey)](./LICENSE)

Most semantic search starts life as a notebook: embed some documents, embed the query, return the
nearest vectors. It demos well and falls apart as a product. The notebook has no stable contract for
callers, ranks purely on semantic similarity so it fumbles exact matches and rare terms, treats
filtering as an afterthought that quietly breaks the top results, and calls relevance "good" based on
a few queries someone eyeballed.

A search *service* is a different artifact. It has an API contract a product can depend on, ranking
that fuses lexical and semantic signal, filtering that is part of the query and applied without
corrupting the ranking, and relevance defined as a measured objective against a fixed query set. This
repository is the design for that service — the layer above a vector store that a real product calls.

**Português:** [README.pt-BR.md](./README.pt-BR.md)

---

## What is here today

| Area | Status | Link |
| --- | --- | --- |
| Context & scope | Done | [docs/context.md](./docs/context.md) |
| API contract | Done | [docs/api-contract.md](./docs/api-contract.md) |
| Ranking — hybrid and fused | Done | [docs/ranking.md](./docs/ranking.md) |
| Request diagrams | Done | [docs/diagrams](./docs/diagrams) |
| Architecture Decision Records | 5 published | [docs/adr](./docs/adr) |
| Reference implementation | Planned — Phase 3 | [ROADMAP.md](./ROADMAP.md) |

## The idea

**A stable contract in front, hybrid ranking inside, relevance measured — that is what makes search a
service.** Four decisions, each an ADR:

- **Search is a service with a stable API contract** ([ADR-0002](./docs/adr/0002-search-is-a-service.md)).
  A query, filters, and pagination in; ranked results with scores and provenance out. The contract is
  decoupled from the embedding model and vector store behind it, so those can change without breaking
  callers.
- **Ranking is hybrid** ([ADR-0003](./docs/adr/0003-hybrid-ranking.md)). Pure semantic similarity
  misses exact matches, identifiers, and rare terms; pure lexical misses meaning. The service fuses
  both, so "error code E-4021" and "why is my payment failing" both work.
- **Filtering is part of the query** ([ADR-0004](./docs/adr/0004-filtering-in-the-query.md)). A filter
  is applied *with* ranking, not bolted on after — because post-filtering a top-k list silently
  returns fewer, worse results than the caller asked for.
- **Relevance is a measured SLO** ([ADR-0005](./docs/adr/0005-relevance-as-slo.md)). Search quality is
  an objective tracked against a golden query set, not a subjective "seems good" — so a change that
  degrades relevance is caught like any other regression.

## Why documented first

The API contract and the ranking model are the expensive, hard-to-change parts. Once a product depends
on the search contract, its shape is fixed; once relevance is defined, changing the definition
re-baselines every quality claim. The embedding model and the vector store, by contrast, are meant to
be swappable — which is only true if the contract in front of them was designed to hide them. Settling
that boundary on paper is far cheaper than discovering, after launch, that the store leaked into the
API.

## Roadmap

Four phases, tracked as GitHub milestones. See [ROADMAP.md](./ROADMAP.md).

1. **Design** — the API contract, hybrid ranking, filtering, relevance as an SLO, the ADRs
2. **Contracts** — the request/response schema, the filter grammar, the relevance-set format
3. **Reference implementation** — a search service with hybrid ranking and filtering, locally
4. **Relevance** — a golden query set and a harness that catches a ranking regression

## Related

- [vector-db-benchmark](https://github.com/prodrigues2023/vector-db-benchmark) — how the vector store beneath this service is chosen, on a recall-versus-latency curve
- [rag-reference-architecture](https://github.com/prodrigues2023/rag-reference-architecture) — RAG, which calls a retrieval service like this one as its first stage
- [document-ingestion-pipeline](https://github.com/prodrigues2023/document-ingestion-pipeline) — how documents get indexed and kept fresh, which is what this service searches over

## Author

Paulo Roberto Franco Rodrigues — AI Solutions Architect.
Recently designed enterprise AI frameworks and served on an AI architecture committee defining
the engineering standards that bring software discipline to AI delivery.
[LinkedIn](https://linkedin.com/in/paulo-roberto-franco-rodrigues)

## License

MIT — see [LICENSE](./LICENSE).
