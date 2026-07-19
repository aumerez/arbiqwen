import { useEffect, useRef, useState, type FormEvent, type KeyboardEvent } from 'react';
import { Send, Square } from 'lucide-react';

// Message composer, ported from the desktop ChatInput: a bordered field that
// highlights on focus, with Enter to send / Shift+Enter for a newline. While a
// response streams the send button becomes a stop control. Send/stop only — no
// uploads or attachments in the browser demo.
interface ChatComposerProps {
  sending: boolean;
  onSend: (text: string) => void;
  onStop: () => void;
  /** A seeded draft (e.g. an agent template). Applied whenever its nonce
   *  changes so the same template can be re-applied. */
  draft?: { text: string; nonce: number };
}

export function ChatComposer({ sending, onSend, onStop, draft }: ChatComposerProps) {
  const [value, setValue] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Apply a seeded draft into the field. Keyed on the nonce, not the text, so
  // re-picking the same template still re-fills it.
  useEffect(() => {
    if (draft && draft.nonce > 0) setValue(draft.text);
  }, [draft?.nonce]); // eslint-disable-line react-hooks/exhaustive-deps

  // Auto-resize like the desktop ChatInput: grow with content up to the CSS
  // max-height (240px), then scroll. Runs after every value change, including
  // the reset to '' on send and a seeded draft.
  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = 'auto';
    ta.style.height = `${Math.min(ta.scrollHeight, 240)}px`;
  }, [value]);

  function submit() {
    const text = value.trim();
    if (!text || sending) return;
    onSend(text);
    setValue('');
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

  return (
    <form className="composer" onSubmit={handleSubmit} aria-label="Message composer">
      <div className="composer__field">
        <textarea
          ref={textareaRef}
          className="composer__input"
          value={value}
          onChange={(event) => setValue(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type your message…"
          rows={1}
        />
        {sending ? (
          <button type="button" className="composer__btn composer__btn--stop" onClick={onStop} aria-label="Stop">
            <Square size={18} strokeWidth={2} />
          </button>
        ) : (
          <button type="submit" className="composer__btn" disabled={!value.trim()} aria-label="Send">
            <Send size={18} strokeWidth={2} />
          </button>
        )}
      </div>
    </form>
  );
}
