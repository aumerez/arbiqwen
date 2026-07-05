// Browser-local chat transport + adapter.
//
// Talks to the backend chat API (/chats — not under /api) using the in-memory
// access token. Streaming reads the response body with fetch + ReadableStream and
// parses the backend's `data: {json}` SSE frames manually — not the browser's
// push-based SSE client or sockets, which the coupling guard disallows. All
// network access for chat lives here, in the approved HTTP adapter layer. Errors
// are typed and non-secret.

import { BrowserReadError } from './httpClient';

export interface ChatClientConfig {
  /** Backend origin (no /api suffix). Empty = same-origin. */
  baseUrl?: string;
  /** Memory-only token source. */
  getToken?: () => string | null | undefined;
  /** Injectable fetch for tests. */
  fetchImpl?: typeof fetch;
}

export interface RawChat {
  id: number;
  title?: string | null;
  project_id?: number | null;
  created_at?: string;
  updated_at?: string | null;
}

export interface RawMessage {
  id: number;
  chat_id: number;
  role: string;
  content: string;
  citations?: unknown[] | null;
  tool_calls?: unknown[] | null;
  created_at?: string;
}

export interface SendHandlers {
  onChunk: (chunk: Record<string, unknown>) => void;
  signal?: AbortSignal;
}

export interface ChatClient {
  create(opts?: { title?: string | null; projectId?: number | null }): Promise<RawChat>;
  list(): Promise<RawChat[]>;
  listMessages(chatId: number): Promise<RawMessage[]>;
  send(chatId: number, message: string, handlers: SendHandlers): Promise<void>;
  cancel(chatId: number): Promise<void>;
  remove(chatId: number): Promise<void>;
}

const defaultFetch: typeof fetch = (input, init) => globalThis.fetch(input, init);

export function createChatClient(config: ChatClientConfig = {}): ChatClient {
  const base = (config.baseUrl ?? '').replace(/\/$/, '');
  const doFetch = config.fetchImpl ?? defaultFetch;

  function authHeaders(extra: Record<string, string> = {}): Record<string, string> {
    const headers: Record<string, string> = { ...extra };
    const token = config.getToken?.();
    if (token) headers.Authorization = `Bearer ${token}`;
    return headers;
  }

  async function requestJson<T>(method: string, path: string, body?: unknown): Promise<T> {
    const headers = authHeaders({ Accept: 'application/json' });
    if (body !== undefined) headers['Content-Type'] = 'application/json';

    let response: Response;
    try {
      response = await doFetch(`${base}${path}`, {
        method,
        headers,
        body: body === undefined ? undefined : JSON.stringify(body),
      });
    } catch {
      throw new BrowserReadError('network', 'Network request failed');
    }
    if (!response.ok) {
      throw new BrowserReadError('http', `Request failed with status ${response.status}`, response.status);
    }
    if (response.status === 204) {
      return undefined as T;
    }
    try {
      return (await response.json()) as T;
    } catch {
      throw new BrowserReadError('parse', 'Received an invalid response');
    }
  }

  return {
    create(opts = {}) {
      return requestJson<RawChat>('POST', '/chats', {
        title: opts.title ?? null,
        project_id: opts.projectId ?? null,
      });
    },

    list() {
      return requestJson<RawChat[]>('GET', '/chats');
    },

    listMessages(chatId) {
      return requestJson<RawMessage[]>('GET', `/chats/${encodeURIComponent(String(chatId))}/messages`);
    },

    cancel(chatId) {
      return requestJson<void>('POST', `/chats/${encodeURIComponent(String(chatId))}/cancel`);
    },

    remove(chatId) {
      return requestJson<void>('DELETE', `/chats/${encodeURIComponent(String(chatId))}`);
    },

    async send(chatId, message, handlers) {
      const url = `${base}/chats/${encodeURIComponent(String(chatId))}/messages`;
      let response: Response;
      try {
        response = await doFetch(url, {
          method: 'POST',
          headers: authHeaders({ 'Content-Type': 'application/json', Accept: 'text/event-stream' }),
          body: JSON.stringify({ message }),
          signal: handlers.signal,
        });
      } catch {
        if (handlers.signal?.aborted) return;
        throw new BrowserReadError('network', 'Unable to reach the backend');
      }
      if (!response.ok) {
        throw new BrowserReadError('http', `Message failed with status ${response.status}`, response.status);
      }
      const stream = response.body;
      if (!stream) {
        throw new BrowserReadError('parse', 'Response had no stream');
      }

      const reader = stream.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      try {
        for (;;) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          let newlineIndex: number;
          while ((newlineIndex = buffer.indexOf('\n')) >= 0) {
            const line = buffer.slice(0, newlineIndex).trim();
            buffer = buffer.slice(newlineIndex + 1);
            // Skip blank separators and `:` heartbeat comments.
            if (!line || line.startsWith(':')) continue;
            if (line.startsWith('data:')) {
              const payload = line.slice(5).trim();
              if (!payload) continue;
              try {
                handlers.onChunk(JSON.parse(payload) as Record<string, unknown>);
              } catch {
                // Ignore a malformed frame rather than aborting the stream.
              }
            }
          }
        }
      } catch {
        if (handlers.signal?.aborted) return;
        throw new BrowserReadError('network', 'Stream interrupted');
      }
    },
  };
}
