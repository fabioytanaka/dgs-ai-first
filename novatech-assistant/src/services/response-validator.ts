// Deterministic harness for the assistant's answers (Cenário 3 — Ex. 3.1).
//
// The system prompt ASKS the model for a source and the dangerous-cargo
// negative; that is PROBABILISTIC — the model can forget. This module makes it
// DETERMINISTIC: a Zod structured output forces the contract, and two guardrails
// BLOCK (not just log) any answer that slips through. On any failure we return a
// safe fallback — the bad answer never reaches the attendant.
//
// Guardrails implemented (subset formalized by the PS in Cenário 2):
//   G1 — every answer MUST carry `source_document`; otherwise it is rejected.
//   G2 — answers mentioning "carga perigosa" + "devolução" MUST contain the
//        negative (POL-001 §3.2: ANTT classes 1–6 are NOT returnable via the
//        standard process). If they assert a return is possible, they are blocked.

import { z } from "zod";
import { logger } from "../shared/logger.js";

const log = logger.child({ module: "response-validator" });

/**
 * Structured output contract the model MUST follow.
 *
 * `.strict()` rejects unexpected keys — a free-text model could otherwise smuggle
 * extra fields past validation (code-review fix #1). `source_document` is trimmed
 * and non-empty, so a present-but-blank value cannot bypass G1 (fix #2).
 * `confidence_score` is bounded to [0,1] instead of an unbounded number (fix #3).
 */
export const structuredOutputSchema = z
  .object({
    answer: z.string().trim().min(1, "answer is required").max(4000),
    source_document: z.string().trim().min(1, "source_document is required"),
    confidence_score: z.number().min(0).max(1),
  })
  .strict();

export type StructuredOutput = z.infer<typeof structuredOutputSchema>;

/** Returned whenever validation fails — safe, never asserts anything. */
export const SAFE_FALLBACK: StructuredOutput = {
  answer:
    "Não consigo responder isso com segurança no momento. Vou encaminhar para um atendente humano revisar.",
  source_document: "ESCALADO-HUMANO",
  confidence_score: 0,
};

/** Result of validation. On `ok: false`, `response` is the safe fallback. */
export type ValidationOutcome =
  | { ok: true; response: StructuredOutput }
  | { ok: false; reason: string; response: StructuredOutput };

// --- G2 helpers ------------------------------------------------------------

/** Lowercase + strip diacritics so "Devolução" and "devolucao" match alike. */
function normalize(text: string): string {
  return text
    .toLowerCase()
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "");
}

// Matches "carga perigosa", "cargas perigosas", "carga(s) perigosa(s)".
const DANGEROUS_CARGO = /\bcargas?\s+perigosas?\b/;
// Matches devolução/devolver/devolvida/devolvido/devolvê-la... (stem "devolv"/"devolu").
const RETURN_TERMS = /\bdevolu\w*|\bdevolv\w*/;
// Presence of a negative — when the dangerous+return combo appears, the answer
// MUST carry one of these (POL-001 §3.2). Operates on normalized text ("nao").
const HAS_NEGATIVE = /\bnao\b|proibid\w*|vedad\w*|inelegiv\w*/;
// An UN-NEGATED affirmation that the return is possible. The `(?<!nao\s)`
// look-behind is the key fix: it stops "nao podem ser devolvidas" (the CORRECT
// negative) from being misread as an affirmation. A leading "sim" is also a block.
const STARTS_WITH_SIM = /^\s*sim\b/;
const AFFIRMS_RETURN =
  /(?<!nao\s)(podem?\s+ser\s+devolvid|podem?\s+devolv|sao\s+devolvid|e\s+possivel\s+devolv|permitid\w*\s+\w*\s*devolv)/;

/**
 * G2: returns a block reason if the answer combines dangerous cargo + return
 * and either affirms the return is possible or omits the mandatory negative.
 * Returns `null` when the answer is compliant or the combo is absent.
 */
function dangerousReturnViolation(answer: string): string | null {
  const text = normalize(answer);
  const mentionsCombo = DANGEROUS_CARGO.test(text) && RETURN_TERMS.test(text);
  if (!mentionsCombo) return null;

  if (STARTS_WITH_SIM.test(text) || AFFIRMS_RETURN.test(text)) {
    return "guardrail.dangerous_cargo_return_asserted_possible";
  }
  if (!HAS_NEGATIVE.test(text)) {
    return "guardrail.dangerous_cargo_return_missing_negative";
  }
  return null;
}

// --- Public API ------------------------------------------------------------

/**
 * Validates a raw model output (already JSON-parsed) against the structured
 * output contract and the two guardrails. ALWAYS returns a usable response:
 * the original when valid, the safe fallback when not. Never throws.
 */
export function validateResponse(raw: unknown): ValidationOutcome {
  // Step 1 — schema (covers G1: missing/blank source_document fails here).
  const parsed = structuredOutputSchema.safeParse(raw);
  if (!parsed.success) {
    const reason = `schema_invalid: ${parsed.error.issues
      .map((i) => `${i.path.join(".") || "body"}: ${i.message}`)
      .join("; ")}`;
    log.warn({ reason }, "response.rejected");
    return { ok: false, reason, response: SAFE_FALLBACK };
  }

  const output = parsed.data;

  // Step 2 — content guardrail (G2). Schema is valid; now check the assertion.
  const violation = dangerousReturnViolation(output.answer);
  if (violation) {
    log.warn({ reason: violation, source: output.source_document }, "response.blocked");
    return { ok: false, reason: violation, response: SAFE_FALLBACK };
  }

  log.info({ source: output.source_document }, "response.validated");
  return { ok: true, response: output };
}
