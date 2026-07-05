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
  return (
    <Widget title="Documents" icon={FileText} count={documents.length} hint={hint}>
      {documents.length > 0 && (
        <div className="wlist">
          {documents.map((doc, index) => (
            <div key={doc.id ?? index} className="wrow wrow--static">
              <span className="wrow__icon">
                <FileText size={13} strokeWidth={1.5} />
              </span>
              <span className="wrow__name">{doc.filename ?? 'Document'}</span>
            </div>
          ))}
        </div>
      )}
    </Widget>
  );
}
