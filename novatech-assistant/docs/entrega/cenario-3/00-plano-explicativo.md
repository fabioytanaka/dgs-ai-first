# 00 — Plano explicativo da tarefa (Desenvolvedor, Cenário 3)

> **Programa:** Trilha de Certificação AI First — DGS / DB1 Global Software
> **Papel:** Desenvolvedor · **Cenário-Âncora 3:** Fase de Governança e Validação
> **Escopo:** exercícios 3.1 (Harness Engineering) e 3.2 (Revisão Crítica de Outputs de IA)
> **Avaliação:** `avaliacao-desenvolvedor.md` + `avaliacao-foundation.md` (5 dimensões, escala 1–3).

## Quem sou eu neste cenário
Sou o **Desenvolvedor**. Nesta fase meu trabalho é **endurecer o harness em código** e **revisar criticamente o que a IA gerou**. A diferença entre protótipo e produção mora aqui: o pipeline de RAG já responde, mas 12% das respostas em teste interno estavam erradas (alucinação, doc desatualizado, chunk errado) e o módulo de feedback gerado pelo Copilot violou o `AGENTS.md`. Eu transformo guardrails de produto (DEVE/NÃO DEVE) em código **determinístico** que de fato **bloqueia** respostas ruins — não só loga.

## O que a tarefa pede (2 exercícios)

- **3.1 — Structured output + verificações determinísticas (harness de código):**
  1. Definir o **schema Zod** do structured output (`answer`, `source_document`, `confidence_score`).
  2. Implementar `src/services/response-validator.ts` que valida a resposta contra o schema e aplica **2 guardrails**:
     - *G1:* toda resposta DEVE conter `source_document` — senão é **rejeitada** e substituída por mensagem padrão.
     - *G2:* respostas que mencionam **"carga perigosa" + "devolução"** DEVEM conter a **negativa** — se afirmarem que a devolução é possível, são **bloqueadas**.
  3. Fazer um **code review** do que o Copilot gerou: achar 2+ problemas reais (schema aceita campos extras? regex cobre variações?) e corrigir.

- **3.2 — Revisão crítica de código gerado por IA:**
  1. Revisar **por conta própria, ANTES do Claude**, o `feedback-handler.ts` gerado pelo Copilot e classificar cada problema (violação do `AGENTS.md`, segurança, bug).
  2. Usar o **Claude** como segundo revisor e **comparar** honestamente as listas.
  3. **Reescrever** o módulo em `src/functions/feedback/handler.ts` seguindo o `AGENTS.md` integralmente.

## Como vou atacar (e por quê)

1. **Determinístico complementa o probabilístico.** O prompt *pede* a fonte (probabilístico — o modelo pode esquecer). O schema Zod + os guardrails *exigem* a fonte e *bloqueiam* o que o prompt deixou passar (determinístico — não depende do humor do modelo). Essa distinção é o critério central do rubrik (D1) e o fio condutor da entrega.
2. **Bloquear, não logar.** A regra de corte é explícita: *"código que deveria bloquear mas só loga → D3 ≤ 2"*. Por isso `validateResponse` **retorna sempre a resposta segura** quando a validação falha, e eu **provo com teste** que a resposta inválida não passa.
3. **Provar com execução real.** `npx tsc -p . --noEmit` exit 0 + `npx vitest run` verde, com testes que exercitam cada guardrail (fonte ausente, fonte vazia, campo extra, afirmação indevida de devolução de carga perigosa, variações de acento/caixa).
4. **Revisão humana primeiro, depois IA.** O rubrik zera D4 se a análise própria estiver vazia ou for idêntica à da IA. Documento minha revisão **antes** de chamar o Claude e marco onde concordamos e onde divergimos.
5. **Ancorar no domínio NovaTech.** A negativa de G2 vem da **POL-001 §3.2** (cargas perigosas classes 1–6 da ANTT não são devolvíveis pelo processo padrão). Os padrões da reescrita vêm do `AGENTS.md` (TS strict, Zod, pino, sem PII em log, import estático).

## Fronteiras de escopo
- **Dentro:** os 2 guardrails pedidos, o schema, o code review, a reescrita do handler de feedback e os testes que comprovam o bloqueio.
- **Fora:** lookup table de valores numéricos de frete (a nota de calibração diz para **não** penalizar a ausência); a verificação de `source_document` contra a lista de docs válidos (isso é o **exercício do Tech Lead 3.1**, não do Dev — menciono a fronteira para não invadir escopo).

## Ordem de execução
schema + `response-validator.ts` → testes do validator → reescrita `feedback/{validator,repository,handler}.ts` → testes do feedback → `tsc` + `vitest` → docs (dev-3.1, dev-3.2) → autoavaliação.

## Mapa de entregáveis
Ver [`SPECIFICATION.md`](SPECIFICATION.md) (rastreabilidade entregável → path → critério). Detalhe do harness em [`dev-3.1-structured-output-harness.md`](dev-3.1-structured-output-harness.md); revisão crítica em [`dev-3.2-revisao-codigo-ia.md`](dev-3.2-revisao-codigo-ia.md); autoavaliação em [`05-autoavaliacao.md`](05-autoavaliacao.md).
