import type { ChatMessageView } from '../../chat/types';
import { ToolCallBubble } from './ToolCallBubble';

// One message row. User and assistant turns are styled distinctly. Assistant
// content streams in as plain text (whitespace preserved); tool calls render as
// desktop-style cards and citation counts as a compact line. No action controls.
export function ChatMessageBubble({ message }: { message: ChatMessageView }) {
  const isUser = message.role === 'user';
  return (
    <li className={`chat-msg chat-msg--${message.role}`} data-role={message.role}>
      <div className={`chat-msg__bubble${message.error ? ' chat-msg__bubble--error' : ''}`}>
        {!isUser && message.toolCalls && message.toolCalls.length > 0 && (
          <div className="chat-msg__tools">
            {message.toolCalls.map((tool, index) => (
              <ToolCallBubble key={tool.id ?? index} tool={tool} />
            ))}
          </div>
        )}

        <p className="chat-msg__text">
          {message.content}
          {message.streaming && <span className="chat-msg__caret" aria-hidden="true" />}
        </p>

        {!isUser && message.citations && message.citations.length > 0 && (
          <p className="chat-msg__cites">
            {message.citations.length} source{message.citations.length === 1 ? '' : 's'}
          </p>
        )}
      </div>
    </li>
  );
}
