import { useEffect, useState, type ReactNode } from 'react';
import { Maximize2, Minimize2, type LucideIcon } from 'lucide-react';

// Dashboard widget chrome, ported from the desktop Widget: a section header
// (icon + title + count + right-aligned hint) over a body. When `expandable`
// and a `renderFull` is provided, the header shows a maximize button that opens
// a full-page overlay (Esc / the minimize button closes it) — the desktop's
// full-screen mode. The size-toggle axis (row/small/normal) is hidden in v1 on
// the desktop too, so it's omitted here.
interface WidgetProps {
  title: string;
  icon: LucideIcon;
  count?: number;
  hint?: string;
  children?: ReactNode;
  /** Extra header controls, left of the maximize button. */
  headerActions?: ReactNode;
  /** Show the maximize button (only takes effect when renderFull is set). */
  expandable?: boolean;
  /** Full-page overlay content, rendered when the widget is maximized. */
  renderFull?: () => ReactNode;
}

export function Widget({ title, icon: Icon, count, hint, children, headerActions, expandable, renderFull }: WidgetProps) {
  const [full, setFull] = useState(false);
  const canExpand = !!expandable && !!renderFull;

  // Esc closes the overlay — bound only while open so we don't fight other
  // keystroke handlers (mirrors the desktop Widget).
  useEffect(() => {
    if (!full) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        setFull(false);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [full]);

  const hasActions = !!headerActions || canExpand;

  return (
    <>
      <section className="widget">
        <div className="widget__header">
          <Icon size={16} strokeWidth={1.5} />
          <h2 className="widget__title">{title}</h2>
          {count !== undefined && <span className="widget__count">{count}</span>}
          {hint && <span className="widget__hint">{hint}</span>}
          {hasActions && (
            <div className="widget__actions">
              {headerActions}
              {canExpand && (
                <button
                  type="button"
                  className="widget__expand"
                  onClick={() => setFull(true)}
                  title="Expand to full page"
                  aria-label={`Expand ${title}`}
                >
                  <Maximize2 size={14} strokeWidth={1.75} />
                </button>
              )}
            </div>
          )}
        </div>
        <div className="widget__body">{children}</div>
      </section>

      {full && renderFull && (
        <div className="widget-overlay" role="dialog" aria-label={title} aria-modal="true">
          <div className="widget-overlay__header">
            <Icon size={16} strokeWidth={1.5} />
            <h2 className="widget__title">{title}</h2>
            {count !== undefined && <span className="widget__count">{count}</span>}
            <button
              type="button"
              className="widget__expand widget-overlay__close"
              onClick={() => setFull(false)}
              title="Collapse"
              aria-label={`Collapse ${title}`}
            >
              <Minimize2 size={14} strokeWidth={1.75} />
            </button>
          </div>
          <div className="widget-overlay__body">{renderFull()}</div>
        </div>
      )}
    </>
  );
}
