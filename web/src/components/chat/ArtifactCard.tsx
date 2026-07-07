import { BarChart3, Eye, FileText } from 'lucide-react';
import type { ArtifactView } from '../../chat/types';
import { useArtifactPanel } from './ArtifactPanel';

// Artifact card in an assistant message, ported from the desktop ArtifactCard:
// an accent icon chip, the title + filename, and an actions area with an Eye
// (preview) button that opens the right-side panel. HTML artifacts (dashboards)
// get the chart icon; others the file icon. Read-only — no download/add-to-KB.
export function ArtifactCard({ artifact }: { artifact: ArtifactView }) {
  const { openPreview } = useArtifactPanel();
  const isHtml = (artifact.contentType ?? '').toLowerCase().includes('html');
  const Icon = isHtml ? BarChart3 : FileText;
  const title = artifact.title || artifact.filename || 'Artifact';

  return (
    <div className="artifact-card">
      <div className="artifact-card__icon">
        <Icon size={18} strokeWidth={1.5} />
      </div>
      <div className="artifact-card__info">
        <span className="artifact-card__title">{title}</span>
        {artifact.filename && <span className="artifact-card__filename">{artifact.filename}</span>}
      </div>
      <div className="artifact-card__actions">
        <button
          type="button"
          className="artifact-card__action"
          onClick={() => openPreview(artifact)}
          title="Preview"
          aria-label="Preview artifact"
        >
          <Eye size={16} strokeWidth={1.5} />
        </button>
      </div>
    </div>
  );
}
