// Environment configuration, validated at startup with Zod (fail-fast).
// No other module reads process.env directly — they import `config` from here.

import { z } from "zod";
import { ConfigError } from "./errors.js";

const envSchema = z.object({
  AZURE_OPENAI_ENDPOINT: z.string().url(),
  AZURE_OPENAI_API_KEY: z.string().min(1),
  AZURE_OPENAI_GPT_DEPLOYMENT: z.string().min(1),
  AZURE_OPENAI_EMBEDDING_DEPLOYMENT: z.string().min(1),
  AZURE_SEARCH_ENDPOINT: z.string().url(),
  AZURE_SEARCH_API_KEY: z.string().min(1),
  AZURE_SEARCH_INDEX: z.string().min(1),
  // Context budget (ADR-0002). Defaults reflect the ADR: ~4K system + ~8K chunks.
  CONTEXT_BUDGET_SYSTEM_TOKENS: z.coerce.number().int().positive().default(4000),
  CONTEXT_BUDGET_CHUNK_TOKENS: z.coerce.number().int().positive().default(8000),
  RETRIEVAL_TOP_K: z.coerce.number().int().positive().default(5),
  MAX_HISTORY_TURNS: z.coerce.number().int().positive().default(3),
  COMPLETION_TIMEOUT_MS: z.coerce.number().int().positive().default(25000),
  // Feedback persistence (Cosmos DB) — Cenário 3, Ex. 3.2.
  COSMOS_CONNECTION_STRING: z.string().min(1),
  COSMOS_DATABASE: z.string().min(1).default("novatech"),
  COSMOS_FEEDBACK_CONTAINER: z.string().min(1).default("feedbacks"),
});

export type AppConfig = z.infer<typeof envSchema>;

function loadConfig(): AppConfig {
  const parsed = envSchema.safeParse(process.env);
  if (!parsed.success) {
    const missing = parsed.error.issues
      .map((i) => `${i.path.join(".")}: ${i.message}`)
      .join("; ");
    throw new ConfigError(`Invalid environment configuration: ${missing}`);
  }
  return parsed.data;
}

export const config: AppConfig = loadConfig();
