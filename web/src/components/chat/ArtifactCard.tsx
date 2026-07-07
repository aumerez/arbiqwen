import { BarChart3, Eye, FileText } from 'lucide-react';
import type { ArtifactView } from '../../chat/types';
import { useArtifactPanel } from './ArtifactPanel';

// Artifact card in an assistant message, ported from the desktop ArtifactCard
// (preview-only): an icon + title and a Preview action that opens the right-side
// panel. HTML artifacts (dashboards) get the chart icon; others the file icon.
export function ArtifactCard({ artifact }: { artifact: ArtifactView }) {
  const { openPreview } = useArtifactPanel();
  const isHtml = (artifact.contentType ?? '').toLowerCase().includes('html');
  const Icon = isHtml ? BarChart3 : FileText;
  const title = artifact.title || artifact.filename || 'Artifact';

  return (
    <button type="button" className="artifact-card" onClick={() => openPreview(artifact)}>
      <span className="artifact-card__icon">
        <Icon size={18} strokeWidth={1.5} />
      </span>
      <span className="artifact-card__title">{title}</span>
      <span className="artifact-card__preview">
        <Eye size={14} strokeWidth={1.75} />
        Preview
      </span>
    </button>
  );
}
