// HTTP trigger for the query endpoint — POST /api/query.
// T-06 scope: register the Azure Functions v4 route, validate input (T-05) and
// return structured errors. The RAG flow (search -> prompt -> completion ->
// response) is wired in T-07..T-10 and currently returns 501.

import { app, type HttpRequest, type HttpResponseInit, type InvocationContext } from "@azure/functions";
import { parseQueryRequest } from "./validator.js";
import { isAppError } from "../../shared/errors.js";
import { logger } from "../../shared/logger.js";
import type { ErrorResponse } from "../../shared/types.js";

function errorBody(code: string, message: string): ErrorResponse {
  return { error: { code, message } };
}

export async function queryHandler(
  request: HttpRequest,
  context: InvocationContext,
): Promise<HttpResponseInit> {
  const log = logger.child({ invocationId: context.invocationId });
  log.info("query.received");

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    log.warn("query.invalid_json");
    return { status: 400, jsonBody: errorBody("VALIDATION_ERROR", "Request body must be valid JSON") };
  }

  try {
    const parsed = parseQueryRequest(body);
    log.info({ hasHistory: Boolean(parsed.history?.length) }, "query.validated");

    // RAG pipeline not implemented yet (T-07..T-10). Validation succeeded.
    return {
      status: 501,
      jsonBody: errorBody("NOT_IMPLEMENTED", "RAG pipeline pending (tasks T-07..T-10)"),
    };
  } catch (err) {
    if (isAppError(err)) {
      log.warn({ code: err.code }, "query.rejected");
      return { status: err.statusCode, jsonBody: errorBody(err.code, err.message) };
    }
    log.error({ err }, "query.unexpected_error");
    return { status: 500, jsonBody: errorBody("INTERNAL_ERROR", "Unexpected error") };
  }
}

app.http("query", {
  methods: ["POST"],
  authLevel: "function",
  route: "query",
  handler: queryHandler,
});
