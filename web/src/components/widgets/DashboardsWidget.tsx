import { useEffect, useState } from 'react';
import { LayoutDashboard } from 'lucide-react';
import type { WorkspaceClient, RawDashboard } from '../../api/http/workspaceClient';
import { useArtifactPanel } from '../chat/ArtifactPanel';
import { Widget } from './Widget';

// Ported from the desktop DashboardsWidget (read-only subset). Dashboards are
// created and refreshed through chat (skill_dashboard_draw); this widget is a
// viewer: clicking a dashboard opens its cached HTML render in the preview
// panel — the same panel the artifact cards use. Rows that were never rendered
// (no cached artifact) are shown but not clickable. No delete / edit-in-chat
// (those are write/chat surfaces, out of scope for the browser demo).

// Module-scoped so Date.now() doesn't run during render (react-hooks purity),
// matching the desktop widget.
function timeAgo(dateStr?: string | null): string {
  if (!dateStr) return '';
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

const TEMPLATE_LABELS: Record<string, string> = {
  executive_summary: 'Executive',
  operational_dashboard: 'Operational',
};
function formatTemplate(template: string): string {
  return TEMPLATE_LABELS[template] ?? template.replace(/_/g, ' ');
}

function metaFor(d: RawDashboard, showProject: boolean): string {
  const parts: string[] = [];
  if (showProject && d.project_id != null) parts.push(`Project ${d.project_id}`);
  const sections = d.sections?.length ?? 0;
  if (sections > 0) parts.push(`${sections} section${sections === 1 ? '' : 's'}`);
  const ago = timeAgo(d.last_rendered_at);
  if (ago) parts.push(ago);
  if (!d.cached_artifact_id) parts.push('not rendered');
  return parts.join(' · ');
}

const LIMIT = 5;

interface DashboardsWidgetProps {
  workspaceClient: WorkspaceClient;
  projectId: number;
  isDefault: boolean;
}

export function DashboardsWidget({ workspaceClient, projectId, isDefault }: DashboardsWidgetProps) {
  const { openPreview } = useArtifactPanel();
  const [rows, setRows] = useState<RawDashboard[] | null>(null);

  // My Space lists every project's dashboards; a project lists only its own.
  const listId = isDefault ? null : projectId;

  useEffect(() => {
    let cancelled = false;
    workspaceClient
      .listDashboards(listId)
      .then((r) => {
        if (!cancelled) setRows(r);
      })
      .catch(() => {
        if (!cancelled) setRows([]);
      });
    return () => {
      cancelled = true;
    };
  }, [workspaceClient, listId]);

  const count = rows?.length ?? 0;
  const hint = rows && rows.length === 0 ? 'No dashboards yet' : undefined;
  const visible = rows ? rows.slice(0, LIMIT) : [];
  const overflow = count - visible.length;

  const open = (d: RawDashboard) => {
    if (!d.cached_artifact_id) return; // never rendered — nothing cached to show
    openPreview({
      id: d.cached_artifact_id,
      filename: `${d.title}.html`,
      title: d.short_name || d.title,
      contentType: 'text/html',
    });
  };

  // Full-page overlay: a card grid of every dashboard (click → preview) plus a
  // Marketplace stub, mirroring the desktop full view (read-only — no delete /
  // edit-in-chat).
  const renderFull = () => (
    <div className="fullview">
      <section>
        <h3 className="fullview__section-title">
          Your dashboards
          {count > 0 && <span className="fullview__lead">{count} total</span>}
        </h3>
        {count === 0 ? (
          <div className="fullview__empty">No dashboards yet — ask the assistant to draw one.</div>
        ) : (
          <div className="fullview__grid">
            {(rows ?? []).map((d) => {
              const label = d.short_name || d.title;
              const meta = metaFor(d, isDefault);
              const tag = d.template ? formatTemplate(d.template) : null;
              const clickable = !!d.cached_artifact_id;
              return (
                <button
                  key={d.id}
                  type="button"
                  className={`fullview__card${clickable ? '' : ' fullview__card--static'}`}
                  onClick={() => open(d)}
                  disabled={!clickable}
                  title={clickable ? `Preview ${d.title}` : d.title}
                >
                  <div className="fullview__card-head">
                    <span className="fullview__card-icon">
                      <LayoutDashboard size={16} strokeWidth={1.5} />
                    </span>
                    <span className="fullview__card-title">{label}</span>
                  </div>
                  {d.description && <span className="fullview__card-desc">{d.description}</span>}
                  <span className="fullview__card-meta">{meta}</span>
                  {tag && (
                    <div className="fullview__card-foot">
                      <span className="wrow__tag">{tag}</span>
                    </div>
                  )}
                </button>
              );
            })}
          </div>
        )}
      </section>

      <section>
        <h3 className="fullview__section-title">Marketplace</h3>
        <div className="fullview__stub">Shared dashboards aren't part of this demo yet.</div>
      </section>
    </div>
  );

  return (
    <Widget title="Dashboards" icon={LayoutDashboard} count={count} hint={hint} expandable renderFull={renderFull}>
      {visible.length > 0 && (
        <div className="wlist">
          {visible.map((d) => {
            const label = d.short_name || d.title;
            const meta = metaFor(d, isDefault);
            const tag = d.template ? formatTemplate(d.template) : null;
            if (!d.cached_artifact_id) {
              return (
                <div key={d.id} className="wrow wrow--static" title={d.title}>
                  <span className="wrow__icon">
                    <LayoutDashboard size={13} strokeWidth={1.5} />
                  </span>
                  <span className="wrow__main">
                    <span className="wrow__name">{label}</span>
                    {meta && <span className="wrow__meta">{meta}</span>}
                  </span>
                  {tag && <span className="wrow__tag">{tag}</span>}
                </div>
              );
            }
            return (
              <button
                key={d.id}
                type="button"
                className="wrow wrow--button"
                onClick={() => open(d)}
                title={`Preview ${d.title}`}
              >
                <span className="wrow__icon">
                  <LayoutDashboard size={13} strokeWidth={1.5} />
                </span>
                <span className="wrow__main">
                  <span className="wrow__name">{label}</span>
                  {meta && <span className="wrow__meta">{meta}</span>}
                </span>
                {tag && <span className="wrow__tag">{tag}</span>}
              </button>
            );
          })}
          {overflow > 0 && <div className="wlist__more">+{overflow} more</div>}
        </div>
      )}
    </Widget>
  );
}
