import { useCallback, useEffect, useRef, useState } from 'react';
import type { ChatClient, RawMessage } from '../api/http/chatClient';
import { BrowserReadError } from '../api/http/httpClient';
import type { ChatCitation, ChatMessageView, ChatSummary, ChatToolCall, StreamChunk } from './types';

// Project-scoped conversation state: the chat list for the active project, the
// selected conversation's messages, and the streaming send path. Switching the
// active project reloads the list and clears the open conversation. Read/append
// only — no project or document mutations.

let idCounter = 0;
function nextLocalId(): string {
  idCounter += 1;
  return `m${idCounter}`;
}

function toToolCall(chunk: StreamChunk): ChatToolCall {
  return {
    id: typeof chunk.tool_use_id === 'string' ? chunk.tool_use_id : undefined,
    toolName: typeof chunk.tool_name === 'string' ? chunk.tool_name : undefined,
    integrationKey: typeof chunk.integration_key === 'string' ? chunk.integration_key : undefined,
    skillKey: typeof chunk.skill_key === 'string' ? chunk.skill_key : undefined,
    operationId: typeof chunk.operation_id === 'string' ? chunk.operation_id : undefined,
    input: chunk.input && typeof chunk.input === 'object' ? chunk.input : undefined,
  };
}

function toToolResult(chunk: StreamChunk) {
  return {
    error: typeof chunk.error === 'string' ? chunk.error : undefined,
    statusCode: typeof chunk.status_code === 'number' ? chunk.status_code : undefined,
    recordCount: typeof chunk.record_count === 'number' ? chunk.record_count : undefined,
    durationMs: typeof chunk.duration_ms === 'number' ? chunk.duration_ms : undefined,
    sizeChars: typeof chunk.size_chars === 'number' ? chunk.size_chars : undefined,
    preview: typeof chunk.preview === 'string' ? chunk.preview : undefined,
    rawPreview: typeof chunk.raw_preview === 'string' ? chunk.raw_preview : undefined,
  };
}

function mapHistory(rows: RawMessage[]): ChatMessageView[] {
  return rows.map((row) => ({
    localId: nextLocalId(),
    role: row.role === 'assistant' ? 'assistant' : 'user',
    content: row.content ?? '',
    citations: Array.isArray(row.citations) ? (row.citations as ChatCitation[]) : undefined,
    toolCalls: Array.isArray(row.tool_calls) ? (row.tool_calls as ChatToolCall[]) : undefined,
    createdAt: row.created_at,
  }));
}

export interface UseConversations {
  chats: ChatSummary[];
  currentChatId: number | null;
  messages: ChatMessageView[];
  sending: boolean;
  error: string | null;
  newChat: () => void;
  selectChat: (id: number) => void;
  send: (text: string) => void;
  stop: () => void;
}

export function useConversations(client: ChatClient, projectId: number | null): UseConversations {
  const [chats, setChats] = useState<ChatSummary[]>([]);
  const [currentChatId, setCurrentChatId] = useState<number | null>(null);
  const [messages, setMessages] = useState<ChatMessageView[]>([]);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const chatIdRef = useRef<number | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const patch = useCallback((localId: string, fn: (prev: ChatMessageView) => ChatMessageView) => {
    setMessages((prev) => prev.map((m) => (m.localId === localId ? fn(m) : m)));
  }, []);

  const loadChats = useCallback(async () => {
    try {
      const rows = await client.list(projectId);
      setChats(rows.map((c) => ({ id: c.id, title: c.title ?? null })));
    } catch {
      setChats([]);
    }
  }, [client, projectId]);

  // Reset and reload when the active project changes.
  useEffect(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    chatIdRef.current = null;
    setCurrentChatId(null);
    setMessages([]);
    setError(null);
    void loadChats();
  }, [loadChats]);

  const newChat = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    chatIdRef.current = null;
    setCurrentChatId(null);
    setMessages([]);
    setError(null);
  }, []);

  const selectChat = useCallback(
    (id: number) => {
      abortRef.current?.abort();
      abortRef.current = null;
      chatIdRef.current = id;
      setCurrentChatId(id);
      setError(null);
      setMessages([]);
      void (async () => {
        try {
          const rows = await client.listMessages(id);
          if (chatIdRef.current === id) setMessages(mapHistory(rows));
        } catch {
          setError('Could not load this conversation.');
        }
      })();
    },
    [client],
  );

  const send = useCallback(
    (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || sending) return;
      setError(null);
      setSending(true);

      const nowIso = new Date().toISOString();
      const userMsg: ChatMessageView = { localId: nextLocalId(), role: 'user', content: trimmed, createdAt: nowIso };
      const assistantId = nextLocalId();
      setMessages((prev) => [
        ...prev,
        userMsg,
        { localId: assistantId, role: 'assistant', content: '', streaming: true, createdAt: nowIso },
      ]);

      const controller = new AbortController();
      abortRef.current = controller;

      const run = async () => {
        let created = false;
        if (chatIdRef.current === null) {
          const chat = await client.create({ projectId });
          chatIdRef.current = chat.id;
          setCurrentChatId(chat.id);
          created = true;
        }
        await client.send(chatIdRef.current as number, trimmed, {
          signal: controller.signal,
          onChunk: (raw) => {
            const chunk = raw as StreamChunk;
            switch (chunk.type) {
              case 'text':
                if (typeof chunk.text === 'string') {
                  // Accumulate into the current segment (the live body).
                  patch(assistantId, (m) => ({ ...m, content: m.content + chunk.text }));
                }
                break;
              case 'segment_role':
                // The backend classifies the round that just ended:
                // "thinking" → commit the current segment as a thinking block
                // (rendered before this round's tool cards) and reset it;
                // "synthesis" → the rest is the answer body.
                if (chunk.kind === 'thinking') {
                  patch(assistantId, (m) => {
                    if (!m.content.trim()) return m;
                    return {
                      ...m,
                      thinkingBlocks: [
                        ...(m.thinkingBlocks ?? []),
                        { content: m.content, beforeToolIndex: m.toolCalls?.length ?? 0 },
                      ],
                      content: '',
                    };
                  });
                } else if (chunk.kind === 'synthesis') {
                  patch(assistantId, (m) => ({ ...m, inSynthesis: true }));
                }
                break;
              case 'citations':
                if (Array.isArray(chunk.citations)) {
                  patch(assistantId, (m) => ({ ...m, citations: chunk.citations as ChatCitation[] }));
                }
                break;
              case 'tool_call':
                patch(assistantId, (m) => ({ ...m, toolCalls: [...(m.toolCalls ?? []), toToolCall(chunk)] }));
                break;
              case 'tool_result':
                patch(assistantId, (m) => ({
                  ...m,
                  toolCalls: (m.toolCalls ?? []).map((tc) =>
                    tc.id && tc.id === chunk.tool_use_id ? { ...tc, result: toToolResult(chunk) } : tc,
                  ),
                }));
                break;
              case 'artifact':
                // Match the desktop: always surface the artifact card (id falls
                // back to 0 when the chunk omits it), so a dashboard/report card
                // appears even if the id is missing.
                patch(assistantId, (m) => ({
                  ...m,
                  artifacts: [
                    ...(m.artifacts ?? []),
                    {
                      id: (chunk.id as number | string | undefined) ?? 0,
                      filename: typeof chunk.filename === 'string' ? chunk.filename : undefined,
                      title: typeof chunk.title === 'string' ? chunk.title : undefined,
                      contentType: typeof chunk.content_type === 'string' ? chunk.content_type : undefined,
                    },
                  ],
                }));
                break;
              case 'thinking_start':
                patch(assistantId, (m) => ({
                  ...m,
                  thinking: { content: m.thinking?.content ?? '', streaming: true, durationMs: 0 },
                }));
                break;
              case 'thinking_delta':
                if (typeof chunk.text === 'string') {
                  patch(assistantId, (m) => ({
                    ...m,
                    thinking: {
                      content: (m.thinking?.content ?? '') + chunk.text,
                      streaming: true,
                      durationMs: m.thinking?.durationMs ?? 0,
                    },
                  }));
                }
                break;
              case 'thinking_end':
                patch(assistantId, (m) => ({
                  ...m,
                  thinking: {
                    content: m.thinking?.content ?? '',
                    streaming: false,
                    durationMs: typeof chunk.duration_ms === 'number' ? chunk.duration_ms : (m.thinking?.durationMs ?? 0),
                  },
                }));
                break;
              case 'error':
                patch(assistantId, (m) => ({
                  ...m,
                  content: 'The assistant could not complete this response.',
                  error: true,
                  streaming: false,
                }));
                break;
              default:
                break;
            }
          },
        });
        if (created) void loadChats();
      };

      run()
        .catch((err) => {
          const message =
            err instanceof BrowserReadError && err.kind === 'network'
              ? 'Could not reach the backend.'
              : 'Something went wrong sending your message.';
          setError(message);
          patch(assistantId, (m) => ({ ...m, content: m.content || message, error: !m.content }));
        })
        .finally(() => {
          patch(assistantId, (m) => ({ ...m, streaming: false }));
          setSending(false);
          abortRef.current = null;
        });
    },
    [client, projectId, patch, sending, loadChats],
  );

  const stop = useCallback(() => {
    abortRef.current?.abort();
    const chatId = chatIdRef.current;
    if (chatId !== null) {
      void client.cancel(chatId).catch(() => {});
    }
  }, [client]);

  return { chats, currentChatId, messages, sending, error, newChat, selectChat, send, stop };
}
