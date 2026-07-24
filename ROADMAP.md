# Roadmap

Four milestones. Each ships something usable on its own.

Track these as GitHub Milestones.

---

## Milestone 1 — Design (docs only)

**Goal:** a reader understands what makes search a service — contract, hybrid ranking, filtering,
measured relevance — before any code.

| Issue | Deliverable |
| --- | --- |
| Write context document | Problem, users, scope, explicit non-goals |
| API contract | Query, filters, pagination in; ranked results with scores out |
| Ranking | Why hybrid, and how lexical and semantic are fused |
| Request diagrams | The request path and the fusion of the two rankings |
| ADR-0001 | Record architecture decisions in ADRs |
| ADR-0002 | Search is a service with a stable API contract |
| ADR-0003 | Ranking is hybrid — lexical and semantic, fused |
| ADR-0004 | Filtering is part of the query, applied with ranking |
| ADR-0005 | Relevance is a measured SLO, not a subjective call |

**Exit criteria:** a reader can explain why a notebook is not a service, and every decision traces to
the contract hiding the model and store behind it.

---

## Milestone 2 — Contracts

**Goal:** the formats are specified, so a caller and the service integrate consistently.

| Issue | Deliverable |
| --- | --- |
| Request/response schema | Query, filters, pagination, and ranked results with scores and provenance |
| Filter grammar | The set of filter operators and how they compose |
| Relevance-set format | Queries, judged results, and the metric definitions |
| ADR-0006 | Request/response schema and filter grammar |

**Exit criteria:** a client and the service could be built independently against the contracts and
agree on every field.

---

## Milestone 3 — Reference implementation

**Goal:** `make up` runs a search service with hybrid ranking and filtering over a sample corpus.

| Issue | Deliverable |
| --- | --- |
| Search endpoint | The API contract, backed by a vector store and a lexical index |
| Hybrid ranking | Lexical and semantic retrieval fused into one ranked list |
| Filtered search | Filters applied with ranking, not as a post-filter |
| Pagination and scores | Stable pagination and scores callers can reason about |
| Local environment | One command, stubbed model, sample corpus, no cloud account |

**Exit criteria:** a first-time reader searches with a filter, gets ranked results with scores, and
sees an exact-term query and a semantic query both work.

---

## Milestone 4 — Relevance

**Goal:** make search quality a measured objective, not a subjective impression.

| Issue | Deliverable |
| --- | --- |
| Golden query set | Queries with judged relevant results |
| Relevance metrics | nDCG and recall at k, defined and computed |
| Regression harness | Run the set on a change; assert relevance did not drop |
| Ranking A/B | Compare two ranking configurations on the same set |
| Freshness check | A newly indexed document is findable within the freshness target |

**Exit criteria:** a ranking change that degrades relevance is caught by the harness before it ships,
with a number, not a hunch.
