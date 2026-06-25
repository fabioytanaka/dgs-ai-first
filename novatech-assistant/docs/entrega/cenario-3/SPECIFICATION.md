# SPECIFICATION.md — Entrega do Desenvolvedor (Cenário 3)

> **Programa:** Trilha de Certificação AI First — DGS / DB1 Global Software
> **Papel:** Desenvolvedor · **Cenário-Âncora 3:** Fase de Governança e Validação
> **Escopo:** exercícios 3.1 (structured output + guardrails) e 3.2 (revisão crítica de código IA)
> **Repositório-alvo:** `novatech-assistant` (estrutura do Anexo C)

Este documento é a spec da própria entrega: define **o que** será produzido, **onde** (paths do Anexo C), e **como cada item satisfaz** os critérios de `avaliacao-desenvolvedor.md`. É o contrato verificável entre a tarefa e a avaliação.

## Outcomes
1. **Structured output validável** (Zod) que torna `source_document` obrigatório por construção — não por confiança no prompt.
2. **2 guardrails determinísticos** que **bloqueiam** (não só logam) respostas inválidas, com testes que provam o bloqueio.
3. **Code review honesto** do código gerado por IA (próprio → Claude → comparação) e **reescrita** do handler de feedback aderente ao `AGENTS.md`.

## Scope boundaries
- **Dentro:** os 2 exercícios do Dev (3.1 e 3.2), o schema, os 2 guardrails, o code review, a reescrita e os testes.
- **Fora:** lookup table de frete (não pedido — nota de calibração); verificação de fonte contra lista de docs válidos (exercício do **TL 3.1**); exercícios de outros papéis; deploy real em Azure.

## Prior decisions respeitadas (cenários 1 e 2)
- **ADR-0002** context budget (histórico ≤ 3 turnos) · **ADR-0003** vigência de documentos contraditórios (PROC-042 vs PROC-042-v2).
- **AGENTS.md** (resumo do cenário 2): TS strict · Zod para validação de input · pino para logging (nunca `console.log`) · nunca logar dados pessoais (e-mail, nome) · imports estáticos no topo (nunca `require` dinâmico).
- **Guardrails de produto** formalizados pelo PS no cenário 2 (DEVE / NÃO DEVE) — este código é a materialização determinística de 2 deles.
- **POL-001 §3.2** (Anexo A) — fonte de verdade da negativa de carga perigosa (classes 1–6 ANTT).

## Entregáveis e rastreabilidade ao rubrik

### Ex. 3.1 — Structured output e verificações determinísticas
| Entregável | Path | Critério atendido |
|---|---|---|
| Schema Zod (answer, source_document, confidence_score) | `src/services/response-validator.ts` | Schema válido com campos obrigatórios e tipos corretos |
| Guardrail 1 (source_document obrigatório) | `src/services/response-validator.ts` | Bloqueia resposta sem fonte e retorna mensagem padrão |
| Guardrail 2 (carga perigosa + devolução) | `src/services/response-validator.ts` | Detecta a combinação e bloqueia se não houver negativa |
| Testes que provam o bloqueio | `tests/unit/response-validator.test.ts` | Guardrails realmente bloqueiam (não só logam) |
| Code review + correções | `docs/entrega/cenario-3/dev-3.1-structured-output-harness.md` | 2+ problemas reais (campos extras, regex frágil) corrigidos |
| Probabilístico vs determinístico | `docs/entrega/cenario-3/dev-3.1-structured-output-harness.md` §Conceito | Distinção clara entre prompt e código |

### Ex. 3.2 — Revisão crítica de código gerado por IA
| Entregável | Path | Critério atendido |
|---|---|---|
| Revisão própria (antes do Claude) | `docs/entrega/cenario-3/dev-3.2-revisao-codigo-ia.md` §1 | 4 armadilhas identificadas independentemente (D4) |
| Revisão do Claude + comparação | `docs/entrega/cenario-3/dev-3.2-revisao-codigo-ia.md` §2–3 | Comparação honesta humano vs Claude |
| Validação de input (Zod) | `src/functions/feedback/validator.ts` | `as any` substituído por Zod estrito |
| Persistência desacoplada (import estático) | `src/functions/feedback/repository.ts` | `require` dinâmico → import estático + injeção |
| Handler reescrito | `src/functions/feedback/handler.ts` | Segue o AGENTS.md integralmente (Zod, pino, sem e-mail em log) |
| Testes do feedback | `tests/unit/feedback-validator.test.ts` | Reescrita comprovada |

## Verification criteria da entrega
- **VC-A:** `npx tsc -p . --noEmit` retorna exit 0 (TS strict).
- **VC-B:** `npx vitest run` passa, incluindo testes que provam G1, G2 e a validação de feedback.
- **VC-C:** Nenhum `console.log`, `as any`, ou `require(` dinâmico no código entregue (`grep` limpo).
- **VC-D:** `attendantEmail` nunca aparece em log (verificado por inspeção + redaction do pino).
- **VC-E:** Arquivos nos paths exatos do Anexo C (`src/services/response-validator.ts`, `src/functions/feedback/handler.ts`).
- **VC-F:** Artefatos referenciam ADR-0002/0003, AGENTS.md e POL-001 §3.2.
