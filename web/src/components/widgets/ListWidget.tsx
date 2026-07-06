import { useEffect, useState } from 'react';
import type { LucideIcon } from 'lucide-react';
import { Widget } from './Widget';

// Generic dashboard widget that loads a list and renders compact rows — used for
// Playbooks, Dashboards, and Active Agents (read-only). The empty state lives in
// the header hint, matching the desktop widgets.
export interface ListRow {
  id: string;
  label: string;
  status?: string;
}

interface ListWidgetProps {
  title: string;
  icon: LucideIcon;
  rowIcon: LucideIcon;
  emptyHint: string;
  loader: () => Promise<ListRow[]>;
}

export function ListWidget({ title, icon, rowIcon: RowIcon, emptyHint, loader }: ListWidgetProps) {
  const [rows, setRows] = useState<ListRow[] | null>(null);

  useEffect(() => {
    let cancelled = false;
    loader()
      .then((r) => {
        if (!cancelled) setRows(r);
      })
      .catch(() => {
        if (!cancelled) setRows([]);
      });
    return () => {
      cancelled = true;
    };
  }, [loader]);

  const count = rows?.length ?? 0;
  const hint = rows && rows.length === 0 ? emptyHint : undefined;

  return (
    <Widget title={title} icon={icon} count={count} hint={hint}>
      {rows && rows.length > 0 && (
        <div className="wlist">
          {rows.map((row) => (
            <div key={row.id} className="wrow wrow--static">
              <span className="wrow__icon">
                <RowIcon size={13} strokeWidth={1.5} />
              </span>
              <span className="wrow__main">
                <span className="wrow__name">{row.label}</span>
                {row.status && <span className="wrow__meta">{row.status}</span>}
              </span>
            </div>
          ))}
        </div>
      )}
    </Widget>
  );
}
