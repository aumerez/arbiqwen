import { useMemo, useState } from 'react';
import { Download, FolderOpen, Globe, Search, X } from 'lucide-react';
import type { DocumentsClient } from '../api/http/documentsClient';
import type { ProjectView } from '../projects/useProjects';
import {
  fileIcon,
  formatDate,
  formatFileSize,
  indexModeBadge,
  statusBadge,
  type DocumentRow,
} from '../documents/documentMeta';

// Read-only Documents page, ported from the desktop full-screen DocumentsWidget
// (Finder-style browser). A left "Sources" sidebar switches scope — All, the
// Global company library, or a specific project — and the right pane is a
// searchable list with indexing status, size, date, and a download. Folder
// navigation, Drive, and the mosaic view are omitted (folders/Drive are
// separate endpoints / OAuth surfaces, out of scope for the read-only demo).
type Scope = 'all' | 'global' | number;

interface DocumentsViewProps {
  documents: DocumentRow[];
  documentsClient: DocumentsClient;
  projects: ProjectView[];
}

export function DocumentsView({ documents, documentsClient, projects }: DocumentsViewProps) {
  const [query, setQuery] = useState('');
  const [scope, setScope] = useState<Scope>('all');

  // Only projects that actually own documents get a source entry, so the
  // sidebar mirrors what's browsable (matches the desktop's populated sources).
  const projectsWithDocs = useMemo(() => {
    const ids = new Set(documents.map((d) => d.project_id).filter((id): id is number => id != null));
    return projects.filter((p) => ids.has(p.id));
  }, [documents, projects]);

  const scoped = useMemo(() => {
    if (scope === 'all') return documents;
    if (scope === 'global') return documents.filter((d) => d.project_id == null);
    return documents.filter((d) => d.project_id === scope);
  }, [documents, scope]);

  const normalized = query.trim().toLowerCase();
  const filtered = useMemo(() => {
    if (!normalized) return scoped;
    return scoped.filter((d) => (d.filename ?? '').toLowerCase().includes(normalized));
  }, [scoped, normalized]);

  const download = (doc: DocumentRow) => {
    void documentsClient
      .getBlob(doc.id)
      .then((blob) => {
        const objectUrl = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = objectUrl;
        a.download = doc.filename || `document-${doc.id}`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(objectUrl);
      })
      .catch(() => {});
  };

  const countFor = (s: Scope) =>
    s === 'all'
      ? documents.length
      : s === 'global'
        ? documents.filter((d) => d.project_id == null).length
        : documents.filter((d) => d.project_id === s).length;

  const sourceButton = (s: Scope, label: string, Icon: typeof Globe) => (
    <button
      type="button"
      className={`docs__source${scope === s ? ' docs__source--active' : ''}`}
      aria-current={scope === s ? 'true' : undefined}
      onClick={() => setScope(s)}
    >
      <Icon size={15} strokeWidth={1.5} />
      <span className="docs__source-label">{label}</span>
      <span className="docs__source-count">{countFor(s)}</span>
    </button>
  );

  return (
    <section className="docs" data-section="documents" aria-labelledby="heading-documents">
      <aside className="docs__sources" aria-label="Document sources">
        <div className="docs__sources-title">Sources</div>
        {sourceButton('all', 'All documents', FolderOpen)}
        {sourceButton('global', 'Company library', Globe)}
        {projectsWithDocs.length > 0 && <div className="docs__sources-title">Projects</div>}
        {projectsWithDocs.map((p) => sourceButton(p.id, p.name, FolderOpen))}
      </aside>

      <div className="docs__main">
        <div className="page__header">
          <h1 id="heading-documents" className="page__title">
            Documents
          </h1>
          <p className="page__desc">Files in this workspace's knowledge base, listed read-only with indexing status.</p>
          <div className="searchbox">
            <Search size={14} strokeWidth={1.75} aria-hidden="true" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search documents"
              aria-label="Search documents"
            />
            {query && (
              <button type="button" className="searchbox__clear" onClick={() => setQuery('')} aria-label="Clear search">
                <X size={14} strokeWidth={1.75} />
              </button>
            )}
          </div>
        </div>

        {documents.length === 0 ? (
          <p className="empty" role="status">
            No documents to show.
          </p>
        ) : filtered.length === 0 ? (
          <p className="empty" role="status">
            {normalized ? `No documents match “${query}”.` : 'No documents in this source.'}
          </p>
        ) : (
          <ul className="card-list">
            {filtered.map((doc) => {
              const Icon = fileIcon(doc.mimetype);
              const status = statusBadge(doc.status);
              const idxMode = indexModeBadge(doc.index_mode);
              const docScope = doc.project_id == null ? 'Global' : doc.project_name || `Project ${doc.project_id}`;
              return (
                <li key={doc.id} className="card doc-row">
                  <span className="card__icon">
                    <Icon size={18} strokeWidth={1.5} />
                  </span>
                  <div className="card__content">
                    <p className="card__name">
                      <span className="doc-row__name">{doc.filename || `Document ${doc.id}`}</span>
                    </p>
                    <div className="doc-row__badges">
                      <span className="badge badge--read">{docScope}</span>
                      <span className={`badge ${status.cls}`}>{status.label}</span>
                      {idxMode && <span className={`badge ${idxMode.cls}`}>{idxMode.label}</span>}
                    </div>
                  </div>
                  <div className="card__meta doc-row__meta">
                    {doc.size != null && <span className="card__metric">{formatFileSize(doc.size)}</span>}
                    {doc.created_at && <span className="card__metric">{formatDate(doc.created_at)}</span>}
                    <button
                      type="button"
                      className="doc-row__action"
                      onClick={() => download(doc)}
                      title={`Download ${doc.filename ?? 'document'}`}
                      aria-label={`Download ${doc.filename ?? 'document'}`}
                    >
                      <Download size={15} strokeWidth={1.75} />
                    </button>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </section>
  );
}
