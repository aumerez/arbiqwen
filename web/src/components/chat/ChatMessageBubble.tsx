import { useState } from 'react';
import { AlertTriangle, Check, Copy, User } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { NucleusMark } from '../brand/NucleusMark';
import type { ChatMessageView } from '../../chat/types';
import { ToolCallBubble } from './ToolCallBubble';
import { ThinkingPanel } from './ThinkingPanel';

// One message row, ported from the desktop ChatMessage: an avatar (the Nucleus
// mark for the assistant, a user icon for you), the markdown body in an
// asymmetric bubble, a collapsible thinking panel, tool-call cards, and a footer
// with the timestamp and a hover copy button. Assistant rows sit left; user rows
// mirror to the right.
function formatTime(iso?: string): string {
  if (!iso) return '';
  const d = new Date(iso);
  return d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });
}

interface ChatMessageBubbleProps {
  message: ChatMessageView;
  isLastAssistant?: boolean;
}

export function ChatMessageBubble({ message, isLastAssistant = false }: ChatMessageBubbleProps) {
  const [copied, setCopied] = useState(false);
  const isUser = message.role === 'user';
  const isError = !!message.error;
  const showBubble = message.content.length > 0 || (message.streaming && !isUser);

  async function copy() {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard unavailable — ignore.
    }
  }

  return (
    <li className={`chat-msg chat-msg--${message.role}${isError ? ' chat-msg--error' : ''}`} data-role={message.role}>
      <div className="chat-msg__avatar">
        {isError ? (
          <AlertTriangle size={18} strokeWidth={1.5} className="chat-msg__erricon" />
        ) : isUser ? (
          <User size={18} strokeWidth={1.5} />
        ) : (
          <NucleusMark size={20} spinSeconds={8} />
        )}
      </div>

      <div className="chat-msg__content">
        {!isUser && message.thinking && <ThinkingPanel thinking={message.thinking} />}

        {!isUser && message.toolCalls && message.toolCalls.length > 0 && (
          <div className="chat-msg__tools">
            {message.toolCalls.map((tool, index) => (
              <ToolCallBubble key={tool.id ?? index} tool={tool} />
            ))}
          </div>
        )}

        {showBubble && (
          <div className="chat-msg__bubble">
            {isUser ? (
              <p className="chat-msg__text">{message.content}</p>
            ) : (
              <div className="chat-msg__text chat-msg__md">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
                {message.streaming && <span className="chat-msg__caret" aria-hidden="true" />}
              </div>
            )}
          </div>
        )}

        {!isUser && message.citations && message.citations.length > 0 && (
          <p className="chat-msg__cites">
            {message.citations.length} source{message.citations.length === 1 ? '' : 's'}
          </p>
        )}

        <div className="chat-msg__footer">
          <span className="chat-msg__time">{formatTime(message.createdAt)}</span>
          {!message.streaming && (
            <button
              type="button"
              className={`chat-msg__copy${!isUser && isLastAssistant ? ' chat-msg__copy--visible' : ''}`}
              onClick={copy}
              title={copied ? 'Copied!' : 'Copy message'}
              aria-label="Copy message"
            >
              {copied ? <Check size={15} strokeWidth={2} /> : <Copy size={15} strokeWidth={2} />}
            </button>
          )}
        </div>
      </div>
    </li>
  );
}
