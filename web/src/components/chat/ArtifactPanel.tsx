import { createContext, useCallback, useContext, useState, type ReactNode } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { X } from 'lucide-react';
import type { ArtifactsClient } from '../../api/http/artifactsClient';
import type { ArtifactView } from '../../chat/types';

// Right-side artifact preview, ported from the desktop ArtifactPreviewPanel.
// Clicking an artifact card opens this panel, which fetches the artifact content
// and renders HTML dashboards in a sandboxed iframe or markdown/text via the
// markdown renderer. Read-only: no download/add-to-KB actions here.

interface ArtifactPanelState {
  open: boolean;
  artifact: ArtifactView | null;
  contentType: string;
  content: string;
  loading: boolean;
  openPreview: (artifact: ArtifactView) => void;
  close: () => void;
}

const noop = () => {};
const ArtifactPanelContext = createContext<ArtifactPanelState>({
  open: false,
  artifact: null,
  contentType: '',
  content: '',
  loading: false,
  openPreview: noop,
  close: noop,
});

export function useArtifactPanel(): ArtifactPanelState {
  return useContext(ArtifactPanelContext);
}

export function ArtifactPanelProvider({ client, children }: { client: ArtifactsClient; children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const [artifact, setArtifact] = useState<ArtifactView | null>(null);
  const [contentType, setContentType] = useState('');
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(false);

  const openPreview = useCallback(
    (next: ArtifactView) => {
      setArtifact(next);
      setOpen(true);
      setLoading(true);
      setContent('');
      setContentType('');
      void client
        .getContent(next.id)
        .then((res) => {
          setContentType(res.contentType);
          setContent(res.text);
        })
        .catch(() => {
          setContentType('text/plain');
          setContent('Failed to load preview content.');
        })
        .finally(() => setLoading(false));
    },
    [client],
  );

  const close = useCallback(() => setOpen(false), []);

  return (
    <ArtifactPanelContext.Provider
      value={{ open, artifact, contentType, content, loading, openPreview, close }}
    >
      {children}
    </ArtifactPanelContext.Provider>
  );
}

export function ArtifactPanel() {
  const { open, artifact, contentType, content, loading, close } = useArtifactPanel();
  if (!open || !artifact) return null;

  const isHtml = contentType.toLowerCase().includes('html');
  const title = artifact.title || artifact.filename || 'Artifact';

  return (
    <aside className="artifact" aria-label="Artifact preview">
      <div className="artifact__header">
        <span className="artifact__title">{title}</span>
        <button type="button" className="artifact__close" onClick={close} aria-label="Close preview">
          <X size={16} strokeWidth={2} />
        </button>
      </div>
      <div className="artifact__body">
        {loading ? (
          <p className="artifact__loading">Loading preview…</p>
        ) : isHtml ? (
          <iframe className="artifact__frame" title={title} srcDoc={content} sandbox="" />
        ) : (
          <div className="artifact__md chat-msg__md">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
          </div>
        )}
      </div>
    </aside>
  );
}
