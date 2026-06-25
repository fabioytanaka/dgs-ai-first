// Domain types for the NovaTech Assistant query endpoint.
// Ubiquitous language is encoded in the type system: tiers, sources and chunks
// carry the same names used across docs/novatech and the AGENTS.md glossary.

/**
 * Customer tiers defined in SLA-2024 §1. These are the ONLY valid tiers —
 * "Platinum" does not exist (see FAQ-15). Modeled as a literal union so the
 * compiler rejects invented tiers.
 */
export type CustomerTier = "Gold" | "Silver" | "Standard";

/** A reference to the source document backing an answer (guardrail: always cited). */
export interface SourceDocument {
  /** Stable document id, e.g. "POL-001", "PROC-042-v2", "SLA-2024". */
  documentId: string;
  /** Human-facing title, e.g. "Política de Devolução". */
  title: string;
  /** Section anchor, e.g. "§3.2". */
  section?: string;
  /** Whether this document is the currently valid version (ADR-0003). */
  isCurrentVersion: boolean;
}

/** A retrieved chunk from Azure AI Search. */
export interface Chunk {
  id: string;
  content: string;
  /** Similarity score (0..1) returned by the retriever. */
  score: number;
  source: SourceDocument;
}

/** A single prior conversation turn (history is capped at 3 — ADR-0002). */
export interface ConversationTurn {
  role: "user" | "assistant";
  content: string;
}

/** Validated request body for POST /api/query. */
export interface QueryRequest {
  question: string;
  conversationId?: string;
  history?: ConversationTurn[];
}

/** Response contract. `source_document` is REQUIRED (guardrail / VC-02). */
export interface QueryResponse {
  answer: string;
  source_document: SourceDocument;
  /** True when retrieval confidence is below threshold (guardrail: warn + escalate). */
  low_confidence: boolean;
}

/** Structured error body returned to clients. */
export interface ErrorResponse {
  error: {
    code: string;
    message: string;
  };
}

/**
 * Validated feedback submitted by a pilot attendant (POST /api/feedback).
 * `attendantEmail` is PII — it is persisted but NEVER logged (AGENTS.md).
 */
export interface FeedbackRequest {
  queryId: string;
  rating: number;
  comment?: string;
  attendantEmail: string;
}

/** A feedback record as persisted (request + server-side timestamp). */
export interface FeedbackRecord extends FeedbackRequest {
  /** ISO-8601 timestamp set on the server, not trusted from the client. */
  timestamp: string;
}
