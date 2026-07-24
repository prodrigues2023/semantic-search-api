# The request path and hybrid fusion

Two diagrams: the request as it travels through the service behind the contract, and how the two
rankings fuse into one.

## The request path

A query enters through the stable contract and leaves as ranked results; everything in between — model,
store, ranking — is hidden ([ADR-0002](../adr/0002-search-is-a-service.md)). Filters are applied *with*
retrieval, not after ([ADR-0004](../adr/0004-filtering-in-the-query.md)).

```mermaid
graph TB
    caller["Caller<br/><i>query + filters + pagination</i>"] --> api["API contract"]
    api --> plan["Plan the search<br/><i>parse query, filters, options</i>"]

    plan --> lex["Lexical retrieval<br/><i>exact terms, identifiers</i>"]
    plan --> sem["Semantic retrieval<br/><i>meaning</i>"]

    filt["Filter set"] -. applied during retrieval, not after .-> lex
    filt -. applied during retrieval, not after .-> sem

    lex --> fuse["Rank-based fusion<br/><i>RRF over positions</i>"]
    sem --> fuse
    fuse --> score["Defined scores + provenance"]
    score --> api2["API contract"]
    api2 --> out["Ranked results<br/><i>to the caller</i>"]

    subgraph hidden["Behind the contract — swappable"]
        lex
        sem
        fuse
        model["Embedding model"]
        store["Vector store"]
    end

    classDef contract fill:#e9a13b,stroke:#b87a26,color:#000
    classDef node fill:#438dd5,stroke:#2e6295,color:#fff
    classDef hide fill:#08427b,stroke:#052e56,color:#fff
    class api,api2 contract
    class caller,plan,out,score node
    class lex,sem,fuse,model,store hide
```

The wall around the shaded box is the point: the caller touches only the contract, so the model, the
store, and the ranking can all change without a breaking change
([ADR-0002](../adr/0002-search-is-a-service.md)).

## Fusing the two rankings

Why hybrid beats either alone: each signal ranks its own strengths first, and rank-based fusion lets a
document carried by *either* signal surface ([ADR-0003](../adr/0003-hybrid-ranking.md)).

```mermaid
sequenceDiagram
    participant Q as Query 'error code E-4021'
    participant L as Lexical ranking
    participant S as Semantic ranking
    participant F as Rank fusion

    Q->>L: exact-term search
    L-->>F: doc with the exact code at rank 1
    Q->>S: meaning search
    S-->>F: topically-related docs, exact code buried at rank 30
    F->>F: combine by position, not by raw score
    Note over F: scales differ — BM25 and cosine are not addable
    F-->>Q: exact-code doc ranked high, carried by its lexical rank
```

Had the service ranked purely on semantics, the document containing the exact code `E-4021` would have
sat at rank 30, beneath topically-similar-but-wrong results — the pure-semantic blind spot
([ranking.md](../ranking.md)). Rank fusion lets its strong lexical position carry it to the top, and a
meaning query like "why is my payment failing" is carried the other way, by its semantic rank. Fusing
by position rather than by raw score is what makes this robust, since BM25 and cosine scores are not on
a comparable scale ([ADR-0003](../adr/0003-hybrid-ranking.md)).
