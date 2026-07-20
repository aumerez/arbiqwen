import { createContext, useCallback, useContext, useState, type ReactNode } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { X } from 'lucide-react';
import type { ArtifactsClient } from '../../api/http/artifactsClient';
import type { DocumentsClient } from '../../api/http/documentsClient';
import type { ArtifactView } from '../../chat/types';

// Right-side preview panel, ported from the desktop ArtifactPreviewPanel. Opens
// for an artifact (a skill output) or a source document (clicked citation):
// HTML renders in a sandboxed iframe, PDFs/images via a blob URL, and
// markdown/text via the markdown renderer. Read-only.
export interface DocumentPreview {
  documentId?: number;
  documentName: string;
  pageNumber?: number;
  snippet?: string;
}

interface PanelState {
  open: boolean;
  title: string;
  contentType: string;
  text: string;
  url: string | null;
  snippet: string;
  loading: boolean;
  openPreview: (artifact: ArtifactView) => void;
  openDocumentPreview: (doc: DocumentPreview) => void;
  close: () => void;
}

const noop = () => {};
const PanelContext = createContext<PanelState>({
  open: false,
  title: '',
  contentType: '',
  text: '',
  url: null,
  snippet: '',
  loading: false,
  openPreview: noop,
  openDocumentPreview: noop,
  close: noop,
});

export function useArtifactPanel(): PanelState {
  return useContext(PanelContext);
}

export function ArtifactPanelProvider({
  artifactsClient,
  documentsClient,
  children,
}: {
  artifactsClient: ArtifactsClient;
  documentsClient: DocumentsClient;
  children: ReactNode;
}) {
  const [open, setOpen] = useState(false);
  const [title, setTitle] = useState('');
  const [contentType, setContentType] = useState('');
  const [text, setText] = useState('');
  const [url, setUrl] = useState<string | null>(null);
  const [snippet, setSnippet] = useState('');
  const [loading, setLoading] = useState(false);

  const begin = useCallback((nextTitle: string) => {
    setTitle(nextTitle);
    setOpen(true);
    setLoading(true);
    setText('');
    setUrl(null);
    setSnippet('');
    setContentType('');
  }, []);

  const openPreview = useCallback(
    (artifact: ArtifactView) => {
      begin(artifact.title || artifact.filename || 'Artifact');
      void artifactsClient
        .getContent(artifact.id)
        .then((res) => {
          setContentType(res.contentType);
          setText(res.text);
        })
        .catch(() => {
          setContentType('text/plain');
          setText('Failed to load preview content.');
        })
        .finally(() => setLoading(false));
    },
    [artifactsClient, begin],
  );

  const openDocumentPreview = useCallback(
    (doc: DocumentPreview) => {
      // Always open the panel — matching the desktop. Citations from a
      // qdrant-style knowledge base carry no local documentId (it arrives
      // null), so there's no file to fetch; we show the cited snippet
      // instead of silently doing nothing.
      begin(doc.documentName || `Source ${doc.documentId ?? ''}`);
      setSnippet(doc.snippet ?? '');
      if (!doc.documentId) {
        setLoading(false);
        return;
      }
      void documentsClient
        .getFile(doc.documentId)
        .then((res) => {
          setContentType(res.contentType);
          if (res.url) setUrl(res.url);
          else setText(res.text ?? '');
        })
        .catch(() => {
          setContentType('text/plain');
          setText('Failed to load document.');
        })
        .finally(() => setLoading(false));
    },
    [documentsClient, begin],
  );

  const close = useCallback(() => setOpen(false), []);

  return (
    <PanelContext.Provider
      value={{ open, title, contentType, text, url, snippet, loading, openPreview, openDocumentPreview, close }}
    >
      {children}
    </PanelContext.Provider>
  );
}

export function ArtifactPanel() {
  const { open, title, contentType, text, url, snippet, loading, close } = useArtifactPanel();
  if (!open) return null;

  const isHtml = contentType.toLowerCase().includes('html');
  const hasContent = !!url || !!text;

  return (
    <aside className="artifact" aria-label="Preview">
      <div className="artifact__header">
        <span className="artifact__title">{title}</span>
        <button type="button" className="artifact__close" onClick={close} aria-label="Close preview">
          <X size={16} strokeWidth={2} />
        </button>
      </div>
      <div className="artifact__body">
        {loading ? (
          <p className="artifact__loading">Loading preview…</p>
        ) : url ? (
          // Blob URL of a fetched document, gated to PDF/image content types in
          // documentsClient.getFile. Sandboxed: allow-same-origin lets the
          // browser's native PDF/image viewer render the same-origin blob, but
          // withholding allow-scripts means no embedded script can run, reach
          // the parent, or read app state.
          <iframe className="artifact__frame" title={title} src={url} sandbox="allow-same-origin" />
        ) : isHtml ? (
          // Untrusted HTML (skill output). Fully sandboxed: no scripts, no
          // same-origin, no top navigation, no popups.
          <iframe className="artifact__frame" title={title} srcDoc={text} sandbox="" />
        ) : hasContent ? (
          <div className="artifact__md chat-msg__md">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{text}</ReactMarkdown>
          </div>
        ) : snippet ? (
          // No fetchable document (qdrant-sourced citation) — show the cited
          // excerpt, mirroring the desktop's "Source excerpt" fallback.
          <div className="artifact__excerpt">
            <p className="artifact__excerpt-label">Source excerpt</p>
            <blockquote className="artifact__excerpt-quote">{snippet}</blockquote>
          </div>
        ) : (
          <p className="artifact__loading">No preview available.</p>
        )}
      </div>
    </aside>
  );
}
