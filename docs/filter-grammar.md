# Filter grammar

The grammar [ADR-0006](./adr/0006-request-response-schema.md) fixes: deliberately small, applied
with ranking rather than after it ([ADR-0004](./adr/0004-filtering-in-the-query.md)).

## Shape

A filter is a flat list of conditions, **ANDed together** — no OR, no NOT, no nesting:

```json
[
  { "field": "category", "op": "eq", "value": "billing" },
  { "field": "status", "op": "in", "value": ["open", "pending"] },
  { "field": "created_at", "op": "gte", "value": "2026-01-01T00:00:00Z" }
]
```

## Operators

| Operator | Meaning | Value type |
| --- | --- | --- |
| `eq` | Field equals value | scalar (string, number, bool) |
| `in` | Field is one of a set | array of scalars |
| `gte` | Field ≥ value | number or ISO-8601 date-time |
| `lte` | Field ≤ value | number or ISO-8601 date-time |

`gte`/`lte` on the same field compose a range (`created_at gte X` + `created_at lte Y`); there is
no dedicated `range` operator because two conditions already express it without adding a fifth op.

## What is deliberately not supported

- **`or` / `not` / nested groups.** "Category A or category B" is not one request. A caller needing
  it issues multiple searches and merges client-side — real extra work, traded for a grammar cheap
  to specify, validate, and push into a store's native filtered retrieval
  ([ADR-0004](./adr/0004-filtering-in-the-query.md)).
- **Free-text field matching as a filter operator.** A filter constrains eligibility; matching text
  is what the `query` and ranking already do. Conflating the two would blur exactly the boundary
  [ADR-0004](./adr/0004-filtering-in-the-query.md) draws between filtering (correctness) and
  ranking (relevance).

## Access control

A permission filter (e.g. `tenant_id eq "acme"`, `visible_to in ["user-42", "team-9"]`) is **just
another condition in the same list** — not a special code path — because
[ADR-0004](./adr/0004-filtering-in-the-query.md) treats access control as a correctness constraint
applied during retrieval, never a post-hoc drop. This means a caller that forgets to add the
permission condition gets an *unfiltered* (over-broad) result, not a silently narrowed one — the
service does not inject access filters implicitly; the caller must always pass them explicitly.
That is a deliberate, documented responsibility boundary, not an oversight.

## Diagnostics

`diagnostics.filterExcludedAll: true` in the response means the filters, applied together, matched
zero documents in the corpus — distinct from `results: []` with `filterExcludedAll: false`, which
means the query itself had no good matches among the eligible set
([ADR-0004](./adr/0004-filtering-in-the-query.md), [api-contract.md](./api-contract.md)).
