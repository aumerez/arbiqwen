import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { ChatMessageView } from '../../chat/types';
import { ToolCallBubble } from './ToolCallBubble';

// One message row. User turns render as plain text; assistant turns render as
// GitHub-flavored markdown (lists, tables, code, links) like the desktop
// MessageContent. Tool calls render as desktop-style cards; citations as a
// compact line. No action controls.
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

        {isUser ? (
          <p className="chat-msg__text">{message.content}</p>
        ) : (
          <div className="chat-msg__text chat-msg__md">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
            {message.streaming && <span className="chat-msg__caret" aria-hidden="true" />}
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
