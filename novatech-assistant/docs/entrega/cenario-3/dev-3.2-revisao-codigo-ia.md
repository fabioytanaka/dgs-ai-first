# Dev 3.2 — Revisão crítica de código gerado por IA

> **Tópico:** Revisão Crítica de Outputs de IA · **Ferramentas:** Claude (2º revisor) + GitHub Copilot (reescrita)
> **Artefatos:** [handler.ts](../../../src/functions/feedback/handler.ts) · [validator.ts](../../../src/functions/feedback/validator.ts) · [repository.ts](../../../src/functions/feedback/repository.ts) · [feedback-validator.test.ts](../../../tests/unit/feedback-validator.test.ts)

O Tech Lead pediu revisão do módulo de feedback gerado pelo Copilot antes do merge. Fiz **minha própria revisão primeiro**, depois usei o Claude como segundo revisor, comparei honestamente e reescrevi.

## §1 — Minha revisão (ANTES do Claude)

Padrão de referência: `AGENTS.md` (TS strict · Zod para input · pino, nunca `console.log` · nunca logar dado pessoal · imports estáticos, nunca `require` dinâmico).

| # | Problema | Linha (v1) | Tipo | Por quê |
|---|---|---|---|---|
| 1 | `await request.json() as any` sem validação | `const body = ... as any` | **Violação AGENTS.md** (bug de segurança latente) | `as any` desliga o type-checker; nenhum campo é validado → `rating` pode ser string, `queryId` ausente, payload arbitrário persiste no Cosmos |
| 2 | `console.log('Feedback recebido:', ...)` | log do feedback | **Violação AGENTS.md** | Projeto exige pino; além disso loga o objeto inteiro |
| 3 | `console.log` inclui `attendantEmail` | mesmo log | **Segurança (PII)** | E-mail do atendente é dado pessoal — proibido em log. Vaza PII para o sink de logs |
| 4 | `require('@azure/cosmos')` dinâmico dentro do handler | construção do client | **Violação AGENTS.md** | Import dinâmico proibido; e construir infra dentro do handler o torna **não testável** |
| 5 | `return { status: 200, body: 'OK' }` | retorno | Bug menor / contrato | Criação deveria ser **201**; corpo deveria ser JSON estruturado, não string solta |
| 6 | Sem try/catch | corpo inteiro | Bug de robustez | JSON malformado ou falha do Cosmos → exceção não tratada → 500 sem corpo estruturado |

Os 4 problemas **obrigatórios** do exercício (1, 2, 3, 4) eu identifiquei de forma independente. Os itens 5 e 6 são complementos meus.

## §2 — Revisão do Claude (2º revisor)

Prompt usado (resumo): *"Revise este handler Azure Functions contra o AGENTS.md (TS strict, Zod, pino, sem PII em log, import estático). Classifique cada problema e diga o que está faltando."*

O Claude apontou:
- Os mesmos 4 obrigatórios (`as any`, `console.log`, `require` dinâmico, `attendantEmail` logado).
- **Acrescentou** dois que eu havia subdimensionado: (a) o handler **constrói o `CosmosClient` a cada invocação** — desperdício de conexão/custo, deveria ser reutilizado; (b) o `timestamp` vem implícito mas **nada impede o cliente de enviar campos extras** que seriam persistidos junto (falta `.strict()` no schema).
- **Concordou** que 201 é o status correto para criação.

## §3 — Comparação honesta (humano vs Claude)

| Achado | Eu (antes) | Claude | Observação |
|---|---|---|---|
| `as any` sem Zod | ✅ | ✅ | Convergência |
| `console.log` vs pino | ✅ | ✅ | Convergência |
| `attendantEmail` (PII) logado | ✅ | ✅ | Convergência — o achado mais crítico |
| `require` dinâmico | ✅ | ✅ | Convergência |
| Status 200 vs 201 | ✅ | ✅ | Convergência |
| Sem try/catch | ✅ | ⚠️ parcial | Eu detalhei mais o caminho do 500 |
| `CosmosClient` recriado por request | ❌ (não vi) | ✅ | **O Claude pegou, eu não** — virou o singleton lazy no `repository.ts` |
| Falta `.strict()` (campos extras persistidos) | ❌ (não vi) | ✅ | **O Claude pegou, eu não** — virou `.strict()` no schema |

**Não foi "concordamos em tudo".** Acertei os 4 obrigatórios e o status sozinho; o Claude me pegou em dois pontos reais (reuso de client e `.strict()`) que eu não tinha visto. Incorporei ambos na reescrita.

## §4 — Código reescrito (segue o AGENTS.md integralmente)

Repartido em 3 arquivos (separação de responsabilidades + testabilidade):

- **[`validator.ts`](../../../src/functions/feedback/validator.ts)** — Zod `.strict()` valida `queryId` (UUID), `rating` (int 1–5), `comment?` (≤2000), `attendantEmail` (e-mail). Substitui o `as any`.
- **[`repository.ts`](../../../src/functions/feedback/repository.ts)** — `@azure/cosmos` via **import estático**, atrás de uma interface `FeedbackRepository`, com `CosmosClient` **construído uma vez** (singleton lazy) e um *test seam* (`setFeedbackRepository`) para testar o handler sem Cosmos. Resolve o `require` dinâmico **e** o client recriado por request.
- **[`handler.ts`](../../../src/functions/feedback/handler.ts)** — usa pino (`logger.child`), loga **apenas** `queryId` e `rating` (nunca `attendantEmail`/`comment`), `timestamp` definido no servidor, erros mapeados por `AppError` sem vazar stack, retorna **201** com JSON.

Defesa em profundidade adicional: incluí `attendantEmail` e `comment` nas `redact.paths` do [`logger.ts`](../../../src/shared/logger.ts) — mesmo que um futuro dev esqueça, o pino censura.

### Tabela de resolução das armadilhas

| Armadilha obrigatória | Status na reescrita |
|---|---|
| `as any` sem Zod | ✅ Zod `.strict()` em `validator.ts` |
| `console.log` vs pino | ✅ `logger` (pino) em `handler.ts` |
| `require` dinâmico | ✅ import estático em `repository.ts` |
| `attendantEmail` logado | ✅ não logado + redaction no pino |

### Evidência
```
$ npx tsc -p . --noEmit          → TSC_EXIT=0
$ npx vitest run                 → 22 passed (22)  (inclui 6 testes do feedback-validator)
$ grep -rn "console.log|as any|require(" src   → só comentários de documentação, zero no código
```
