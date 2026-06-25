// Input validation for POST /api/query (Zod). Enforces the ADR-0002 history
// cap (<= 3 turns) and rejects anything malformed before it reaches the model.

import { z } from "zod";
import { ValidationError } from "../../shared/errors.js";
import type { QueryRequest } from "../../shared/types.js";

const MAX_HISTORY_TURNS = 3; // ADR-0002

const conversationTurnSchema = z.object({
  role: z.enum(["user", "assistant"]),
  content: z.string().min(1).max(4000),
});

const queryRequestSchema = z.object({
  question: z
    .string({ required_error: "question is required" })
    .trim()
    .min(3, "question must be at least 3 characters")
    .max(1000, "question must be at most 1000 characters"),
  conversationId: z.string().uuid().optional(),
  history: z
    .array(conversationTurnSchema)
    .max(MAX_HISTORY_TURNS, `history is limited to ${MAX_HISTORY_TURNS} turns (ADR-0002)`)
    .optional(),
});

/**
 * Parses and validates an unknown request body.
 * @throws {ValidationError} when the body is malformed or violates the schema.
 */
export function parseQueryRequest(body: unknown): QueryRequest {
  const result = queryRequestSchema.safeParse(body);
  if (!result.success) {
    const detail = result.error.issues
      .map((i) => `${i.path.join(".") || "body"}: ${i.message}`)
      .join("; ");
    throw new ValidationError(detail);
  }
  return result.data;
}
