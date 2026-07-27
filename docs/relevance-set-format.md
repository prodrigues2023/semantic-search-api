# Relevance-set format

The format for the golden query set [ADR-0005](./adr/0005-relevance-as-slo.md) requires: fixed
queries with judged relevant results, so relevance has a ground truth to measure against
([Milestone 4](../ROADMAP.md)).

## Shape

```json
{
  "queryId": "q-001",
  "query": "why is my payment failing",
  "filters": [],
  "judgments": [
    { "chunkId": "doc-042:3", "grade": 3 },
    { "chunkId": "doc-042:1", "grade": 2 },
    { "chunkId": "doc-017:0", "grade": 1 }
  ],
  "note": "Exact-term-light, meaning-carried query -- should favour semantic ranking."
}
```

| Field | Meaning |
| --- | --- |
| `queryId` | Stable identity for this query across runs, so a metric trend can be tracked per query, not just averaged away |
| `query` | The literal query text sent to the service |
| `filters` | The same filter grammar as a real request ([filter-grammar.md](./filter-grammar.md)) — a golden query can be filtered too |
| `judgments` | Every chunk a human judged relevant to this query, with a graded relevance score |
| `note` | Why this query is in the set — which failure mode it probes (exact term, meaning, filtered, adversarial) |

## Grading scale

Graded, not binary — `0` (not judged / irrelevant) through `3` (highly relevant) — because nDCG is
defined for graded relevance and a binary judgment throws away the distinction between "the exact
answer" and "a chunk that merely mentions the topic." A chunk absent from `judgments` is graded `0`
by default; it is not an error to omit clearly irrelevant chunks.

## What the set must cover — one query per failure mode ADR-0003 names

| Query kind | Why it is in the set |
| --- | --- |
| Exact identifier / error code | Probes the lexical signal; pure-semantic's known blind spot |
| Rare / technical term | Same blind spot, different shape |
| Proper noun | Same blind spot |
| Short keyword | Weak semantic signal; lexical should carry it |
| Meaning-carried, few shared words | Probes the semantic signal; pure-lexical's blind spot |
| Filtered query | Confirms filtering does not silently corrupt ranking (ADR-0004) |
| A query with **zero** relevant documents in the corpus | Confirms the metric and the harness handle "correctly empty" without a false regression signal |

A set that only contains meaning-carried queries would make semantic-only ranking look sufficient —
exactly the blind spot [ADR-0003](./adr/0003-hybrid-ranking.md) exists to close, now hiding in the
measurement instead of the ranking. The set must be adversarial to the ranking strategy it tests,
not friendly to it.

## Maintenance

The set drifts when the corpus or real query patterns change
([ADR-0005](./adr/0005-relevance-as-slo.md)'s named cost). A query whose judged chunks no longer
exist (the source document was deleted) is a signal to re-judge or retire that query, not to leave
it silently scoring against stale ground truth.
