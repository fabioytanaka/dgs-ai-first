# Dev 3.1 — Structured output e verificações determinísticas (harness de código)

> **Tópico:** Harness Engineering · **Ferramentas:** GitHub Copilot (geração) + Claude (code review)
> **Artefatos:** [response-validator.ts](../../../src/services/response-validator.ts) · [response-validator.test.ts](../../../tests/unit/response-validator.test.ts)

## Conceito — por que código determinístico complementa o prompt probabilístico

O system prompt **pede** ao modelo: "cite sempre a fonte" e "carga perigosa não pode ser devolvida". Isso é **probabilístico** — o modelo acerta na maioria das vezes, mas pode esquecer (foi exatamente o que produziu os 12% de respostas erradas no teste interno). O harness de código é **determinístico**: o que o schema exige, o modelo **tem** de entregar; o que o guardrail proíbe, **não passa**, independentemente do humor do modelo.

| Camada | Mecanismo | Garantia |
|---|---|---|
| Prompt | "inclua a fonte" | Probabilística — pode falhar silenciosamente |
| Structured output (Zod) | `source_document` obrigatório no schema | Determinística — sem fonte → rejeitado |
| Guardrail de conteúdo | regex carga perigosa + devolução | Determinística — afirmação indevida → bloqueada |

A ordem importa: **valida-se o schema antes do conteúdo**. Se o JSON não bate com o contrato, rejeita-se antes de gastar lógica analisando o texto (`validateResponse`, passo 1 → passo 2).

## Schema do structured output

```ts
export const structuredOutputSchema = z
  .object({
    answer: z.string().trim().min(1).max(4000),
    source_document: z.string().trim().min(1),   // G1 por construção
    confidence_score: z.number().min(0).max(1),
  })
  .strict();
```

## Os 2 guardrails

- **G1 — `source_document` obrigatório.** Garantido pelo próprio schema: `.min(1)` após `.trim()`. Resposta sem fonte (ou com fonte em branco) **falha o parse** e `validateResponse` retorna `SAFE_FALLBACK` — a mensagem padrão de escalonamento humano. Não apenas loga: **substitui** a resposta.
- **G2 — carga perigosa + devolução exige a negativa (POL-001 §3.2).** Quando a resposta menciona `carga(s) perigosa(s)` **e** termos de devolução, ela é **bloqueada** se afirmar que a devolução é possível, ou se **omitir** a negativa. Fundamento de negócio: cargas perigosas classes 1–6 da ANTT não são devolvíveis pelo processo padrão.

> **Bloqueia, não loga** (regra de corte D3 ≤ 2 do Foundation): `validateResponse` sempre devolve `{ ok: false, response: SAFE_FALLBACK }` na falha. O teste [`response-validator.test.ts`](../../../tests/unit/response-validator.test.ts) prova que a resposta ruim **não passa** (`expect(outcome.response).toEqual(SAFE_FALLBACK)`).

## Code review do output do Copilot (ciclo gerar → avaliar → corrigir)

O Copilot, ao gerar a primeira versão, produziu um schema e um guardrail ingênuos. Abaixo a v1 (literal do que ele sugeriu) e os problemas **reais** que o Claude e eu identificamos no code review, com a correção aplicada na versão final.

### v1 gerada pelo Copilot (antes da revisão)

```ts
// schema v1 — Copilot
const schema = z.object({
  answer: z.string(),
  source_document: z.string(),
  confidence_score: z.number(),
});

// guardrail v1 — Copilot
if (answer.includes("carga perigosa") && answer.includes("devolução") && answer.includes("pode")) {
  return fallback; // bloqueia
}
```

### Problemas reais identificados e corrigidos

| # | Problema (v1) | Por que é real | Correção (versão final) |
|---|---|---|---|
| 1 | `z.object` **sem `.strict()`** | Aceita campos extras: um modelo pode injetar chaves inesperadas que passam pela validação silenciosamente | `.strict()` rejeita qualquer chave fora do contrato |
| 2 | `source_document: z.string()` | `""` (string vazia) passa → G1 burlado: fonte "presente" mas em branco | `.trim().min(1)` |
| 3 | `confidence_score: z.number()` | Aceita `7` ou `-3` — score fora de faixa contamina a lógica de baixa confiança/HITL a jusante | `.min(0).max(1)` |
| 4 | Regex G2 `.includes("pode")` | **Trivialmente burlável e com falso-positivo:** "**não** pode" contém "pode" (bloquearia a resposta CORRETA), e "é possível devolver" não contém "pode" (deixaria a afirmação errada passar). Sensível a acento/caixa: "Devolução"/"devolucao"/"Cargas Perigosas" escapam | Normalização (lowercase + remoção de diacríticos), regex de stem (`cargas? perigosas?`, `devolu\w*`), detecção de negativa, e **look-behind** `(?<!nao\s)` para não confundir "não podem ser devolvidas" (correto) com afirmação |

O problema #4 só apareceu **ao escrever o teste**: a primeira versão do meu próprio regex de afirmação casava "não podem ser devolvidas" e bloqueava a resposta compliant da POL-001. O teste `allows the compliant negative answer` falhou (`expected true, received false`), expondo o bug. Corrigi com o look-behind. Isso reforça o ponto: **o teste é parte do harness** — sem ele, o guardrail "parecia" certo.

## Evidência de execução real

```
$ npx tsc -p . --noEmit
TSC_EXIT=0                                  # strict:true, zero erros

$ npx vitest run
 ✓ tests/unit/query-validator.test.ts      (4 tests)
 ✓ tests/unit/feedback-validator.test.ts   (6 tests)
 ✓ tests/unit/response-validator.test.ts   (12 tests)
 Test Files  3 passed (3)
      Tests  22 passed (22)
```

Os 12 testes do validator cobrem: schema válido; rejeição de campo extra (`.strict`); `source_document` em branco (G1); `confidence_score` fora de [0,1]; G1 sem fonte → `SAFE_FALLBACK`; input lixo/`null` sem lançar exceção; G2 negativa compliant **permitida**; G2 afirmação indevida **bloqueada**; G2 combo sem negativa **bloqueado**; robustez a acento/caixa; e ausência de over-block para devolução de carga comum.

## Fronteira de escopo (consciente)
Não implementei lookup de fonte contra a lista de documentos válidos (`POL-001`, `PROC-042`, …) — isso é o **exercício do Tech Lead 3.1**, não do Dev. Também não implementei lookup table de valores de frete: a nota de calibração da avaliação pede explicitamente para **não** penalizar sua ausência.
