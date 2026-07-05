import type { ReactNode } from 'react';
import type { LucideIcon } from 'lucide-react';

// Dashboard widget chrome, ported from the desktop Widget: a section header
// (icon + title + count + right-aligned hint) over a body. The desktop's
// size-toggle / maximize controls are hidden in v1, so they're omitted here.
interface WidgetProps {
  title: string;
  icon: LucideIcon;
  count?: number;
  hint?: string;
  children?: ReactNode;
}

export function Widget({ title, icon: Icon, count, hint, children }: WidgetProps) {
  return (
    <section className="widget">
      <div className="widget__header">
        <Icon size={16} strokeWidth={1.5} />
        <h2 className="widget__title">{title}</h2>
        {count !== undefined && <span className="widget__count">{count}</span>}
        {hint && <span className="widget__hint">{hint}</span>}
      </div>
      <div className="widget__body">{children}</div>
    </section>
  );
}
