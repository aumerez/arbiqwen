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
  documentId: number;
  documentName: string;
}

interface PanelState {
  open: boolean;
  title: string;
  contentType: string;
  text: string;
  url: string | null;
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
  const [loading, setLoading] = useState(false);

  const begin = useCallback((nextTitle: string) => {
    setTitle(nextTitle);
    setOpen(true);
    setLoading(true);
    setText('');
    setUrl(null);
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
      if (!doc.documentId) return;
      begin(doc.documentName || `Source ${doc.documentId}`);
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
      value={{ open, title, contentType, text, url, loading, openPreview, openDocumentPreview, close }}
    >
      {children}
    </PanelContext.Provider>
  );
}

export function ArtifactPanel() {
  const { open, title, contentType, text, url, loading, close } = useArtifactPanel();
  if (!open) return null;

  const isHtml = contentType.toLowerCase().includes('html');

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
          <iframe className="artifact__frame" title={title} src={url} />
        ) : isHtml ? (
          <iframe className="artifact__frame" title={title} srcDoc={text} sandbox="" />
        ) : (
          <div className="artifact__md chat-msg__md">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{text}</ReactMarkdown>
          </div>
        )}
      </div>
    </aside>
  );
}
