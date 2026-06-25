// Proves the harness BLOCKS invalid responses (does not merely log them).
// avaliacao-foundation cut rule: "código que deveria bloquear mas só loga → D3 ≤ 2".

import { describe, it, expect } from "vitest";
import {
  validateResponse,
  structuredOutputSchema,
  SAFE_FALLBACK,
} from "../../src/services/response-validator.js";

const valid = {
  answer: "O prazo de devolução para produtos standard é de 7 dias úteis.",
  source_document: "POL-001",
  confidence_score: 0.92,
};

describe("structuredOutputSchema", () => {
  it("accepts a well-formed structured output", () => {
    expect(structuredOutputSchema.safeParse(valid).success).toBe(true);
  });

  it("rejects unexpected extra fields (.strict — code-review fix #1)", () => {
    const withExtra = { ...valid, injected: "x" };
    expect(structuredOutputSchema.safeParse(withExtra).success).toBe(false);
  });

  it("rejects a blank source_document (G1 cannot be bypassed by empty string — fix #2)", () => {
    expect(structuredOutputSchema.safeParse({ ...valid, source_document: "   " }).success).toBe(false);
  });

  it("rejects confidence_score outside [0,1] (fix #3)", () => {
    expect(structuredOutputSchema.safeParse({ ...valid, confidence_score: 7 }).success).toBe(false);
  });
});

describe("validateResponse — schema / G1", () => {
  it("passes a valid response through unchanged", () => {
    const outcome = validateResponse(valid);
    expect(outcome.ok).toBe(true);
    expect(outcome.response.source_document).toBe("POL-001");
  });

  it("G1: blocks a response with no source_document and returns the safe fallback", () => {
    const outcome = validateResponse({ answer: "resposta sem fonte", confidence_score: 0.8 });
    expect(outcome.ok).toBe(false);
    expect(outcome.response).toEqual(SAFE_FALLBACK);
  });

  it("blocks non-object / garbage input without throwing", () => {
    expect(validateResponse("not json").ok).toBe(false);
    expect(validateResponse(null).ok).toBe(false);
  });
});

describe("validateResponse — G2 (carga perigosa + devolução)", () => {
  it("allows the compliant negative answer (POL-001 §3.2)", () => {
    const outcome = validateResponse({
      answer:
        "Não. Cargas perigosas classes 1 a 6 da ANTT não podem ser devolvidas pelo processo padrão.",
      source_document: "POL-001",
      confidence_score: 0.95,
    });
    expect(outcome.ok).toBe(true);
  });

  it("blocks an answer that asserts a dangerous-cargo return IS possible", () => {
    const outcome = validateResponse({
      answer: "Sim, cargas perigosas podem ser devolvidas pelo processo padrão.",
      source_document: "FAQ-Atendimento",
      confidence_score: 0.9,
    });
    expect(outcome.ok).toBe(false);
    expect(outcome.response).toEqual(SAFE_FALLBACK);
  });

  it("blocks the combo when the mandatory negative is missing", () => {
    const outcome = validateResponse({
      answer: "Para devolver carga perigosa, abra um chamado no portal e anexe fotos.",
      source_document: "POL-001",
      confidence_score: 0.7,
    });
    expect(outcome.ok).toBe(false);
  });

  it("is not bypassable via accents/case (fix #4 — regex robustness)", () => {
    const outcome = validateResponse({
      answer: "SIM, CARGAS PERIGOSAS PODEM SER DEVOLVIDAS normalmente.",
      source_document: "FAQ-Atendimento",
      confidence_score: 0.9,
    });
    expect(outcome.ok).toBe(false);
  });

  it("does not over-block answers about ordinary cargo returns", () => {
    const outcome = validateResponse({
      answer: "Produtos standard podem ser devolvidos em até 7 dias úteis.",
      source_document: "POL-001",
      confidence_score: 0.9,
    });
    expect(outcome.ok).toBe(true);
  });
});
