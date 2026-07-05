import { useEffect, useMemo, useRef } from 'react';
import { MessageSquarePlus } from 'lucide-react';
import { createChatClient } from '../../api/http/chatClient';
import { getApiBaseUrl } from '../../config';
import { getToken } from '../../session';
import { useChat } from '../../chat/useChat';
import { ChatMessageBubble } from './ChatMessageBubble';
import { ChatComposer } from './ChatComposer';

// Interactive assistant surface. Builds the chat client from the configured
// backend origin and the in-memory token, then sends messages and renders the
// streamed reply. Only safe controls are present: new conversation, send, stop.
export function ChatView() {
  const client = useMemo(() => createChatClient({ baseUrl: getApiBaseUrl(), getToken }), []);
  const { messages, sending, error, send, stop, reset } = useChat(client);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // scrollIntoView is absent in jsdom; guard so tests and SSR-like envs are safe.
    endRef.current?.scrollIntoView?.({ block: 'end' });
  }, [messages]);

  return (
    <section className="chat" aria-labelledby="heading-assistant">
      <div className="page__header chat__header">
        <div>
          <h1 id="heading-assistant" className="page__title">
            Assistant
          </h1>
          <p className="page__desc">Ask questions grounded in this workspace&apos;s connected sources.</p>
        </div>
        <button type="button" className="chat__new" onClick={reset}>
          <MessageSquarePlus size={15} strokeWidth={1.75} />
          New conversation
        </button>
      </div>

      <div className="chat__scroll">
        {messages.length === 0 ? (
          <p className="empty">Start a conversation by sending a message below.</p>
        ) : (
          <ul className="chat__list">
            {messages.map((message) => (
              <ChatMessageBubble key={message.localId} message={message} />
            ))}
          </ul>
        )}
        <div ref={endRef} />
      </div>

      {error && (
        <p className="chat__error" role="alert">
          {error}
        </p>
      )}

      <ChatComposer sending={sending} onSend={send} onStop={stop} />
    </section>
  );
}
