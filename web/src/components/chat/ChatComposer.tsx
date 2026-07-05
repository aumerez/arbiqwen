import { useState, type FormEvent, type KeyboardEvent } from 'react';
import { Send, Square } from 'lucide-react';

// Message composer. Enter sends; Shift+Enter inserts a newline. While a response
// streams, the send button becomes a stop control. The only actions are send and
// stop — no uploads, no attachments, no tool/agent controls.
interface ChatComposerProps {
  sending: boolean;
  onSend: (text: string) => void;
  onStop: () => void;
}

export function ChatComposer({ sending, onSend, onStop }: ChatComposerProps) {
  const [value, setValue] = useState('');

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
      <textarea
        className="composer__input"
        value={value}
        onChange={(event) => setValue(event.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask the assistant…"
        rows={1}
      />
      {sending ? (
        <button type="button" className="composer__btn composer__btn--stop" onClick={onStop} aria-label="Stop">
          <Square size={15} strokeWidth={2} />
        </button>
      ) : (
        <button type="submit" className="composer__btn" disabled={!value.trim()} aria-label="Send">
          <Send size={15} strokeWidth={2} />
        </button>
      )}
    </form>
  );
}
