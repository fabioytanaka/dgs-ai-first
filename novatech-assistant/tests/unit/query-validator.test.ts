import { describe, it, expect } from "vitest";
import { parseQueryRequest } from "../../src/functions/query/validator.js";
import { ValidationError } from "../../src/shared/errors.js";

describe("parseQueryRequest", () => {
  it("should accept a valid question", () => {
    const result = parseQueryRequest({ question: "Qual o SLA do cliente Gold?" });
    expect(result.question).toBe("Qual o SLA do cliente Gold?");
  });

  it("should reject a body without question (VC-05)", () => {
    expect(() => parseQueryRequest({})).toThrowError(ValidationError);
  });

  it("should reject a question shorter than 3 characters", () => {
    expect(() => parseQueryRequest({ question: "ok" })).toThrowError(ValidationError);
  });

  it("should reject history with more than 3 turns (ADR-0002)", () => {
    const history = Array.from({ length: 4 }, () => ({ role: "user" as const, content: "x" }));
    expect(() => parseQueryRequest({ question: "Posso devolver carga perigosa?", history })).toThrowError(
      ValidationError,
    );
  });
});
