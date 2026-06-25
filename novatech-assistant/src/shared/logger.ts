// Structured logging with pino. AGENTS.md / ADR: never use console.log.
// The full user question is redacted at info level to avoid persisting PII in logs.

import pino from "pino";

export const logger = pino({
  level: process.env.LOG_LEVEL ?? "info",
  redact: {
    // Defense in depth: even if a caller forgets, these PII fields are censored.
    // attendantEmail/comment come from the feedback endpoint (Cenário 3, Ex. 3.2).
    paths: [
      "question",
      "*.question",
      "history",
      "*.history",
      "attendantEmail",
      "*.attendantEmail",
      "comment",
      "*.comment",
    ],
    censor: "[redacted]",
  },
  base: { service: "novatech-assistant", module: "query-endpoint" },
});

export type Logger = typeof logger;
