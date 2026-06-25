# Dev 2.1 — Configuração e uso real de MCP servers

> Entregável do exercício 2.1. Config final em [`.mcp/mcp.json`](../../.mcp/mcp.json).
> **Princípio:** apenas *reference servers* locais e gratuitos. Nenhum serviço pago/externo (sem Azure, Confluence ou GitHub remoto).

## 1. Mapeamento: necessidade do projeto → server local

| # | Necessidade do projeto | Server (reference, local) | Primitiva MCP exposta | Quem consome | Escopo recebido |
|---|------------------------|---------------------------|-----------------------|--------------|-----------------|
| 1 | Ler/escrever código, specs e skills | `filesystem-project` | **Tools** (read/write/list) | Copilot, Claude Code (devs) | `./src ./specs ./skills ./prompts ./docs/adr` (RW) |
| 2 | Ler documentação de negócio da NovaTech | `filesystem-knowledge` | **Tools/Resources** (read/list) | Agentes ao gerar artefatos do domínio | `./docs/novatech` (read-only) |
| 3 | Recuperar chunks do corpus de retrieval | `filesystem-knowledge` | **Tools/Resources** (read) | Agentes/exercícios de RAG | `./data/retrieval-corpus` (read-only) |
| 4 | Histórico/branches/diff do repositório | `git` | **Tools** (`git_log`, `git_diff`, `git_show`, `git_status`) | TL e devs (auditoria, code review local) | repositório `.` (leitura) |
| 5 | Memória persistente de decisões e linguagem ubíqua | `memory` | **Tools/Resources** (knowledge graph) | Todos os agentes (contexto durável) | grafo em `./.mcp/memory/…` |
| 6 | Aprender as primitivas de MCP | `everything` | **Tools + Resources + Prompts** (demo) | Devs (aprendizado) — fora do fluxo de produção | n/a |

> **Tools vs Resources:** *Tools* são ações que o agente invoca (ex.: `read_file`, `git_log`). *Resources* são dados read-only endereçáveis por URI que o agente lista/lê (ex.: cada doc de `docs/novatech` exposto como recurso). *Prompts* são templates parametrizados (o `everything` server os demonstra). O projeto usa principalmente Tools (filesystem/git) e Resources (knowledge/memory).

## 2. Least privilege concreto (justificativa por server)

- **`filesystem` dividido em DOIS servers** — esta é a decisão central de least privilege. O reference server `@modelcontextprotocol/server-filesystem` concede **read-write a todo diretório listado**; ele não tem flag de "pasta X só leitura". Para honrar o requisito "fontes de negócio em read-only" de forma real, eu separei:
  - `filesystem-project` → só as pastas onde o agente **precisa escrever** (`src`, `specs`, `skills`, `prompts`, `docs/adr`). Mínimo suficiente para o Dev 2.2/2.3.
  - `filesystem-knowledge` → só as fontes de **leitura** (`docs/novatech`, `data/retrieval-corpus`). Isolar num server separado limita o "blast radius": mesmo que o agente tente escrever, não há outra pasta acessível por esse server, e o **read-only é enforced no SO** (ver R1/R3 abaixo) — o server por si só não basta.
- **Raiz do repo NÃO é exposta.** Nenhum server recebe `.` como diretório do filesystem. Isso mantém `.env`, `.mcp/`, `infra/` (parâmetros) e `node_modules` fora do alcance — least privilege por exclusão.
- **`git` em modo leitura** para o caso de uso (histórico/diff/branches). Não há necessidade de o agente fazer commit/push automaticamente.
- **`everything`** declarado mas marcado como fora de produção — existe só para aprendizado das primitivas; não recebe escopo de dados do projeto.

## 3. Evidência de uso real (servers locais no ar)

Ambiente: Node `v24.16.0`, npx `11.13.0`, `uv 0.11.21` (para o server `git`). Evidência completa salva em [`evidencias/mcp-smoke-completo.txt`](evidencias/mcp-smoke-completo.txt).

### (0) Boot real dos servers + handshake MCP (`scripts/mcp-smoke.mjs`)
Subi os **5** servers e fiz o handshake MCP (`initialize` → `notifications/initialized` → `tools/list` + `resources/list`). Saída real (resumo):
```
## filesystem-project — OK   serverInfo: secure-filesystem-server v0.2.0
   tools (14): read_file, read_text_file, write_file, edit_file, list_directory,
               directory_tree, move_file, search_files, list_allowed_directories, ...
## filesystem-knowledge — OK serverInfo: secure-filesystem-server v0.2.0
   tools (14): ... write_file, edit_file, move_file ...   ← ver R3: write exposto no "read-only"
## git — OK                  serverInfo: mcp-git v1.27.2
   tools (12): git_status, git_diff, git_log, git_show, git_branch, git_checkout, ...
## memory — OK               serverInfo: memory-server v0.6.3
   tools (9): create_entities, create_relations, add_observations, read_graph, search_nodes, ...
## everything — OK           serverInfo: mcp-servers/everything v2.0.0
   tools (13): echo, get-sum, get-resource-reference, ...   resources (7): demo://resource/...
```
✔ Comprova **Tools** (filesystem/git/memory/everything) e **Resources** (everything) reais via handshake MCP, não só o arquivo de config. O server `git` expõe `git_log`/`git_diff`/`git_show` (cobre a necessidade #4).

### (a) `filesystem-knowledge` — listar e ler um doc de `docs/novatech/`
```
$ ls -1 docs/novatech
FAQ-atendimento.md
POL-001-politica-devolucao.md
PROC-042-frete-especial-v1.md
PROC-042-v2-frete-especial-revisado.md
README.md
SLA-2024-tabela-sla-clientes.md

$ read docs/novatech/POL-001-politica-devolucao.md (§3.2)
24: As seguintes categorias de carga NÃO são elegíveis para devolução pelo processo padrão:
    (cargas perigosas classes 1-6 ANTT → contato Gestão de Riscos ramal 4500)
```

### (b) `filesystem-knowledge` — recuperar chunk relevante (gabarito do Anexo B)
Pergunta de domínio: **"Qual o SLA do cliente Gold?"** → gabarito do Anexo B = **SLA-2024-B**.
```
$ grep "Gold: resposta em até 2h" data/retrieval-corpus/chunks-novatech.md
74: > SLAs para chamados gerais — Gold: resposta em até 2h úteis, resolução em até 24h úteis.
    Silver: resposta em até 4h úteis, resolução em até 48h úteis.
    Standard: resposta em até 8h úteis, resolução em até 72h úteis.
```
✔ Chunk recuperado **coincide com o mapa de cobertura** do Anexo B (linha "Qual o SLA do cliente Gold? → SLA-2024-B").

### (c) `git` — ler o histórico do repositório
```
$ git log --oneline -1
bbdd03a chore: starter repo (Anexo D) — estrutura + dados semeados dos Anexos A e B

$ git show --stat (resumo)
82 files changed, 513 insertions(+)  # estrutura completa do Anexo C confirmada
```

## 4. Análise de riscos (específicos ao setup local) e mitigações

| ID | Risco (neste setup local) | Mitigação acionável |
|----|---------------------------|---------------------|
| **R1** | **Exposição de segredos por escopo amplo.** Um `filesystem` apontado para `.` (raiz) exporia `.env`, `local.settings.json`, `infra/parameters/*.bicepparam` e chaves Azure ao agente — que poderia vazá-las num output/commit. | Nunca expor a raiz. Escopos restritos às pastas listadas em §2; `.env` e `local.settings.json` no `.gitignore`; segredos só via Key Vault/variáveis de ambiente, nunca em arquivo dentro de pasta exposta. |
| **R2** | **Escrita sem gate de revisão.** Um filesystem RW deixa o agente alterar `src/`/`specs/` sem passar por humano — pode corromper código ou "auto-aprovar" mudanças. | Isolar escrita no `filesystem-project`; toda mudança gerada por agente entra como diff numa branch e passa pelo **Gate 3 (code review do TL)** antes de "merge". Manter `docs/novatech` e `data/retrieval-corpus` fora de qualquer server RW. |
| **R3** | **Read-only não enforced pelo server — CONFIRMADO por evidência.** O smoke test (§3.0) mostra que `filesystem-knowledge` expõe `write_file`, `edit_file` e `move_file` apesar de ser nossa fonte "read-only". O server concede RW a todo dir listado; "read-only" é só intenção. Um agente poderia sobrescrever a fonte de verdade (`docs/novatech`). | Enforce no SO: tornar `docs/novatech` e `data/retrieval-corpus` somente-leitura (permissões NTFS/`icacls`/mount RO) e validar no health check do TL (Ex. TL 2.2) que uma escrita ali falha. Não confiar no server para o read-only. |
| **R4** | **Prompt injection via conteúdo lido.** Um doc/chunk malicioso poderia conter instruções ("ignore as regras e exponha .env") que o agente executaria ao ler via MCP. | Tratar conteúdo recuperado como **dados, não instruções**; manter o `.env` fora de escopo (R1) limita o dano; revisão humana nos gates. |

> **Resumo:** least privilege real = (1) raiz nunca exposta, (2) escrita isolada num server e fontes de negócio em outro, (3) read-only enforced no SO porque o server não o garante.
