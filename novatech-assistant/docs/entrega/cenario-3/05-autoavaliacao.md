# 05 — Autoavaliação contra `avaliacao-desenvolvedor.md` (Cenário 3)

> Avaliação honesta da entrega contra os critérios do papel (Score 3 vs Red flag) e as 5 dimensões Foundation.

## Ex. 3.1 — Structured output e verificações determinísticas

| Critério (rubrik) | Status | Evidência |
|---|---|---|
| Schema de structured output | ✅ Score 3 | Zod `.strict()` com `answer`/`source_document`/`confidence_score`, tipos e faixas corretas ([response-validator.ts](../../../src/services/response-validator.ts)) |
| Guardrail 1 (source_document) | ✅ Score 3 | Schema torna a fonte obrigatória; `validateResponse` retorna `SAFE_FALLBACK` — **bloqueia**, com teste provando |
| Guardrail 2 (carga perigosa + devolução) | ✅ Score 3 | Detecta o combo, bloqueia afirmação/omissão da negativa; não burlável por acento/caixa; look-behind evita falso-positivo |
| Code review com Claude | ✅ Score 3 | 4 problemas **reais** (sem `.strict`, source vazio, score sem faixa, regex frágil) corrigidos ([dev-3.1](dev-3.1-structured-output-harness.md)) |
| Probabilístico vs determinístico | ✅ Score 3 | Tabela conceitual + ordem schema-antes-de-conteúdo |

## Ex. 3.2 — Revisão crítica de código gerado por IA

| Armadilha obrigatória | Identificada na análise própria? |
|---|---|
| `as any` sem Zod | ✅ |
| `console.log` vs pino | ✅ |
| `require` dinâmico | ✅ |
| `attendantEmail` (PII) logado | ✅ |

| Critério (rubrik) | Status | Evidência |
|---|---|---|
| Análise própria ANTES do Claude | ✅ Score 3 | 6 problemas (4 obrigatórios + status + try/catch) antes de chamar o Claude ([dev-3.2](dev-3.2-revisao-codigo-ia.md) §1) |
| Comparação humano vs Claude | ✅ Score 3 | Honesta: o Claude pegou 2 que eu não vi (client recriado, `.strict`) (§3) |
| Código reescrito | ✅ Score 3 | Zod, pino, import estático, sem PII em log, 201, erros sem stack ([handler.ts](../../../src/functions/feedback/handler.ts)) |

## 5 Dimensões (Foundation)

| Dim | Nota | Justificativa |
|---|---|---|
| D1 Domínio conceitual | **3** | Explica por que structured output (campo validado) > pedir fonte no prompt; ordem schema→conteúdo; HITL via `SAFE_FALLBACK` |
| D2 Uso de ferramentas | **3** | Ciclo Copilot gerar → Claude revisar → reescrever documentado; `tsc`/`vitest` reais |
| D3 Qualidade do entregável | **3** | Código funcional que **bloqueia** (não loga), 22 testes verdes, paths exatos do Anexo C |
| D4 Pensamento crítico | **3** | 4 armadilhas na análise própria; admite os 2 achados que só o Claude viu; bug do regex exposto pelo próprio teste |
| D5 Aplicabilidade | **3** | POL-001 §3.2, AGENTS.md, ADR-0002/0003, guardrails do cenário 2; respeita fronteira com o exercício do TL |

## Score estimado
Média das 5 dimensões = **3.0** em ambos os exercícios → score do cenário **3.0** → **Aprovado com distinção**.

## Regras de corte — checagem
| Regra | Risco | Situação |
|---|---|---|
| "humano primeiro" sem análise própria → D4 ≤ 1 | Alto | ✅ Análise própria documentada antes do Claude |
| Armadilha não identificada → D4 ≤ 1 | Alto | ✅ As 4 obrigatórias identificadas |
| Copilot sem evidência de geração/revisão → D2 ≤ 1 | Médio | ✅ v1 do Copilot + ciclo de revisão documentados |
| Código que só loga (não bloqueia) → D3 ≤ 2 | **Crítico** | ✅ `SAFE_FALLBACK` retornado e **testado** |
| Ignora decisões dos cenários 1/2 → D5 ≤ 2 | Médio | ✅ ADRs, AGENTS.md, guardrails referenciados |

**Conclusão:** entrega aprovada, **3.0 (Aprovado com distinção)**.
