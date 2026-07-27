# Semantic Search API

> Semantic search is a service with an API contract, not a notebook. A clean query-to-ranked-results
> contract, hybrid ranking that respects exact terms as well as meaning, filtering as part of the
> query, and relevance measured as an SLO. Documented first, provider-neutral, implemented in the
> open.

[![Phase](https://img.shields.io/badge/phase-4%20relevance-blue)](./ROADMAP.md)
[![ADRs](https://img.shields.io/badge/ADRs-6-green)](./docs/adr)
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
| Architecture Decision Records | 6 published | [docs/adr](./docs/adr) |
| Contracts (schema, filter grammar, relevance-set format) | Done — Phase 2 | [ADR-0006](./docs/adr/0006-request-response-schema.md) · [filter-grammar.md](./docs/filter-grammar.md) · [relevance-set-format.md](./docs/relevance-set-format.md) |
| Reference implementation (hybrid search, filtering, pagination) | Done — Phase 3 | [Quickstart](#quickstart) below |
| Relevance (golden set, metrics, regression gate, ranking A/B) | Done — Phase 4 | [relevance/golden-set.jsonl](./relevance/golden-set.jsonl), results in [ROADMAP.md](./ROADMAP.md) |

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

## Stack

**Python + FastAPI + one Postgres** — pgvector for the semantic index, `tsvector`/`ts_rank_cd`
(Postgres full-text search) for the lexical signal, no second search engine to run. Reciprocal
Rank Fusion combines the two rankings ([ADR-0003](./docs/adr/0003-hybrid-ranking.md)); filters
are pushed into both underlying queries before the top-k is taken
([ADR-0004](./docs/adr/0004-filtering-in-the-query.md)), never applied after.

The embedding model is a deterministic, offline **stub** (feature-hashed bag-of-words with a small
synonym table — see [src/search_api/embedder.py](./src/search_api/embedder.py)), not a real
semantic model, so the whole stack runs locally with no API key. It exists to prove the plumbing —
hybrid retrieval, fusion, filtering, pagination — works; swapping it for a real embedding model is
an internal change behind the contract ([ADR-0002](./docs/adr/0002-search-is-a-service.md)), not an
API change.

## Quickstart

```bash
make up      # docker compose up, waits for health, seeds the sample corpus
```

Then open http://localhost:8000 for a search console (try the exact-identifier, rare-term,
proper-noun, short-keyword, and meaning-carried example queries — each is a case
[ranking.md](./docs/ranking.md) names as pure-semantic's or pure-lexical's blind spot), or call the
API directly:

```bash
curl -s -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "why is my payment failing"}' | python -m json.tool
```

`make down` tears the stack down. `make test` runs the unit tests (fusion, filter translation,
cursor binding, embedder) without needing Postgres running.

## Relevance — measured, not assumed

[ADR-0005](./docs/adr/0005-relevance-as-slo.md) says search quality is a measured SLO. The golden
query set ([relevance/golden-set.jsonl](./relevance/golden-set.jsonl)) covers the blind spots
[ranking.md](./docs/ranking.md) names, and `make relevance-ab` measures all three ranking profiles
against it:

| Profile | avg nDCG@10 | avg recall@10 |
| --- | --- | --- |
| hybrid | **0.971** | **1.000** |
| semantic | 0.959 | 1.000 |
| lexical | 0.960 | 0.952 |

Hybrid wins because it recovers what each single signal misses on its own — see
[ROADMAP.md](./ROADMAP.md#milestone-4--relevance) for the per-query breakdown. `make
relevance-check` re-runs the set and fails the build if a change drops relevance past a small
tolerance against [relevance/baseline.json](./relevance/baseline.json); `make freshness` confirms a
newly indexed chunk is immediately findable.

## Why documented first

The API contract and the ranking model are the expensive, hard-to-change parts. Once a product depends
on the search contract, its shape is fixed; once relevance is defined, changing the definition
re-baselines every quality claim. The embedding model and the vector store, by contrast, are meant to
be swappable — which is only true if the contract in front of them was designed to hide them. Settling
that boundary on paper is far cheaper than discovering, after launch, that the store leaked into the
API.

## Roadmap

Four phases, tracked as GitHub milestones. See [ROADMAP.md](./ROADMAP.md).

1. **Design** — the API contract, hybrid ranking, filtering, relevance as an SLO, the ADRs — done
2. **Contracts** — the request/response schema, the filter grammar, the relevance-set format — done
3. **Reference implementation** — a search service with hybrid ranking and filtering, locally — done
4. **Relevance** — a golden query set and a harness that catches a ranking regression — done

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
