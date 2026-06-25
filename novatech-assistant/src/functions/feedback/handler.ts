// HTTP trigger for the feedback endpoint — POST /api/feedback.
// Rewritten in Cenário 3 (Ex. 3.2) from the Copilot draft to follow AGENTS.md:
//   - Zod validation instead of `body as any`
//   - pino logger instead of console.log
//   - static imports (no dynamic require of @azure/cosmos)
//   - NEVER logs PII (attendantEmail / comment are persisted, never logged)
//   - structured errors via AppError, no stack-trace leak to the client.

import { app, type HttpRequest, type HttpResponseInit, type InvocationContext } from "@azure/functions";
import { parseFeedbackRequest } from "./validator.js";
import { getFeedbackRepository } from "./repository.js";
import { isAppError } from "../../shared/errors.js";
import { logger } from "../../shared/logger.js";
import type { ErrorResponse, FeedbackRecord } from "../../shared/types.js";

function errorBody(code: string, message: string): ErrorResponse {
  return { error: { code, message } };
}

export async function feedbackHandler(
  request: HttpRequest,
  context: InvocationContext,
): Promise<HttpResponseInit> {
  const log = logger.child({ invocationId: context.invocationId });
  log.info("feedback.received");

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    log.warn("feedback.invalid_json");
    return { status: 400, jsonBody: errorBody("VALIDATION_ERROR", "Request body must be valid JSON") };
  }

  try {
    const feedback = parseFeedbackRequest(body);
    const record: FeedbackRecord = {
      ...feedback,
      timestamp: new Date().toISOString(), // server-side, not trusted from client
    };

    await getFeedbackRepository().save(record);

    // Log only non-PII fields. attendantEmail/comment are intentionally omitted.
    log.info({ queryId: record.queryId, rating: record.rating }, "feedback.saved");
    return { status: 201, jsonBody: { status: "ok" } };
  } catch (err) {
    if (isAppError(err)) {
      log.warn({ code: err.code }, "feedback.rejected");
      return { status: err.statusCode, jsonBody: errorBody(err.code, err.message) };
    }
    log.error({ err }, "feedback.unexpected_error");
    return { status: 500, jsonBody: errorBody("INTERNAL_ERROR", "Unexpected error") };
  }
}

app.http("feedback", {
  methods: ["POST"],
  authLevel: "function",
  route: "feedback",
  handler: feedbackHandler,
});
