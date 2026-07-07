import { FileText } from 'lucide-react';
import { Widget } from './Widget';

export interface DocLike {
  id?: number | string;
  filename?: string;
}

// Documents widget, ported from the desktop DocumentsWidget but read-only: it
// lists the workspace's documents (no upload control in the browser demo).
export function DocumentsWidget({ documents }: { documents: DocLike[] }) {
  const hint = documents.length === 0 ? 'No documents yet' : undefined;
  const visible = documents.slice(0, 5);
  const overflow = documents.length - visible.length;
  return (
    <Widget title="Documents" icon={FileText} count={documents.length} hint={hint}>
      {visible.length > 0 && (
        <div className="wlist">
          {visible.map((doc, index) => (
            <div key={doc.id ?? index} className="wrow wrow--static">
              <span className="wrow__icon">
                <FileText size={13} strokeWidth={1.5} />
              </span>
              <span className="wrow__name">{doc.filename ?? 'Document'}</span>
            </div>
          ))}
          {overflow > 0 && <div className="wlist__more">+{overflow} more</div>}
        </div>
      )}
    </Widget>
  );
}
