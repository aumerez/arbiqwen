import { Wrench } from 'lucide-react';
import type { ChatMessageView } from '../../chat/types';

// One message row. User and assistant turns are styled distinctly. Assistant
// content streams in as plain text (whitespace preserved); tool calls and
// citation counts render as compact, non-secret chips. No action controls.
export function ChatMessageBubble({ message }: { message: ChatMessageView }) {
  const isUser = message.role === 'user';
  return (
    <li className={`chat-msg chat-msg--${message.role}`} data-role={message.role}>
      <div className={`chat-msg__bubble${message.error ? ' chat-msg__bubble--error' : ''}`}>
        <p className="chat-msg__text">
          {message.content}
          {message.streaming && <span className="chat-msg__caret" aria-hidden="true" />}
        </p>

        {!isUser && message.toolCalls && message.toolCalls.length > 0 && (
          <div className="chat-msg__tools">
            {message.toolCalls.map((tool, index) => (
              <span className="chat-msg__tool" key={index}>
                <Wrench size={11} strokeWidth={2} />
                {tool.toolName ?? tool.skillKey ?? tool.integrationKey ?? 'tool'}
              </span>
            ))}
          </div>
        )}

        {!isUser && message.citations && message.citations.length > 0 && (
          <p className="chat-msg__cites">
            {message.citations.length} source{message.citations.length === 1 ? '' : 's'}
          </p>
        )}
      </div>
    </li>
  );
}
