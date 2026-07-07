import { Fragment, useState } from 'react';
import { AlertTriangle, Check, Copy, User } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { NucleusMark } from '../brand/NucleusMark';
import type { ChatMessageView, ThinkingBlock } from '../../chat/types';
import { ToolCallBubble } from './ToolCallBubble';
import { ArtifactCard } from './ArtifactCard';
import { ThinkingPanel } from './ThinkingPanel';

// One message row, ported from the desktop ChatMessage. Assistant turns render
// the Nucleus-mark avatar, an optional reasoning panel, then thinking segments
// interleaved with tool cards, the synthesis body, artifact cards, and a footer
// (timestamp + hover copy). User turns mirror to the right. The body is flat
// markdown (no colored bubble), matching the desktop.
function formatTime(iso?: string): string {
  if (!iso) return '';
  const d = new Date(iso);
  return d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });
}

function Markdown({ text }: { text: string }) {
  return <ReactMarkdown remarkPlugins={[remarkGfm]}>{text}</ReactMarkdown>;
}

interface ChatMessageBubbleProps {
  message: ChatMessageView;
  isLastAssistant?: boolean;
}

export function ChatMessageBubble({ message, isLastAssistant = false }: ChatMessageBubbleProps) {
  const [copied, setCopied] = useState(false);
  const isUser = message.role === 'user';
  const isError = !!message.error;

  const tools = message.toolCalls ?? [];
  const blocks = message.thinkingBlocks ?? [];
  const blocksByTool = new Map<number, ThinkingBlock[]>();
  const trailing: ThinkingBlock[] = [];
  for (const b of blocks) {
    if (b.beforeToolIndex >= tools.length) trailing.push(b);
    else blocksByTool.set(b.beforeToolIndex, [...(blocksByTool.get(b.beforeToolIndex) ?? []), b]);
  }
  const hasRounds = !isUser && (tools.length > 0 || blocks.length > 0);
  const bodyIsThinking = !!message.streaming && !message.inSynthesis && hasRounds;
  const showBubble = message.content.length > 0 || (!!message.streaming && !isUser);

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

        {hasRounds && (
          <div className="chat-msg__rounds">
            {tools.map((tool, idx) => (
              <Fragment key={tool.id ?? idx}>
                {(blocksByTool.get(idx) ?? []).map((b, bi) => (
                  <div key={`b-${idx}-${bi}`} className="chat-msg__thinking chat-msg__md">
                    <Markdown text={b.content} />
                  </div>
                ))}
                <ToolCallBubble tool={tool} />
              </Fragment>
            ))}
            {trailing.map((b, bi) => (
              <div key={`bt-${bi}`} className="chat-msg__thinking chat-msg__md">
                <Markdown text={b.content} />
              </div>
            ))}
          </div>
        )}

        {showBubble && (
          <div className={`chat-msg__bubble chat-msg__md${bodyIsThinking ? ' chat-msg__thinking' : ''}`}>
            <Markdown text={message.content} />
            {message.streaming && <span className="chat-msg__caret" aria-hidden="true" />}
          </div>
        )}

        {!isUser && message.artifacts && message.artifacts.length > 0 && (
          <div className="chat-msg__artifacts">
            {message.artifacts.map((artifact) => (
              <ArtifactCard key={artifact.id} artifact={artifact} />
            ))}
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
