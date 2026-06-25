# Dev 2.3 — Estratégia de skills do projeto

> Entregável do exercício 2.3. Hierarquia Foundation → Domain → Artifact (Anexo C: `/skills/foundation`, `/skills/domain`, `/skills/artifact`).
> SKILL.md Foundation entregue: [`skills/foundation/typescript-conventions.md`](../../skills/foundation/typescript-conventions.md).

## 1. Árvore de skills (coerente com os artefatos repetidos do projeto)

```
skills/
├── foundation/        # convenções globais — herdadas por TODAS as outras
│   ├── typescript-conventions   ⭐ base (entregue neste exercício)
│   ├── error-handling           # AppError, retry/backoff, mapeamento p/ HTTP
│   └── project-structure        # pastas, módulos, exports, paths do Anexo C
│
├── domain/            # padrões por camada
│   ├── azure-functions-endpoint    # HTTP trigger v4, Zod na borda, pino
│   ├── azure-ai-search-integration # query top-k, vigência (ADR-0003)
│   ├── react-components            # padrões do painel web
│   └── testing-patterns            # Vitest, msw, fixtures
│
└── artifact/          # receitas de geração ponta a ponta
    ├── create-rag-endpoint     # endpoint RAG completo (embed→search→prompt→complete)
    ├── create-integration-test # teste de integração de endpoint
    └── create-react-card       # card de resposta/feedback no painel
```

Por que cada skill existe (≠ teórica): o projeto gera **vários endpoints Azure Functions com padrão RAG**, **um teste de integração por endpoint**, e **cards React** repetidamente (lista do enunciado). Cada Artifact mapeia 1:1 a um desses artefatos recorrentes; cada Domain encapsula o padrão de uma camada; Foundation evita repetir convenções em toda skill.

## 2. Mapeamento criação / consumo / frequência (visão multi-papel)

| Skill | Nível | Cria (papel) | Consome (papel + agente) | Frase-ativação | Frequência |
|-------|-------|--------------|--------------------------|----------------|-----------|
| typescript-conventions | Foundation | **Tech Lead** | Todos os devs · Copilot/Claude Code | "gerar qualquer .ts" | Altíssima (sempre) |
| error-handling | Foundation | Tech Lead / Dev Sênior | Devs · Copilot | "tratar erro / retry / lançar exceção" | Alta |
| project-structure | Foundation | Tech Lead | Devs · Copilot | "criar arquivo/módulo novo" | Alta |
| azure-functions-endpoint | Domain | Tech Lead | Devs · Copilot | "criar endpoint Azure Function" | Alta |
| azure-ai-search-integration | Domain | Dev Sênior | Devs · Copilot | "buscar chunks / indexar" | Média |
| react-components | Domain | Dev (front) | Devs · Copilot | "componente do painel" | Média |
| testing-patterns | Domain | **QA** | Devs + QA · Copilot | "escrever teste" | Alta |
| create-rag-endpoint | Artifact | Tech Lead + Dev Sênior | Devs · Copilot | "criar endpoint RAG completo" | Média |
| create-integration-test | Artifact | **QA** | Devs + QA · Copilot | "criar teste de integração" | Média |
| create-react-card | Artifact | Dev (front) | Devs · Copilot | "criar card de resposta/feedback" | Baixa-Média |
| (spec SDD) create-spec | Artifact | **Product Specialist** | PS + TL · Claude | "escrever requirements.md" | Média |

> **Não é só para devs:** o **QA** é dono de `testing-patterns` e `create-integration-test`; o **Product Specialist** é dono da skill de spec SDD; o **Tech Lead** é dono das Foundation/Domain técnicas. Consumo é amplo (devs + agentes), criação é por competência.

## 3. SKILL.md Foundation entregue (a base)
Escolhi `typescript-conventions` como a Foundation **mais importante** porque é a única herdada por 100% das outras skills (toda geração de `.ts` passa por ela). O arquivo contém: contexto/quando usar, 10 regras prescritivas DEVE/NÃO DEVE, exemplos DO/DON'T com **código TypeScript real** (validação Zod na borda, unions literais de domínio, logging/erros), e uma lista de **anti-padrões que o LLM realmente gera** (`as any`, `console.log`, import sem `.js`, `catch` vazio, `require` dinâmico, `@ts-ignore`, `process.env` espalhado, domínio como `string`).

## 4. Como skills se conectam ao AGENTS.md
O `AGENTS.md` (constitution) aponta para `/skills/` como a fonte de "como gerar". Fluxo de leitura do agente: **AGENTS.md** (regras duráveis + glossário) → **Foundation** (convenções) → **Domain** (camada) → **Artifact** (receita). Uma skill Artifact declara nas "Dependências" quais Foundation/Domain ler antes, garantindo herança consistente.
