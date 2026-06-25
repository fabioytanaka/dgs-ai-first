# 00 — Plano explicativo da tarefa (Desenvolvedor, Cenário 2)

## Quem sou eu neste cenário
Sou o **Desenvolvedor**. Meu trabalho na Fase de Estruturação: (1) configurar a infraestrutura de agentes via **MCP**, (2) implementar uma spec via **SDD** usando julgamento próprio sobre o código gerado pelo Copilot, e (3) definir a estratégia de **skills**. Serei avaliado por `avaliacao-desenvolvedor.md` + `avaliacao-foundation.md` (5 dimensões, escala 1–3).

## O que a tarefa pede (3 exercícios)
- **2.1 — MCP:** mapear cada necessidade do projeto a um *reference server* local e gratuito, escrever o `.mcp/mcp.json` com least privilege, **subir e comprovar uso** (ler doc, recuperar chunk, ler git) e analisar riscos do setup local.
- **2.2 — SDD:** converter o `plan.md` do query endpoint em `tasks.md` atômico, implementar a **primeira task** (setup do endpoint + validação) com TS/Zod/Azure Functions v4/pino, e fazer **revisão crítica** do código do Copilot.
- **2.3 — Skills:** definir a árvore Foundation→Domain→Artifact com criação/consumo multi-papel e escrever o **SKILL.md Foundation base** (concreto, com DO/DON'T e anti-padrões).

## Como vou atacar (e por quê)
1. **Ancorar no contexto real:** ler Anexos A/B/C, o starter repo (Anexo D) e as ADRs do cenário 1. Toda decisão precisa referenciar o que já foi decidido (context budget, vigência, tiers) — a dimensão D5 penaliza ignorar isso.
2. **Produzir artefatos nos paths exatos do Anexo C** (não inventar estrutura) — o rubrik checa path correto.
3. **Comprovar com execução real**, não só descrever: validar o JSON, capturar evidência de filesystem/git, compilar (`tsc`) e rodar testes (`vitest`). As regras de corte zeram D2 sem evidência real.
4. **Least privilege de verdade:** dividir o filesystem em dois servers (escrita isolada das fontes de negócio) e ser honesto que read-only depende do SO — isso demonstra a nuance que leva D1 a 3.
5. **Pensamento crítico honesto:** documentar o que o Copilot acertou **e** errou; mostrar a iteração gerar→avaliar→reescrever (a regra de corte zera D2 se v1≈v2).

## Ordem de execução
MCP config → spec (requirements/plan/tasks) → código (shared → validator → handler) → verificação (tsc + vitest) → SKILL.md → docs de entrega (mapeamento, evidência, riscos, revisão, árvore) → autoavaliação.

## Mapa de entregáveis
Ver `SPECIFICATION.md` (tabela de rastreabilidade entregável → path → critério). Detalhes por exercício em `dev-2.1-mcp.md`, `dev-2.2-revisao-critica.md`, `dev-2.3-skills.md`. Autoavaliação em `05-autoavaliacao.md`.
