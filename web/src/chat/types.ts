// Browser-side chat view models and the backend SSE chunk contract.
//
// Chunk shapes mirror what the backend emits from POST /chats/{id}/messages
// (text / citations / tool_call / tool_result / thinking_* / segment_role /
// artifact / done / error). Only non-secret display fields are carried into the
// view models.

export type ChatRole = 'user' | 'assistant';

export interface ChatCitation {
  number?: number;
  documentName?: string;
  pageNumber?: number;
  snippet?: string;
}

export interface ChatToolResult {
  error?: string;
  statusCode?: number;
  recordCount?: number;
  durationMs?: number;
}

export interface ChatToolCall {
  id?: string;
  toolName?: string;
  integrationKey?: string;
  skillKey?: string;
  operationId?: string;
  result?: ChatToolResult;
}

export interface ArtifactView {
  id: number | string;
  filename?: string;
  title?: string;
  contentType?: string;
}

export interface ChatThinking {
  content: string;
  streaming: boolean;
  durationMs: number;
}

export interface ChatMessageView {
  /** Local, stable key for rendering — not the backend row id. */
  localId: string;
  role: ChatRole;
  content: string;
  citations?: ChatCitation[];
  toolCalls?: ChatToolCall[];
  artifacts?: ArtifactView[];
  thinking?: ChatThinking;
  /** ISO timestamp for the footer. */
  createdAt?: string;
  /** True while the assistant message is still streaming. */
  streaming?: boolean;
  /** True when this message represents a safe error notice. */
  error?: boolean;
}

export interface ChatSummary {
  id: number;
  title: string | null;
}

/** A single parsed SSE frame from the backend stream. */
export interface StreamChunk {
  type: string;
  text?: string;
  citations?: unknown[];
  error?: string;
  role?: string;
  tool_use_id?: string;
  tool_name?: string;
  integration_key?: string;
  skill_key?: string;
  operation_id?: string;
  status_code?: number;
  duration_ms?: number;
  record_count?: number;
  id?: number | string;
  filename?: string;
  title?: string;
  content_type?: string;
  [key: string]: unknown;
}
