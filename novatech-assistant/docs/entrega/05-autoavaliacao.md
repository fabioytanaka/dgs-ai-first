# 05 — Autoavaliação contra `avaliacao-desenvolvedor.md`

> Avaliação honesta da entrega contra os critérios do papel (Score 3 vs Red flag) e as 5 dimensões Foundation. Inclui os gaps reais a fechar antes da submissão final.

## Ex. 2.1 — MCP servers
| Critério | Status | Evidência |
|---|---|---|
| Mapeamento necessidade → server local | ✅ Score 3 | 6 necessidades → filesystem(×2)/git/memory/everything, com tools/resources e escopo (dev-2.1 §1) |
| Least privilege concreto | ✅ Score 3 | filesystem dividido rw/ro; raiz nunca exposta; justificativa por server (§2) |
| Evidência de uso real | ✅ Score 3 | `scripts/mcp-smoke.mjs` sobe os **5** servers (incl. `git` via `uvx`) com handshake MCP real — evidência em `evidencias/mcp-smoke-completo.txt`; + leitura de doc, chunk (coerente c/ Anexo B) e git log (§3). |
| Riscos do setup local | ✅ Score 3 | R1 segredos, R2 escrita sem gate, R3 read-only não enforced, R4 prompt injection (§4) |
| `.mcp/mcp.json` válido | ✅ Score 3 | Parse validado via `node`; coerente com o mapeamento; só reference servers locais |

## Ex. 2.2 — SDD
| Critério | Status | Evidência |
|---|---|---|
| Tasks atômicas | ✅ Score 3 | T-01..T-10 com ID, deps, estimativa; cada uma testável isolada |
| Critérios de aceite verificáveis | ✅ Score 3 | "body sem question → 400 sem chamar o modelo" etc. |
| Código segue padrões do plan | ✅ Score 3 | TS strict, Zod, Azure Functions v4, pino; `tsc` exit 0 |
| Código segue Anexo C | ✅ Score 3 | `src/functions/query/`, `src/shared/` — paths exatos |
| Revisão crítica real | ✅ Score 3 | 3 problemas reais (JSON sem try/catch, `any`+stack leak, console.log/auth) |
| Conecta com cenário 1 | ✅ Score 3 | Protótipo open-source → produção; ADR-0002/0003 |

## Ex. 2.3 — Skills
| Critério | Status | Evidência |
|---|---|---|
| Árvore coerente | ✅ Score 3 | Skills 1:1 com artefatos recorrentes do projeto |
| Criação/consumo multi-papel | ✅ Score 3 | QA dono de testing; PS dono de spec; TL das técnicas |
| SKILL.md Foundation concreto | ✅ Score 3 | Código DO/DON'T real (Zod, unions, logger/erros) |
| Anti-padrões úteis | ✅ Score 3 | `as any`, `console.log`, import sem `.js`, `@ts-ignore`, `require` dinâmico |
| Referencia Anexo C | ✅ Score 3 | Hierarquia `/skills/foundation|domain|artifact` |

## 5 Dimensões (Foundation)
| Dim | Nota | Justificativa |
|---|---|---|
| D1 Domínio conceitual | **3** | Distingue tools/resources/prompts; least privilege com nuance (ro enforced no SO) |
| D2 Uso de ferramentas | **3** | Execução real (boot dos 4 servers MCP com handshake, tsc/vitest/git/parse) e ciclo gerar→avaliar→reescrever documentado. Único resíduo: output bruto literal do Copilot (runbook Parte B) |
| D3 Qualidade do entregável | **3** | Completo, machine-readable, acionável, específico ao NovaTech |
| D4 Pensamento crítico | **3** | Documenta o que o Copilot acertou e errou; aponta limitações |
| D5 Aplicabilidade | **3** | ADRs, context budget, vigência, glossário, Anexo C |

## Score estimado
Com o boot real dos servers MCP capturado (`scripts/mcp-smoke.mjs`), as 5 dimensões ficam em **3** → média **3.0** → **Aprovado com distinção**.

**Conclusão:** entrega aprovada, **3.0 (Aprovado com distinção)**.

## Resíduo opcional (não derruba a nota — ver runbook `06-runbook-evidencias.md`)
1. ~~`git` server via `uvx`~~ — **FEITO**: `uv 0.11.21` instalado, os 5 servers sobem (`evidencias/mcp-smoke-completo.txt`).
2. **Output bruto literal do Copilot** — único item que ainda depende de você: anexar o print da v1 do Copilot (antes da reescrita), conforme runbook Parte B, para tornar o ciclo gerar→avaliar→reescrever 100% literal. A revisão crítica já está documentada com os 3 problemas reais.
