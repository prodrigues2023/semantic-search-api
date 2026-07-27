# Semantic Search API

> Busca semântica é um serviço com contrato de API, não um notebook. Um contrato query-para-resultados
> limpo, ranking híbrido que respeita termos exatos tanto quanto significado, filtragem como parte da
> query, e relevância medida como SLO. Documentado primeiro, neutro de fornecedor, implementado em
> público.

[![Fase](https://img.shields.io/badge/fase-4%20relev%C3%A2ncia-blue)](./ROADMAP.md)
[![ADRs](https://img.shields.io/badge/ADRs-6-green)](./docs/adr)
[![Licença](https://img.shields.io/badge/licen%C3%A7a-MIT-lightgrey)](./LICENSE)

A maioria das buscas semânticas nasce como notebook: embeda documentos, embeda a query, retorna os
vetores mais próximos. Demonstra bem e desmorona como produto. O notebook não tem contrato estável
para quem chama, rankeia puramente por similaridade semântica então tropeça em matches exatos e termos
raros, trata filtragem como algo secundário que silenciosamente quebra os melhores resultados, e chama
a relevância de "boa" com base em algumas queries que alguém olhou.

Um *serviço* de busca é outro artefato. Tem um contrato de API do qual um produto depende, ranking que
funde sinal léxico e semântico, filtragem que faz parte da query e é aplicada sem corromper o ranking,
e relevância definida como objetivo medido contra um conjunto fixo de queries. Este repositório é o
design desse serviço — a camada acima de um vector store que um produto real chama.

**English:** [README.md](./README.md)

---

## O que já existe

| Área | Status | Link |
| --- | --- | --- |
| Contexto e escopo | Pronto | [docs/context.md](./docs/context.md) |
| Contrato de API | Pronto | [docs/api-contract.md](./docs/api-contract.md) |
| Ranking — híbrido e fundido | Pronto | [docs/ranking.md](./docs/ranking.md) |
| Diagramas de requisição | Pronto | [docs/diagrams](./docs/diagrams) |
| Registros de Decisão de Arquitetura | 6 publicados | [docs/adr](./docs/adr) |
| Contratos (schema, gramática de filtros, formato do golden set) | Pronto — Fase 2 | [ADR-0006](./docs/adr/0006-request-response-schema.md) |
| Implementação de referência (busca híbrida, filtragem, paginação) | Pronta — Fase 3 | `make up` (veja o README em inglês) |
| Relevância (golden set, métricas, gate de regressão, A/B) | Pronta — Fase 4 | `make relevance-ab` (veja o README em inglês) |

## A ideia

**Um contrato estável na frente, ranking híbrido dentro, relevância medida — é isso que faz da busca
um serviço.** Quatro decisões, cada uma um ADR:

- **Busca é um serviço com contrato de API estável** — query, filtros e paginação entram; resultados
  rankeados com scores e proveniência saem. O contrato é desacoplado do modelo e do store por trás.
- **Ranking é híbrido** — similaridade semântica pura erra matches exatos, identificadores e termos
  raros; léxica pura erra significado. O serviço funde os dois.
- **Filtragem faz parte da query** — um filtro é aplicado *junto* ao ranking, não colado depois —
  porque pós-filtrar uma lista top-k retorna silenciosamente menos e piores resultados.
- **Relevância é um SLO medido** — qualidade de busca é um objetivo acompanhado contra um golden query
  set, não um "parece bom" subjetivo.

> Os documentos técnicos são mantidos em inglês para alcançar o público mais amplo possível.
> Este README traz o contexto em português.

## Roadmap

Quatro fases, acompanhadas como milestones no GitHub. Detalhes em [ROADMAP.md](./ROADMAP.md).

1. **Design** — o contrato de API, ranking híbrido, filtragem, relevância como SLO, os ADRs — pronto
2. **Contratos** — o schema de request/response, a gramática de filtros, o formato do conjunto de relevância — pronto
3. **Implementação de referência** — um serviço de busca com ranking híbrido e filtragem, local — pronto
4. **Relevância** — um golden query set e um harness que pega uma regressão de ranking — pronto

## Relacionados

- [vector-db-benchmark](https://github.com/prodrigues2023/vector-db-benchmark) — como o vector store sob este serviço é escolhido, numa curva recall × latência
- [rag-reference-architecture](https://github.com/prodrigues2023/rag-reference-architecture) — RAG, que chama um serviço de recuperação como este como primeira etapa
- [document-ingestion-pipeline](https://github.com/prodrigues2023/document-ingestion-pipeline) — como documentos são indexados e mantidos frescos, que é o que este serviço busca

## Autor

Paulo Roberto Franco Rodrigues — AI Solutions Architect.
Recentemente projetou frameworks corporativos de IA e atuou em comitê de arquitetura de IA definindo
os padrões de engenharia que trazem disciplina de software para a entrega de IA.
[LinkedIn](https://linkedin.com/in/paulo-roberto-franco-rodrigues)

## Licença

MIT — veja [LICENSE](./LICENSE).
