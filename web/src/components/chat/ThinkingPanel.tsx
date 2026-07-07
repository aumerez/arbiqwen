import { useState } from 'react';
import { Brain, ChevronRight } from 'lucide-react';
import type { ChatThinking } from '../../chat/types';

// Collapsible reasoning panel, ported from the desktop ThinkingPanel: shows the
// model's chain-of-thought, collapsed by default ("Thinking…" while streaming,
// "Thought · 3s" after).
function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  const seconds = ms / 1000;
  if (seconds < 60) return `${seconds.toFixed(seconds < 10 ? 1 : 0)}s`;
  const mins = Math.floor(seconds / 60);
  return `${mins}m ${Math.round(seconds - mins * 60)}s`;
}

export function ThinkingPanel({ thinking }: { thinking: ChatThinking }) {
  const [open, setOpen] = useState(false);
  const label = thinking.streaming ? 'Thinking…' : 'Thought';
  const duration = thinking.durationMs > 0 ? formatDuration(thinking.durationMs) : null;

  return (
    <div className="thinking">
      <button type="button" className="thinking__header" onClick={() => setOpen(!open)} aria-expanded={open}>
        <span className={`thinking__chevron${open ? ' thinking__chevron--open' : ''}`}>
          <ChevronRight size={12} />
        </span>
        <Brain size={12} strokeWidth={1.8} />
        <span className="thinking__label">{label}</span>
        {duration && <span className="thinking__duration">· {duration}</span>}
      </button>
      {open && <div className="thinking__body">{thinking.content || '(no content)'}</div>}
    </div>
  );
}
