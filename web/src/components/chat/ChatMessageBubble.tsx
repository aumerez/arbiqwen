import { Children, Fragment, useState, type ReactNode } from 'react';
import { AlertTriangle, Check, Copy, User } from 'lucide-react';
import ReactMarkdown, { type Components } from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { NucleusMark } from '../brand/NucleusMark';
import type { ChatCitation, ChatMessageView, ThinkingBlock } from '../../chat/types';
import { ToolCallBubble } from './ToolCallBubble';
import { ArtifactCard } from './ArtifactCard';
import { ThinkingPanel } from './ThinkingPanel';
import { useArtifactPanel } from './ArtifactPanel';

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

function CodeBlock({ code, language }: { code: string; language?: string }) {
  const [copied, setCopied] = useState(false);
  async function onCopy() {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // ignore
    }
  }
  return (
    <div className="codeblock">
      <button
        type="button"
        className="codeblock__copy"
        onClick={onCopy}
        aria-label={copied ? 'Copied' : 'Copy code'}
        title={copied ? 'Copied!' : 'Copy code'}
      >
        {copied ? <Check size={14} strokeWidth={2} /> : <Copy size={14} strokeWidth={2} />}
      </button>
      <pre className="codeblock__pre">
        <code className={language ? `language-${language}` : undefined}>{code}</code>
      </pre>
    </div>
  );
}

function renderWithCitations(
  children: ReactNode,
  citations: ChatCitation[],
  onCite: (c: ChatCitation) => void,
): ReactNode {
  return Children.map(children, (child) => {
    if (typeof child === 'string' && citations.length > 0 && /\[\d+\]/.test(child)) {
      return child.split(/(\[\d+\])/g).map((part, i) => {
        const m = part.match(/^\[(\d+)\]$/);
        if (m) {
          const num = parseInt(m[1], 10);
          const c = citations.find((x) => x.number === num);
          if (c) {
            return (
              <button
                key={i}
                type="button"
                className="citation"
                title={c.documentName || `Source ${num}`}
                onClick={() => onCite(c)}
              >
                [{num}]
              </button>
            );
          }
        }
        return part;
      });
    }
    return child;
  });
}

function Markdown({
  text,
  citations = [],
  onCite,
}: {
  text: string;
  citations?: ChatCitation[];
  onCite?: (c: ChatCitation) => void;
}) {
  const components: Components = {
    pre: ({ children }) => <>{children}</>,
    code: ({ className, children }) => {
      const codeText = String(children ?? '').replace(/\n$/, '');
      const language = className?.match(/language-(\w+)/)?.[1];
      const isBlock = !!language || codeText.includes('\n');
      return isBlock ? <CodeBlock code={codeText} language={language} /> : <code className="md-inline">{children}</code>;
    },
    table: ({ children }) => (
      <div className="md-table">
        <table>{children}</table>
      </div>
    ),
    a: ({ href, children }) => (
      <a href={href} target="_blank" rel="noopener noreferrer">
        {children}
      </a>
    ),
  };
  if (citations.length > 0 && onCite) {
    components.p = ({ children }) => <p>{renderWithCitations(children, citations, onCite)}</p>;
    components.li = ({ children }) => <li>{renderWithCitations(children, citations, onCite)}</li>;
  }
  return (
    <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
      {text}
    </ReactMarkdown>
  );
}

interface ChatMessageBubbleProps {
  message: ChatMessageView;
  isLastAssistant?: boolean;
}

export function ChatMessageBubble({ message, isLastAssistant = false }: ChatMessageBubbleProps) {
  const [copied, setCopied] = useState(false);
  const { openDocumentPreview } = useArtifactPanel();
  const isUser = message.role === 'user';
  const isError = !!message.error;
  const citations = message.citations ?? [];
  const onCite = (c: ChatCitation) =>
    openDocumentPreview({ documentId: c.documentId ?? 0, documentName: c.documentName || `Source ${c.number ?? ''}` });

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
                    <Markdown text={b.content} citations={citations} onCite={onCite} />
                  </div>
                ))}
                <ToolCallBubble tool={tool} />
              </Fragment>
            ))}
            {trailing.map((b, bi) => (
              <div key={`bt-${bi}`} className="chat-msg__thinking chat-msg__md">
                <Markdown text={b.content} citations={citations} onCite={onCite} />
              </div>
            ))}
          </div>
        )}

        {showBubble && (
          <div className={`chat-msg__bubble chat-msg__md${bodyIsThinking ? ' chat-msg__thinking' : ''}`}>
            <Markdown text={message.content} citations={citations} onCite={onCite} />
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

        {!isUser && citations.length > 0 && (
          <div className="chat-msg__sources">
            <div className="chat-msg__sources-title">
              Source{citations.length === 1 ? '' : 's'}
            </div>
            {citations.map((c, i) => (
              <button
                key={i}
                type="button"
                className="chat-msg__source"
                onClick={() => onCite(c)}
                disabled={!c.documentId}
                title={c.documentId ? `Open ${c.documentName || `Source ${c.number}`}` : c.documentName || ''}
              >
                <span className="citation">[{c.number}]</span>
                <span className="chat-msg__source-name">{c.documentName || `Source ${c.number}`}</span>
              </button>
            ))}
          </div>
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
              {copied ? <Check size={16} strokeWidth={2} /> : <Copy size={16} strokeWidth={2} />}
            </button>
          )}
        </div>
      </div>
    </li>
  );
}
