// MCP smoke test — sobe cada server do .mcp/mcp.json, faz o handshake
// (initialize + initialized) e lista as primitivas (tools/resources).
// Serve como EVIDÊNCIA de boot real dos servers e como base do health check.
//
// Uso:
//   node scripts/mcp-smoke.mjs            # testa todos os servers
//   node scripts/mcp-smoke.mjs filesystem-project memory   # só os listados
//
// Transporte MCP stdio = JSON-RPC 2.0 delimitado por newline.

import { spawn } from "node:child_process";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const cfg = JSON.parse(readFileSync(resolve(root, ".mcp/mcp.json"), "utf8"));
const only = process.argv.slice(2);
const PROTOCOL = "2024-11-05";
const TIMEOUT_MS = 60000;

function rpc(id, method, params) {
  return JSON.stringify({ jsonrpc: "2.0", id, method, params }) + "\n";
}
function note(method, params) {
  return JSON.stringify({ jsonrpc: "2.0", method, params }) + "\n";
}

function probe(name, server) {
  return new Promise((done) => {
    const child = spawn(server.command, server.args ?? [], {
      cwd: root,
      env: { ...process.env, ...(server.env ?? {}) },
      stdio: ["pipe", "pipe", "pipe"],
      shell: process.platform === "win32",
    });

    const result = { name, ok: false, serverInfo: null, tools: [], resources: [], error: null };
    let gotTools = false, gotResources = false;
    let buf = "";
    const timer = setTimeout(() => finish("timeout após 20s"), TIMEOUT_MS);

    function finish(err) {
      clearTimeout(timer);
      if (err) result.error = err;
      try { child.kill(); } catch {}
      done(result);
    }

    child.on("error", (e) => finish(`spawn falhou: ${e.message}`));
    child.stderr.on("data", () => {}); // logs do server vão p/ stderr; ignorar

    child.stdout.on("data", (d) => {
      buf += d.toString();
      let nl;
      while ((nl = buf.indexOf("\n")) >= 0) {
        const line = buf.slice(0, nl).trim();
        buf = buf.slice(nl + 1);
        if (!line) continue;
        let msg;
        try { msg = JSON.parse(line); } catch { continue; }
        handle(msg);
      }
    });

    function send(s) { child.stdin.write(s); }
    function maybeFinish() { result.ok = true; finish(null); }

    function handle(msg) {
      if (msg.id === 1 && msg.result) {
        result.serverInfo = msg.result.serverInfo ?? null;
        send(note("notifications/initialized", {}));
        send(rpc(2, "tools/list", {}));
        send(rpc(3, "resources/list", {}));
      } else if (msg.id === 2) {
        result.tools = (msg.result?.tools ?? []).map((t) => t.name);
        gotTools = true;
        if (gotResources) maybeFinish();
      } else if (msg.id === 3) {
        result.resources = (msg.result?.resources ?? []).map((r) => r.uri ?? r.name);
        gotResources = true;
        if (gotTools) maybeFinish();
      }
    }

    send(rpc(1, "initialize", {
      protocolVersion: PROTOCOL,
      capabilities: {},
      clientInfo: { name: "novatech-mcp-smoke", version: "0.1.0" },
    }));
  });
}

const entries = Object.entries(cfg.mcpServers).filter(([n]) => only.length === 0 || only.includes(n));
console.log(`# MCP smoke test — ${entries.length} server(s)\n`);
for (const [name, server] of entries) {
  const r = await probe(name, server);
  const status = r.ok ? "OK" : "FALHOU";
  console.log(`## ${name} — ${status}`);
  console.log(`   command: ${server.command} ${(server.args ?? []).join(" ")}`);
  if (r.serverInfo) console.log(`   serverInfo: ${r.serverInfo.name} v${r.serverInfo.version}`);
  if (r.tools.length) console.log(`   tools (${r.tools.length}): ${r.tools.join(", ")}`);
  if (r.resources.length) console.log(`   resources (${r.resources.length}): ${r.resources.slice(0, 6).join(", ")}${r.resources.length > 6 ? " …" : ""}`);
  if (r.error) console.log(`   erro: ${r.error}`);
  console.log("");
}
