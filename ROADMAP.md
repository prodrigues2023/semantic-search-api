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

| Issue | Deliverable | Status |
| --- | --- | --- |
| Request/response schema | Query, filters, pagination, and ranked results with scores and provenance | Done — [ADR-0006](./docs/adr/0006-request-response-schema.md), [schemas](./contracts/schemas) |
| Filter grammar | The set of filter operators and how they compose | Done — [filter-grammar.md](./docs/filter-grammar.md) |
| Relevance-set format | Queries, judged results, and the metric definitions | Done — [relevance-set-format.md](./docs/relevance-set-format.md) |
| ADR-0006 | Request/response schema and filter grammar | Done — [ADR-0006](./docs/adr/0006-request-response-schema.md) |

**Exit criteria:** a client and the service could be built independently against the contracts and
agree on every field. **Met.**

---

## Milestone 3 — Reference implementation

**Goal:** `make up` runs a search service with hybrid ranking and filtering over a sample corpus.

| Issue | Deliverable | Status |
| --- | --- | --- |
| Search endpoint | The API contract, backed by a vector store and a lexical index | Done — FastAPI `/search`, Postgres + pgvector |
| Hybrid ranking | Lexical and semantic retrieval fused into one ranked list | Done — `src/search_api/ranking.py`, Reciprocal Rank Fusion |
| Filtered search | Filters applied with ranking, not as a post-filter | Done — `src/search_api/filters.py`, pushed into both legs |
| Pagination and scores | Stable pagination and scores callers can reason about | Done — opaque cursor bound to query/filters/profile hash |
| Local environment | One command, stubbed model, sample corpus, no cloud account | Done — `make up`, deterministic stub embedder, 6-doc corpus |

**Exit criteria:** a first-time reader searches with a filter, gets ranked results with scores, and
sees an exact-term query and a semantic query both work. **Met** — verified live: `error code
E-4021` ranks the exact-match chunk first via `lexicalRank=1`; `why is my payment failing` ranks a
paraphrased chunk first via the semantic leg; a `category` filter narrows results without changing
the fusion logic; a cursor from one query rejected against a different query returns `400`.

---

## Milestone 4 — Relevance

**Goal:** make search quality a measured objective, not a subjective impression.

| Issue | Deliverable | Status |
| --- | --- | --- |
| Golden query set | Queries with judged relevant results | Done — [relevance/golden-set.jsonl](./relevance/golden-set.jsonl), one query per ADR-0003 blind spot |
| Relevance metrics | nDCG and recall at k, defined and computed | Done — [src/search_api/metrics.py](./src/search_api/metrics.py) |
| Regression harness | Run the set on a change; assert relevance did not drop | Done — `make relevance-check`, gates on [relevance/baseline.json](./relevance/baseline.json) |
| Ranking A/B | Compare two ranking configurations on the same set | Done — `make relevance-ab` |
| Freshness check | A newly indexed document is findable within the freshness target | Done — `make freshness` |

**Exit criteria met**, measured, not assumed — running `make relevance-ab` against the seeded corpus:

| Profile | avg nDCG@10 | avg recall@10 |
| --- | --- | --- |
| hybrid | **0.971** | **1.000** |
| semantic | 0.959 | 1.000 |
| lexical | 0.960 | 0.952 |

Hybrid beats both single-signal profiles on the same set — lexical alone misses part of the
meaning-carried query (`recall@10 = 0.667` on that query alone; the semantic leg recovers it), and
semantic alone loses a little precision on the exact-identifier and proper-noun queries relative to
hybrid. The regression harness was verified to actually gate: corrupting a golden judgment to an
unreachable chunk id drops nDCG@10 from 0.971 to 0.828 and `relevance check` correctly fails
(exit 1) past the 0.02 tolerance.

Building this harness surfaced a real lexical-search bug, not a hypothetical one: `plainto_tsquery`
ANDs every term in the query, so a chunk containing only *some* of the query's lexemes (e.g. the
identifier but not the word "error") was silently excluded rather than merely ranked lower. Fixed
in [search.py](./src/search_api/search.py) by turning the query into an OR of its own lexemes and
letting `ts_rank_cd` rank by overlap — exactly the kind of fusion-adjacent bug ADR-0005 exists to
catch with a number instead of a hunch.

**Exit criteria:** a ranking change that degrades relevance is caught by the harness before it ships,
with a number, not a hunch.
