# 06 — Runbook: fechar as evidências residuais (Windows / PowerShell)

> Estes passos são **opcionais** (a nota já está em 3.0), mas tornam as evidências 100% literais.
> Execute na raiz do repo: `C:\Users\fabio.tanaka\AI First\DGS\Desafios\dgs-ai-first\contexto\novatech-assistant`.
> Salve cada saída/print em `docs/entrega/evidencias/` (crie a pasta).

---

## Parte A — `git` MCP server via `uvx` (o único que faltou subir)

Os 4 servers `npx` (filesystem ×2, memory, everything) já sobem com handshake MCP — comprovado por `scripts/mcp-smoke.mjs`. O `git` reference server é Python e roda via `uvx`.

### A.1 Instalar o `uv` (traz o `uvx`)
```powershell
# Opção 1 — winget (recomendado)
winget install --id=astral-sh.uv -e

# Opção 2 — instalador oficial (se não tiver winget)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Feche e reabra o terminal, depois confirme:
uv --version
uvx --version
```

### A.2 Subir o git server e fazer o handshake (smoke test)
```powershell
# O mcp.json já tem o server "git". Rode o smoke só contra ele:
node scripts/mcp-smoke.mjs git
```
**Saída esperada** (algo como):
```
## git — OK
   serverInfo: mcp-server-git vX.Y.Z
   tools (...): git_status, git_log, git_diff, git_show, git_add, git_commit, ...
```
> Salve essa saída em `docs/entrega/evidencias/git-server-smoke.txt`.

### A.3 (Opcional) Provar leitura de histórico via a tool do server
Se for usar o server num agente (Claude Code/Copilot), peça: *"use a tool `git_log` para listar o último commit"*. O resultado esperado bate com:
```
bbdd03a chore: starter repo (Anexo D) — estrutura + dados semeados dos Anexos A e B
```

### A.4 Rodar o smoke completo (os 5 servers de uma vez)
```powershell
node scripts/mcp-smoke.mjs   # sem argumentos = todos
```
> Salve em `docs/entrega/evidencias/mcp-smoke-completo.txt`.

---

## Parte B — Rodada real com o GitHub Copilot (output bruto da v1)

Objetivo: capturar o que o Copilot gera **antes** da sua reescrita, tornando o ciclo gerar→avaliar→reescrever literal (já documentado em `dev-2.2-revisao-critica.md`).

### B.1 Preparar o ambiente
1. Abra o repo no **VS Code** com a extensão **GitHub Copilot** ativa.
2. Garanta que o `AGENTS.md` e `skills/foundation/typescript-conventions.md` estão no repo (já estão) — o Copilot Chat os lê como contexto.

### B.2 Gerar a primeira task com o Copilot (capturar a V1)
1. **Antes**, guarde a versão atual (a sua, já revisada):
   ```powershell
   Copy-Item src/functions/query/handler.ts docs/entrega/evidencias/handler-revisado.ts
   ```
2. No **Copilot Chat**, com `specs/query-endpoint/tasks.md` aberto, peça:
   > "Implemente a task **T-06** de `specs/query-endpoint/tasks.md`: o HTTP trigger do query endpoint em `src/functions/query/handler.ts`, seguindo `plan.md` e o `AGENTS.md`."
3. **Sem editar nada**, copie o bloco que o Copilot gerou e salve:
   `docs/entrega/evidencias/handler-copilot-v1.ts`
4. Tire um **print** do Copilot Chat mostrando a geração → `docs/entrega/evidencias/copilot-v1.png`.

### B.3 Avaliar e documentar o diff
```powershell
# Diferença entre a V1 do Copilot e a sua versão revisada:
git diff --no-index docs/entrega/evidencias/handler-copilot-v1.ts src/functions/query/handler.ts `
  > docs/entrega/evidencias/diff-v1-vs-revisado.txt
```
Confirme que os 3 problemas de `dev-2.2-revisao-critica.md` aparecem no diff (try/catch do JSON, `any`+stack leak, `console.log`/`authLevel`). Se o seu Copilot gerar problemas **diferentes**, atualize a seção de revisão crítica com os reais — honestidade vale ponto em D4.

### B.4 Validar a versão final
```powershell
npx tsc -p . --noEmit          # deve sair com exit 0
npx vitest run                 # deve passar
```
> Salve as duas saídas em `docs/entrega/evidencias/`.

---

## Checklist final de evidências
- [ ] `git-server-smoke.txt` (Parte A.2)
- [ ] `mcp-smoke-completo.txt` (Parte A.4) — os 5 servers OK
- [ ] `handler-copilot-v1.ts` + `copilot-v1.png` (Parte B.2)
- [ ] `diff-v1-vs-revisado.txt` (Parte B.3)
- [ ] saídas de `tsc` e `vitest` (Parte B.4)

Com isso, as 5 dimensões ficam blindadas em **3.0 — Aprovado com distinção**.
