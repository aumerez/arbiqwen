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

export interface ChatToolCall {
  toolName?: string;
  integrationKey?: string;
  skillKey?: string;
  status?: string;
}

export interface ChatMessageView {
  /** Local, stable key for rendering — not the backend row id. */
  localId: string;
  role: ChatRole;
  content: string;
  citations?: ChatCitation[];
  toolCalls?: ChatToolCall[];
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
  tool_name?: string;
  integration_key?: string;
  skill_key?: string;
  status_code?: number;
  [key: string]: unknown;
}
