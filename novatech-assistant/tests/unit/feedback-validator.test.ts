// Proves the rewritten feedback endpoint validates input with Zod (no `as any`).

import { describe, it, expect } from "vitest";
import { parseFeedbackRequest } from "../../src/functions/feedback/validator.js";
import { ValidationError } from "../../src/shared/errors.js";

const valid = {
  queryId: "3f1c6b2a-9d4e-4a1b-8c2d-1e2f3a4b5c6d",
  rating: 5,
  comment: "resposta correta e bem citada",
  attendantEmail: "atendente@novatech.com.br",
};

describe("parseFeedbackRequest", () => {
  it("accepts a valid feedback payload", () => {
    expect(parseFeedbackRequest(valid).rating).toBe(5);
  });

  it("rejects a missing attendantEmail", () => {
    const { attendantEmail: _omit, ...rest } = valid;
    expect(() => parseFeedbackRequest(rest)).toThrowError(ValidationError);
  });

  it("rejects an invalid e-mail", () => {
    expect(() => parseFeedbackRequest({ ...valid, attendantEmail: "nope" })).toThrowError(ValidationError);
  });

  it("rejects rating out of range", () => {
    expect(() => parseFeedbackRequest({ ...valid, rating: 9 })).toThrowError(ValidationError);
  });

  it("rejects a non-UUID queryId", () => {
    expect(() => parseFeedbackRequest({ ...valid, queryId: "q1" })).toThrowError(ValidationError);
  });

  it("rejects unexpected extra fields (.strict)", () => {
    expect(() => parseFeedbackRequest({ ...valid, isAdmin: true })).toThrowError(ValidationError);
  });
});
