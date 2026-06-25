// Input validation for POST /api/feedback (Zod) — Cenário 3, Ex. 3.2.
// Replaces the `body as any` from the Copilot draft: nothing untrusted reaches
// persistence without passing this schema first (AGENTS.md: Zod for input).

import { z } from "zod";
import { ValidationError } from "../../shared/errors.js";
import type { FeedbackRequest } from "../../shared/types.js";

const feedbackRequestSchema = z
  .object({
    queryId: z.string().uuid("queryId must be a UUID"),
    rating: z.number().int().min(1).max(5),
    comment: z.string().trim().max(2000).optional(),
    attendantEmail: z.string().email("attendantEmail must be a valid e-mail"),
  })
  .strict(); // reject unexpected fields (e.g. a client trying to spoof `timestamp`)

/**
 * Parses and validates an unknown feedback body.
 * @throws {ValidationError} when the body is malformed or violates the schema.
 */
export function parseFeedbackRequest(body: unknown): FeedbackRequest {
  const result = feedbackRequestSchema.safeParse(body);
  if (!result.success) {
    const detail = result.error.issues
      .map((i) => `${i.path.join(".") || "body"}: ${i.message}`)
      .join("; ");
    throw new ValidationError(detail);
  }
  return result.data;
}
