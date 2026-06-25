// Custom error hierarchy. Each error carries an HTTP statusCode and a stable
// machine-readable `code`, so the handler maps domain failures to responses
// without leaking stack traces.

export abstract class AppError extends Error {
  abstract readonly statusCode: number;
  abstract readonly code: string;

  protected constructor(message: string) {
    super(message);
    // Restore prototype chain (TS + extending built-in Error).
    this.name = new.target.name;
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

/** Invalid client input — never reaches search/completion. HTTP 400. */
export class ValidationError extends AppError {
  readonly statusCode = 400;
  readonly code = "VALIDATION_ERROR";
  constructor(message: string) {
    super(message);
  }
}

/** Azure AI Search retrieval failed after retries. HTTP 502. */
export class RetrievalError extends AppError {
  readonly statusCode = 502;
  readonly code = "RETRIEVAL_ERROR";
  constructor(message: string) {
    super(message);
  }
}

/** Azure OpenAI completion failed after retries. HTTP 502. */
export class CompletionError extends AppError {
  readonly statusCode = 502;
  readonly code = "COMPLETION_ERROR";
  constructor(message: string) {
    super(message);
  }
}

/** Missing/invalid environment configuration. HTTP 500. */
export class ConfigError extends AppError {
  readonly statusCode = 500;
  readonly code = "CONFIG_ERROR";
  constructor(message: string) {
    super(message);
  }
}

/** Type guard for centralized error handling in the HTTP handler. */
export function isAppError(err: unknown): err is AppError {
  return err instanceof AppError;
}
