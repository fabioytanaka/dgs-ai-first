# Dev 2.2 — Implementação com SDD + revisão crítica

> Entregável do exercício 2.2. `plan.md` → `tasks.md` → implementação da primeira task.
> Artefatos: [tasks.md](../../specs/query-endpoint/tasks.md), [handler.ts](../../src/functions/query/handler.ts), [validator.ts](../../src/functions/query/validator.ts), [shared/*](../../src/shared).

## Conexão com o cenário 1
No cenário 1 (Dev 1.3) o protótipo de RAG com ferramentas **open-source** (ChromaDB + sentence-transformers) **validou a abordagem** (embed → search → prompt → complete) e expôs o problema de chunking de tabelas (ADR-0004). Esta task é a versão de **produção** dessa mesma sequência, agora sobre Azure AI Search + Azure OpenAI e com os padrões do projeto (TS strict, Zod, pino, `AppError`). O context budget vem da **ADR-0002** (`config.ts`) e o tratamento de versões contraditórias da **ADR-0003** (refletido em `Chunk.source.isCurrentVersion` e na task T-08).

## Primeira task implementada — T-06 (setup do endpoint + validação)
Implementei T-06 e suas dependências mínimas (T-01..T-05), porque o handler não compila sem tipos/erros/logger/config/validator. Resultado: input validado **antes** de qualquer chamada ao modelo (VC-05).

### Evidência de execução real
```
$ npx tsc -p . --noEmit
TSC EXIT: 0                      # compila com strict:true, zero erros

$ npx vitest run tests/unit/query-validator.test.ts
 ✓ tests/unit/query-validator.test.ts (4 tests) 10ms
   Test Files  1 passed (1)
        Tests  4 passed (4)
```
Os 4 testes cobrem: pergunta válida; body sem `question` → `ValidationError` (VC-05); `question` < 3 chars; `history` > 3 turnos → rejeitada (ADR-0002).

## Revisão crítica do código gerado por IA (Copilot)
Ciclo aplicado: **gerar com Copilot → avaliar → reescrever**. Abaixo o que o Copilot produziu na 1ª passada e os ajustes que fiz antes de considerar a task pronta para code review. Estes são problemas **reais** observados no output, não cosméticos.

### Problema 1 — `request.json()` sem try/catch (crash em JSON malformado)
A 1ª geração do Copilot fez `const body = await request.json()` direto. Com body não-JSON, isso **rejeita a promise** e cai no `catch` genérico como 500 — quando o correto é **400** (erro do cliente). Reescrevi com try/catch dedicado retornando `VALIDATION_ERROR` 400. (Critério de aceite de T-05: "JSON malformado → ValidationError, nunca exceção não tratada".)

### Problema 2 — `catch (e: any)` e vazamento de stack trace
O Copilot gerou `catch (e: any) { return { status: 500, body: e.stack } }`. Dois defeitos: (1) `any` viola `typescript-conventions`; (2) devolver `e.stack` no body **vaza detalhes internos** ao cliente. Reescrevi para `catch (err: unknown)` + `isAppError(err)`, mapeando `AppError.statusCode/code` e retornando 500 **genérico** (sem stack) para o inesperado.

### Problema 3 — `console.log` e `authLevel: "anonymous"`
O Copilot logou com `console.log("query", body)` (viola "nunca console.log" e ainda logaria a pergunta inteira → PII) e registrou a function como `authLevel: "anonymous"`. Troquei por `logger` (pino, com redaction de `question`/`history`) e `authLevel: "function"`, já que o endpoint é interno para atendentes.

> **Honestidade (D4):** o que o Copilot **acertou** foi o esqueleto `app.http(...)` v4 e a estrutura geral do handler; o que **errou** foi exatamente a borda de robustez/segurança (tratamento de erro, logging, auth) — o tipo de detalhe que o `AGENTS.md`/skills precisam tornar prescritivo para o agente não repetir.

## Próximas tasks
T-07..T-10 (search, prompt-builder, completion, response-builder) seguem o mesmo padrão; o handler já está com o ponto de extensão marcado (retorna 501 até T-10).
