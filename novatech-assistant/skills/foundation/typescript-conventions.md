---
name: typescript-conventions
level: foundation
description: Convenções base de TypeScript do NovaTech Assistant. LEIA ANTES de gerar qualquer .ts. Toda skill Domain e Artifact herda destas regras.
owner: Tech Lead
consumed_by: [GitHub Copilot, Claude Code, todos os devs]
---

# Skill (Foundation) — TypeScript Conventions

## Contexto / quando usar
Esta é a skill **base** do projeto. Toda geração de código `.ts` (endpoints, services, pipeline, bot, testes) DEVE respeitá-la. As skills Domain (`azure-functions-endpoint`, `testing-patterns`, …) e Artifact (`create-rag-endpoint`, …) **dependem** desta e não repetem suas regras.

Stack alvo: TypeScript 5.5 `strict: true`, ESM (`"type": "module"`), Azure Functions v4, Zod, pino. Ver `tsconfig.json` e `AGENTS.md`.

## Regras prescritivas (DEVE / NÃO DEVE)

1. **DEVE** rodar com `strict: true`. Nunca relaxe flags do compilador para "fazer compilar".
2. **NÃO DEVE** usar `any`. Para valor desconhecido, use `unknown` e faça narrowing (Zod, type guard).
3. **DEVE** validar todo dado externo (HTTP body, env, resposta de API) com **Zod** na fronteira; o tipo interno vem de `z.infer`.
4. **NÃO DEVE** usar `console.log` / `console.error`. Use `logger` (pino) de `src/shared/logger.ts`.
5. **DEVE** lançar erros da hierarquia `AppError` (`src/shared/errors.ts`) — nunca `throw new Error("string solta")` em código de produção.
6. **DEVE** usar imports ESM com extensão `.js` em paths relativos (ex: `import { logger } from "../../shared/logger.js"`), porque `module: ESNext`.
7. **NÃO DEVE** ler `process.env` fora de `src/shared/config.ts`. Consuma `config`.
8. **DEVE** preferir `interface`/`type` literais a `string` solta para conceitos do domínio (ex: `CustomerTier`, não `string`).
9. **DEVE** usar `const`; `let` só quando há reatribuição real. Nunca `var`.
10. **DEVE** marcar funções públicas async com retorno explícito `Promise<T>`.

## Exemplos concretos (DO / DON'T)

### Tratamento de valor externo
```typescript
// ❌ DON'T — silencia o compilador e propaga lixo
function handle(body: any) {
  return body.question.trim(); // estoura em runtime se body for null
}

// ✅ DO — fronteira validada, tipo derivado do schema
import { z } from "zod";
const schema = z.object({ question: z.string().min(3) });
function handle(body: unknown) {
  const { question } = schema.parse(body); // lança ZodError → mapeado p/ ValidationError
  return question.trim();
}
```

### Tipos de domínio (linguagem ubíqua)
```typescript
// ❌ DON'T — aceita "Platinum", que NÃO existe (SLA-2024 §1 / FAQ-15)
function slaFor(tier: string) { /* ... */ }

// ✅ DO — o compilador rejeita tiers inventados
type CustomerTier = "Gold" | "Silver" | "Standard";
function slaFor(tier: CustomerTier) { /* ... */ }
```

### Logging e erros
```typescript
// ❌ DON'T
console.log("erro", e);
throw new Error("falhou");

// ✅ DO
import { logger } from "../shared/logger.js";
import { RetrievalError } from "../shared/errors.js";
logger.error({ err }, "search.failed");
throw new RetrievalError("Azure AI Search indisponível após 3 tentativas");
```

## Anti-padrões que o Copilot/LLM realmente gera (evite)
- `data as any` ou `as unknown as T` para "calar" o compilador → use Zod/guards.
- `console.log` de debug deixado no código → use `logger.debug`.
- `import x from "./y"` **sem** a extensão `.js` → quebra em ESM/runtime.
- `catch (e) { }` vazio ou `catch (e: any)` → use `catch (err: unknown)` + `isAppError(err)`.
- `require(...)` dinâmico em projeto ESM → use `import`.
- Ler `process.env.FOO` espalhado pelo código → centralize em `config.ts`.
- `// @ts-ignore` para pular erro de tipo → corrija o tipo.
- Tipos do domínio como `string` (tier, status, documentId) → use unions literais.

## Dependências
Nenhuma (é a raiz da hierarquia). É **pré-requisito** de: `error-handling`, `project-structure` (Foundation) e de todas as skills Domain/Artifact.
