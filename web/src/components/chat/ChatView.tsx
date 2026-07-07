import { useEffect, useRef } from 'react';
import type { ChatMessageView } from '../../chat/types';
import { ChatMessageBubble } from './ChatMessageBubble';
import { ChatComposer } from './ChatComposer';

// Presentational conversation surface: the message thread plus the composer.
// All state (messages, sending, send/stop) is owned by the parent so the sidebar
// conversation list and this view stay in sync.
interface ChatViewProps {
  messages: ChatMessageView[];
  sending: boolean;
  error: string | null;
  onSend: (text: string) => void;
  onStop: () => void;
}

export function ChatView({ messages, sending, error, onSend, onStop }: ChatViewProps) {
  const endRef = useRef<HTMLDivElement>(null);
  let lastAssistantIndex = -1;
  messages.forEach((m, i) => {
    if (m.role === 'assistant') lastAssistantIndex = i;
  });

  useEffect(() => {
    endRef.current?.scrollIntoView?.({ block: 'end' });
  }, [messages]);

  return (
    <section className="chat" aria-label="Conversation">
      <div className="chat__scroll">
        {messages.length === 0 ? (
          <p className="empty">Start a conversation by sending a message below.</p>
        ) : (
          <ul className="chat__list">
            {messages.map((message, index) => (
              <ChatMessageBubble
                key={message.localId}
                message={message}
                isLastAssistant={message.role === 'assistant' && index === lastAssistantIndex}
              />
            ))}
          </ul>
        )}
        <div ref={endRef} />
      </div>

      {sending && (
        <div className="chat__dots" aria-label="Assistant is responding" role="status">
          <span className="chat__dot" />
          <span className="chat__dot" />
          <span className="chat__dot" />
        </div>
      )}

      {error && (
        <p className="chat__error" role="alert">
          {error}
        </p>
      )}

      <ChatComposer sending={sending} onSend={onSend} onStop={onStop} />
    </section>
  );
}
