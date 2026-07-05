import { useCallback, useRef, useState } from 'react';
import type { ChatClient } from '../api/http/chatClient';
import { BrowserReadError } from '../api/http/httpClient';
import type { ChatCitation, ChatMessageView, ChatToolCall, StreamChunk } from './types';

// Drives a single conversation: lazily creates a backend chat on first send,
// appends the user turn, and accumulates the streamed assistant turn from SSE
// chunks. Read-only beyond sending: no project/document/agent operations. The
// chat client (and its in-memory token) is injected.

let idCounter = 0;
function nextLocalId(): string {
  idCounter += 1;
  return `m${idCounter}`;
}

function toToolCall(chunk: StreamChunk): ChatToolCall {
  return {
    toolName: typeof chunk.tool_name === 'string' ? chunk.tool_name : undefined,
    integrationKey: typeof chunk.integration_key === 'string' ? chunk.integration_key : undefined,
    skillKey: typeof chunk.skill_key === 'string' ? chunk.skill_key : undefined,
  };
}

export interface UseChat {
  messages: ChatMessageView[];
  sending: boolean;
  error: string | null;
  send: (text: string) => void;
  stop: () => void;
  reset: () => void;
}

export function useChat(client: ChatClient): UseChat {
  const [messages, setMessages] = useState<ChatMessageView[]>([]);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const chatIdRef = useRef<number | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const patchAssistant = useCallback((localId: string, patch: (prev: ChatMessageView) => ChatMessageView) => {
    setMessages((prev) => prev.map((m) => (m.localId === localId ? patch(m) : m)));
  }, []);

  const send = useCallback(
    (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || sending) return;

      setError(null);
      setSending(true);

      const userMsg: ChatMessageView = { localId: nextLocalId(), role: 'user', content: trimmed };
      const assistantId = nextLocalId();
      const assistantMsg: ChatMessageView = { localId: assistantId, role: 'assistant', content: '', streaming: true };
      setMessages((prev) => [...prev, userMsg, assistantMsg]);

      const controller = new AbortController();
      abortRef.current = controller;

      const run = async () => {
        if (chatIdRef.current === null) {
          const chat = await client.create();
          chatIdRef.current = chat.id;
        }
        const chatId = chatIdRef.current;
        await client.send(chatId, trimmed, {
          signal: controller.signal,
          onChunk: (raw) => {
            const chunk = raw as StreamChunk;
            switch (chunk.type) {
              case 'text':
                if (typeof chunk.text === 'string') {
                  patchAssistant(assistantId, (m) => ({ ...m, content: m.content + chunk.text }));
                }
                break;
              case 'citations':
                if (Array.isArray(chunk.citations)) {
                  patchAssistant(assistantId, (m) => ({ ...m, citations: chunk.citations as ChatCitation[] }));
                }
                break;
              case 'tool_call':
                patchAssistant(assistantId, (m) => ({
                  ...m,
                  toolCalls: [...(m.toolCalls ?? []), toToolCall(chunk)],
                }));
                break;
              case 'error':
                patchAssistant(assistantId, (m) => ({
                  ...m,
                  content: 'The assistant could not complete this response.',
                  error: true,
                  streaming: false,
                }));
                break;
              // tool_result / thinking_* / segment_role / artifact / done are
              // consumed without dedicated rendering in this view.
              default:
                break;
            }
          },
        });
      };

      run()
        .catch((err) => {
          const message =
            err instanceof BrowserReadError && err.kind === 'network'
              ? 'Could not reach the backend.'
              : 'Something went wrong sending your message.';
          setError(message);
          patchAssistant(assistantId, (m) => ({
            ...m,
            content: m.content || message,
            error: !m.content,
          }));
        })
        .finally(() => {
          patchAssistant(assistantId, (m) => ({ ...m, streaming: false }));
          setSending(false);
          abortRef.current = null;
        });
    },
    [client, patchAssistant, sending],
  );

  const stop = useCallback(() => {
    abortRef.current?.abort();
    const chatId = chatIdRef.current;
    if (chatId !== null) {
      void client.cancel(chatId).catch(() => {
        // Best-effort cancel; ignore failures.
      });
    }
  }, [client]);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    chatIdRef.current = null;
    setMessages([]);
    setError(null);
    setSending(false);
  }, []);

  return { messages, sending, error, send, stop, reset };
}
