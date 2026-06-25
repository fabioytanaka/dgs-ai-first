# SPECIFICATION.md — Entrega do Desenvolvedor (Cenário 2)

> **Programa:** Trilha de Certificação AI First — DGS / DB1 Global Software
> **Papel:** Desenvolvedor · **Cenário-Âncora 2:** Fase de Estruturação do Trabalho
> **Escopo:** exercícios 2.1 (MCP), 2.2 (SDD), 2.3 (Skills)
> **Repositório-alvo:** `novatech-assistant` (estrutura do Anexo C)

Este documento é a spec da própria entrega: define **o que** será produzido, **onde** (paths do Anexo C), e **como cada item satisfaz** os critérios de `avaliacao-desenvolvedor.md`. É o contrato verificável entre a tarefa e a avaliação.

## Outcomes
1. Infraestrutura de agentes (MCP) configurada com least privilege e **uso comprovado**.
2. Uma spec do query endpoint implementada via SDD (plan → tasks → código) com **código que compila e testa**.
3. Estratégia de skills definida com uma skill Foundation concreta e prescritiva.

## Scope boundaries
- **Dentro:** os 3 exercícios do papel Desenvolvedor e seus artefatos.
- **Fora:** exercícios de outros papéis (DM, PS, TL, QA); deploy real em Azure; implementação das tasks T-07..T-10 (fora da "primeira task").

## Prior decisions (cenário 1 — respeitadas em toda a entrega)
- ADR-0001 Azure OpenAI GPT-4o · ADR-0002 context budget (~4K system + ~8K chunks, histórico ≤ 3 turnos) · ADR-0003 documentos contraditórios (vigência) · ADR-0004 Azure AI Search + lição do protótipo open-source.

## Entregáveis e rastreabilidade ao rubrik

### Ex. 2.1 — MCP
| Entregável | Path | Critério atendido |
|---|---|---|
| Mapeamento necessidade→server | `docs/entrega/dev-2.1-mcp.md` §1 | Mapeamento necessidade → server local |
| `.mcp/mcp.json` final | `.mcp/mcp.json` | `.mcp/mcp.json` válido e coerente |
| Least privilege | `docs/entrega/dev-2.1-mcp.md` §2 | Least privilege concreto |
| Evidência de execução | `docs/entrega/dev-2.1-mcp.md` §3 | Evidência de uso real |
| Riscos + mitigações | `docs/entrega/dev-2.1-mcp.md` §4 | Riscos de segurança do setup local |

### Ex. 2.2 — SDD
| Entregável | Path | Critério atendido |
|---|---|---|
| tasks atômicas | `specs/query-endpoint/tasks.md` | Tasks atômicas; critérios de aceite verificáveis |
| código (1ª task) | `src/functions/query/{handler,validator}.ts`, `src/shared/*` | Código segue padrões do plan + Anexo C |
| revisão crítica | `docs/entrega/dev-2.2-revisao-critica.md` | Revisão crítica real; conecta com cenário 1 |

### Ex. 2.3 — Skills
| Entregável | Path | Critério atendido |
|---|---|---|
| árvore + mapeamento | `docs/entrega/dev-2.3-skills.md` | Árvore coerente; criação/consumo multi-papel; referencia Anexo C |
| SKILL.md Foundation | `skills/foundation/typescript-conventions.md` | SKILL.md Foundation concreto; anti-padrões úteis |

## Verification criteria da entrega
- VC-A: `.mcp/mcp.json` parseia (validado via `node`) e usa só reference servers locais.
- VC-B: evidência real de leitura de doc, recuperação de chunk (coerente com o gabarito do Anexo B) e leitura do git.
- VC-C: `npx tsc -p . --noEmit` retorna exit 0; `npx vitest run` passa.
- VC-D: arquivos nos paths exatos do Anexo C.
- VC-E: artefatos referenciam ADRs do cenário 1 e a linguagem ubíqua do domínio.
