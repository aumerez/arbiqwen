import { useEffect, useRef, useState, type ChangeEvent, type FormEvent, type KeyboardEvent } from 'react';
import { AlertCircle, Check, FileText, Loader2, Paperclip, Send, Square, X } from 'lucide-react';
import type { DocumentsClient } from '../../api/http/documentsClient';

// Message composer, ported from the desktop ChatInput: a rounded container with
// the chip strip on top, the auto-growing textarea in the middle, and a controls
// bar at the bottom (paperclip left, send/stop right). Enter sends, Shift+Enter
// adds a newline. Attachments upload to the backend and inline as "📎 name
// [doc:id]" prose on send — the one write the read-only demo allows, since it's
// part of the chat flow.
interface ChatComposerProps {
  sending: boolean;
  onSend: (text: string) => void;
  onStop: () => void;
  /** A seeded draft (e.g. an agent template). Applied whenever its nonce
   *  changes so the same template can be re-applied. */
  draft?: { text: string; nonce: number };
  /** Enables the paperclip attach flow when provided. */
  documentsClient?: DocumentsClient;
  /** Scope uploads to the active project (null/undefined = global library). */
  projectId?: number | null;
}

// A file staged in the input but not yet sent. Lifecycle: uploading → indexing
// → ready (or error). Sending is blocked until every chip is ready.
interface StagedAttachment {
  tempId: string;
  name: string;
  size: number;
  status: 'uploading' | 'indexing' | 'ready' | 'error';
  documentId?: number;
  errorMessage?: string;
}

const POLL_MS = 3000;

function formatBytes(bytes?: number): string {
  if (!bytes) return '';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

export function ChatComposer({ sending, onSend, onStop, draft, documentsClient, projectId }: ChatComposerProps) {
  const [value, setValue] = useState('');
  const [staged, setStaged] = useState<StagedAttachment[]>([]);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  // Mirror of `staged` for the polling interval to read without stale closures.
  const stagedRef = useRef<StagedAttachment[]>([]);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    stagedRef.current = staged;
  }, [staged]);

  // Apply a seeded draft. Keyed on the nonce, not the text, so re-picking the
  // same template re-fills it; clears any stale chips from the previous chat.
  useEffect(() => {
    if (draft && draft.nonce > 0) {
      setValue(draft.text);
      setStaged([]);
    }
  }, [draft?.nonce]); // eslint-disable-line react-hooks/exhaustive-deps

  // Auto-resize like the desktop ChatInput: grow up to the CSS max (240px),
  // then scroll.
  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = 'auto';
    ta.style.height = `${Math.min(ta.scrollHeight, 240)}px`;
  }, [value]);

  const stopPoll = () => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  };

  // Stop the indexing poll on unmount.
  useEffect(() => () => stopPoll(), []);

  const updateChip = (tempId: string, patch: Partial<StagedAttachment>) =>
    setStaged((prev) => prev.map((a) => (a.tempId === tempId ? { ...a, ...patch } : a)));

  // One shared interval polls every indexing chip's status until it's indexed
  // or errored, then stops itself — mirrors the desktop's shared poll.
  const ensurePoll = () => {
    if (pollRef.current || !documentsClient) return;
    pollRef.current = setInterval(() => {
      const indexing = stagedRef.current.filter((a) => a.status === 'indexing' && a.documentId);
      if (indexing.length === 0) {
        stopPoll();
        return;
      }
      void Promise.all(
        indexing.map(async (a) => {
          try {
            const doc = await documentsClient.get(a.documentId!);
            if (doc.status === 'indexed') updateChip(a.tempId, { status: 'ready' });
            else if (doc.status === 'error') updateChip(a.tempId, { status: 'error', errorMessage: 'Indexing failed' });
          } catch {
            // Transient read error — keep polling on the next tick.
          }
        }),
      );
    }, POLL_MS);
  };

  const stageFiles = async (files: File[]) => {
    if (!documentsClient) return;
    for (const file of files) {
      const tempId = `chip_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
      setStaged((prev) => [...prev, { tempId, name: file.name, size: file.size, status: 'uploading' }]);
      try {
        const doc = await documentsClient.upload(file, projectId);
        const documentId = doc.id ? Number(doc.id) : 0;
        // On a content-hash collision the backend returns the existing doc,
        // already indexed — stage it ready and skip the poll.
        const ready = doc.status === 'indexed';
        updateChip(tempId, {
          documentId,
          size: typeof doc.size === 'number' ? doc.size : file.size,
          status: ready ? 'ready' : 'indexing',
        });
        if (!ready && documentId > 0) ensurePoll();
      } catch (err) {
        updateChip(tempId, { status: 'error', errorMessage: err instanceof Error ? err.message : 'Upload failed' });
      }
    }
  };

  const handlePick = (e: ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files ? Array.from(e.target.files) : [];
    // Reset the input so picking the same file again re-fires onChange.
    e.target.value = '';
    if (files.length > 0) void stageFiles(files);
  };

  const removeChip = (tempId: string) => setStaged((prev) => prev.filter((a) => a.tempId !== tempId));

  const hasUploading = staged.some((a) => a.status === 'uploading');
  const hasIndexing = staged.some((a) => a.status === 'indexing');
  const hasErrored = staged.some((a) => a.status === 'error');
  const allowSend = !hasUploading && !hasIndexing && !hasErrored;

  function submit() {
    const text = value.trim();
    if (sending || !allowSend) return;
    if (!text && staged.length === 0) return;

    // Inline ready attachments as "📎 name [doc:id]" prose lines above the text,
    // matching the desktop — the RAG pipeline embeds the filename and the LLM
    // reads it as natural language (not an opaque token).
    const fileLines = staged
      .filter((a) => a.status === 'ready' || a.status === 'indexing')
      .map((a) => (a.documentId && a.documentId > 0 ? `📎 ${a.name} [doc:${a.documentId}]` : `📎 ${a.name}`))
      .join('\n');
    const message = [fileLines, text].filter(Boolean).join('\n\n');

    onSend(message);
    setValue('');
    setStaged([]);
    stopPoll();
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    submit();
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      submit();
    }
  }

  const sendDisabled = sending ? false : (!value.trim() && staged.length === 0) || !allowSend;

  return (
    <form className="composer" onSubmit={handleSubmit} aria-label="Message composer">
      <div className={`composer__box${staged.length > 0 ? ' composer__box--has-chips' : ''}`}>
        {staged.length > 0 && (
          <div className="composer__chips">
            {staged.map((att) => (
              <div
                key={att.tempId}
                className={`composer__chip${att.status === 'error' ? ' composer__chip--error' : ''}`}
                title={att.errorMessage || att.name}
              >
                <FileText size={14} className="composer__chip-icon" />
                <div className="composer__chip-text">
                  <span className="composer__chip-name">{att.name}</span>
                  <span className="composer__chip-meta">
                    {att.status === 'uploading' && (
                      <>
                        <Loader2 size={11} className="composer__spin" /> Uploading…
                      </>
                    )}
                    {att.status === 'indexing' && (
                      <>
                        <Loader2 size={11} className="composer__spin" /> Indexing…
                      </>
                    )}
                    {att.status === 'ready' && (
                      <>
                        <Check size={11} /> Ready · {formatBytes(att.size)}
                      </>
                    )}
                    {att.status === 'error' && (
                      <>
                        <AlertCircle size={11} /> Failed
                      </>
                    )}
                  </span>
                </div>
                <button
                  type="button"
                  className="composer__chip-remove"
                  onClick={() => removeChip(att.tempId)}
                  aria-label={`Remove ${att.name}`}
                >
                  <X size={14} />
                </button>
              </div>
            ))}
          </div>
        )}

        <textarea
          ref={textareaRef}
          className="composer__input"
          value={value}
          onChange={(event) => setValue(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type your message…"
          rows={1}
          aria-label="Message input"
        />

        <div className="composer__controls">
          {documentsClient && (
            <>
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept=".pdf,.docx,.pptx,.xlsx,.txt,.md,.csv"
                className="composer__file-input"
                onChange={handlePick}
                tabIndex={-1}
                aria-hidden="true"
              />
              <button
                type="button"
                className="composer__attach"
                onClick={() => fileInputRef.current?.click()}
                aria-label="Attach document"
                title="Attach document"
              >
                <Paperclip size={18} strokeWidth={2} />
              </button>
            </>
          )}
          <div className="composer__spacer" />
          {sending ? (
            <button type="button" className="composer__btn composer__btn--stop" onClick={onStop} aria-label="Stop">
              <Square size={18} strokeWidth={2} />
            </button>
          ) : (
            <button
              type="submit"
              className="composer__btn"
              disabled={sendDisabled}
              aria-label="Send"
              title={
                hasUploading
                  ? 'Wait for uploads to finish'
                  : hasIndexing
                    ? 'Wait for indexing to finish'
                    : hasErrored
                      ? 'Remove failed attachments first'
                      : 'Send'
              }
            >
              <Send size={18} strokeWidth={2} />
            </button>
          )}
        </div>
      </div>
    </form>
  );
}
