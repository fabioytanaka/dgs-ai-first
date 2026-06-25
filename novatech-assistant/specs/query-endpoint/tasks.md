# Tasks — Query Endpoint

> **Autor:** Dev (com apoio do Copilot). **Status:** aguardando aprovação do Tech Lead (Gate 2).
> Decomposição do `plan.md` em tasks **atômicas** — cada uma implementável e testável isoladamente.
> Estimativa: **P** (≤ 2h), **M** (meio dia), **G** (1 dia+). Path-alvo conforme Anexo C.

## Ordem de execução e dependências

```
T-01 (tipos) ──┬──> T-02 (errors) ──> T-03 (logger) ──> T-04 (config)
               └──> T-05 (validator) ──> T-06 (handler/setup) ──> T-07 (search)
                                                                    └─> T-08 (prompt-builder) ──> T-09 (completion) ──> T-10 (response-builder)
```

---

### T-01 — Tipos de domínio compartilhados
- **Path:** `src/shared/types.ts`
- **Descrição:** Definir os tipos do domínio usados pelo endpoint: `Chunk`, `SourceDocument`, `QueryRequest`, `QueryResponse`, `CustomerTier` (`'Gold' | 'Silver' | 'Standard'`).
- **Critérios de aceite:**
  - `CustomerTier` é um union literal com exatamente os 3 tiers (Gold/Silver/Standard) — não aceita string arbitrária.
  - `QueryResponse` inclui `source_document: SourceDocument` **obrigatório** (não opcional) e `low_confidence: boolean`.
  - `tsc -p .` compila sem erro com `strict: true`.
- **Dependências:** nenhuma.
- **Estimativa:** P

### T-02 — Hierarquia de erros customizados
- **Path:** `src/shared/errors.ts`
- **Descrição:** Criar `AppError` base + `ValidationError` (HTTP 400), `RetrievalError` (502), `CompletionError` (502), `ConfigError` (500). Cada erro carrega `statusCode` e `code` estável.
- **Critérios de aceite:**
  - `new ValidationError('msg').statusCode === 400` e `.code === 'VALIDATION_ERROR'`.
  - Todas as classes estendem `AppError`, que estende `Error`, com `name` setado corretamente.
  - Nenhum uso de `any`.
- **Dependências:** nenhuma.
- **Estimativa:** P

### T-03 — Logger estruturado (pino)
- **Path:** `src/shared/logger.ts`
- **Descrição:** Exportar uma instância pino configurada (nível por env, redaction de campos sensíveis). Proibir `console.log` no projeto.
- **Critérios de aceite:**
  - Exporta `logger` com métodos `.info/.warn/.error`.
  - `console.log` não aparece em nenhum arquivo de `src/` (verificável por lint/grep).
  - Redaction configurada para não logar a pergunta completa do usuário em nível `info`.
- **Dependências:** nenhuma.
- **Estimativa:** P

### T-04 — Configuração de ambiente validada
- **Path:** `src/shared/config.ts`
- **Descrição:** Carregar e validar env vars (endpoints/keys Azure, deployment GPT-4o, índice de busca, budget de contexto) com Zod, falhando rápido (`ConfigError`) na ausência.
- **Critérios de aceite:**
  - Variável ausente lança `ConfigError` com a lista de chaves faltantes (não retorna `undefined` silencioso).
  - Exporta objeto `config` tipado; nenhuma key é lida com `process.env.X` fora deste módulo.
- **Dependências:** T-02.
- **Estimativa:** P

### T-05 — Validação de input (Zod)
- **Path:** `src/functions/query/validator.ts`
- **Descrição:** Schema Zod do body `POST /api/query`: `question` (string, 3–1.000 chars, obrigatória), `conversation_id` opcional, `history` opcional (≤ 3 turnos — ADR-0002). Função `parseQueryRequest(body)` que retorna o tipo validado ou lança `ValidationError`.
- **Critérios de aceite:**
  - Body sem `question` → `ValidationError` (não chega ao modelo).
  - `question` com 2 chars → `ValidationError`; com 3 chars → ok.
  - `history` com 4 turnos → `ValidationError` (respeita limite da ADR-0002).
  - JSON malformado → `ValidationError`, nunca exceção não tratada.
- **Dependências:** T-01, T-02.
- **Estimativa:** M

### T-06 — Setup do endpoint (HTTP trigger + wiring de validação) ⭐ PRIMEIRA TASK
- **Path:** `src/functions/query/handler.ts`
- **Descrição:** Registrar a Azure Function v4 (`app.http`) em `POST /api/query`. Fazer parse/validação via T-05, montar resposta de erro estruturada para `ValidationError`, e responder `501 Not Implemented` para o fluxo de RAG (a ser preenchido em T-07..T-10). Logar início/fim com `logger`.
- **Critérios de aceite:**
  - `POST /api/query` sem `question` → **400** com `{ error: { code: 'VALIDATION_ERROR', message } }`, **sem** chamar search/completion (VC-05).
  - `POST /api/query` com `question` válida → **501** (placeholder) até T-10 — comprovando que validação passou.
  - Nenhum `console.log`; toda saída via `logger`.
  - Erros inesperados → **500** genérico, sem vazar stack trace no body.
- **Dependências:** T-05 (e T-01..T-04).
- **Estimativa:** M

### T-07 — Integração com Azure AI Search (top-5 chunks)
- **Path:** `src/services/search.ts`
- **Descrição:** Embedding da pergunta + busca top-5 no índice, com retry/backoff. Retorna `Chunk[]` com metadado de vigência (ADR-0003).
- **Critérios de aceite:** retorna ≤ 5 chunks ordenados por score; falha de rede → `RetrievalError` após N retries; mock testável via msw.
- **Dependências:** T-04, T-02, T-01.
- **Estimativa:** G

### T-08 — Montagem de prompt com context budget (ADR-0002)
- **Path:** `src/services/prompt-builder.ts`
- **Descrição:** Montar prompt = system prompt (`/prompts/system-prompt.md`) + chunks (≤ ~8K tokens) + pergunta + histórico ≤ 3 turnos. Ao detectar 2 versões do mesmo doc, priorizar a vigente e sinalizar (ADR-0003).
- **Critérios de aceite:** total estimado ≤ 12K tokens; trunca chunks excedentes por score; marca contradição quando há v1+v2.
- **Dependências:** T-07.
- **Estimativa:** G

### T-09 — Integração com Azure OpenAI (GPT-4o)
- **Path:** `src/services/completion.ts`
- **Descrição:** Chamada ao GPT-4o com retry/backoff; timeout coerente com VC-01 (< 30s).
- **Critérios de aceite:** timeout configurável; falha → `CompletionError`; testável com mock.
- **Dependências:** T-08, T-04.
- **Estimativa:** M

### T-10 — Montagem da resposta com fonte e confiança
- **Path:** `src/functions/query/response-builder.ts`
- **Descrição:** Montar `QueryResponse` com `source_document` obrigatório (VC-02), `low_confidence` + aviso quando aplicável, e mensagem padrão de "não encontrado" quando não há chunk relevante (VC-04).
- **Critérios de aceite:** 100% das respostas têm `source_document`; sem match → mensagem padrão; baixa confiança → aviso + sugestão de escalar.
- **Dependências:** T-09.
- **Estimativa:** M
