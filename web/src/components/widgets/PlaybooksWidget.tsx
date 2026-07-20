import { useEffect, useState } from 'react';
import {
  Bell,
  BookOpen,
  CalendarClock,
  CheckCircle2,
  DollarSign,
  FileCheck,
  GitBranch,
  Rocket,
  ShieldAlert,
  X,
  Zap,
  type LucideIcon,
} from 'lucide-react';
import type { RawPlaybook, RawPlaybookStep, WorkspaceClient } from '../../api/http/workspaceClient';
import { Widget } from './Widget';

// Playbooks widget, ported from the desktop PlaybooksWidget. Playbooks are
// authored through chat (the assistant calls the playbook tools); this widget
// lists them and opens a read-only detail panel on click. The desktop has no
// Playbooks sidebar entry — it lives on the dashboard, same as here. No create /
// run / delete / edit (write surfaces, out of scope for the demo).

const ICONS: Record<string, LucideIcon> = {
  ShieldAlert,
  Rocket,
  DollarSign,
  CalendarClock,
  Zap,
  Bell,
  GitBranch,
  FileCheck,
  BookOpen,
};

const TRIGGER_LABELS: Record<string, string> = {
  manual: 'Manual',
  alert: 'On Alert',
  schedule: 'Scheduled',
  webhook: 'Webhook',
};

const STEP_COLORS: Record<string, string> = {
  action: 'var(--accent)',
  condition: '#e8a838',
  notification: '#7c6dd8',
  approval: '#d86d6d',
};

function triggerLabel(trigger?: string): string {
  return (trigger && TRIGGER_LABELS[trigger]) || 'Manual';
}

function timeAgo(dateStr?: string): string {
  if (!dateStr) return '';
  const diff = Date.now() - new Date(dateStr).getTime();
  if (Number.isNaN(diff)) return '';
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

function statusClass(status?: string): string {
  return status === 'active' ? 'badge--on' : 'badge--off';
}

function steps(pb: RawPlaybook): RawPlaybookStep[] {
  return Array.isArray(pb.steps) ? pb.steps : [];
}

function metaLine(pb: RawPlaybook): string {
  const n = steps(pb).length;
  return [`${n} step${n === 1 ? '' : 's'}`, triggerLabel(pb.trigger), pb.last_run?.started_at ? timeAgo(pb.last_run.started_at) : null]
    .filter(Boolean)
    .join(' · ');
}

const LIMIT = 5;

interface PlaybooksWidgetProps {
  workspaceClient: WorkspaceClient;
  projectId: number;
  isDefault: boolean;
}

export function PlaybooksWidget({ workspaceClient, projectId, isDefault }: PlaybooksWidgetProps) {
  const [playbooks, setPlaybooks] = useState<RawPlaybook[] | null>(null);
  const [selected, setSelected] = useState<RawPlaybook | null>(null);

  useEffect(() => {
    let cancelled = false;
    // My Space lists every playbook; a project lists its own.
    workspaceClient
      .listPlaybooks(isDefault ? undefined : projectId)
      .then((r) => {
        if (!cancelled) setPlaybooks(r);
      })
      .catch(() => {
        if (!cancelled) setPlaybooks([]);
      });
    return () => {
      cancelled = true;
    };
  }, [workspaceClient, projectId, isDefault]);

  const list = playbooks ?? [];
  const count = list.length;
  const hint = playbooks && count === 0 ? 'No playbooks yet' : undefined;
  const visible = list.slice(0, LIMIT);
  const overflow = count - visible.length;

  const card = (pb: RawPlaybook) => {
    const Icon = ICONS[pb.icon ?? ''] || Zap;
    return (
      <button
        key={pb.id}
        type="button"
        className="fullview__card"
        onClick={() => setSelected(pb)}
        title={`Open ${pb.name}`}
      >
        <div className="fullview__card-head">
          <span className="fullview__card-icon">
            <Icon size={16} strokeWidth={1.5} />
          </span>
          <span className="fullview__card-title">{pb.name}</span>
        </div>
        {pb.description && <span className="fullview__card-desc">{pb.description}</span>}
        <div className="fullview__card-foot">
          <span className="wrow__tag">{pb.status === 'active' ? 'active' : 'draft'}</span>
          <span className="fullview__card-meta">{metaLine(pb)}</span>
        </div>
      </button>
    );
  };

  const renderFull = () => (
    <div className="fullview">
      <section>
        <h3 className="fullview__section-title">
          Playbooks<span className="fullview__lead">{count}</span>
        </h3>
        {count === 0 ? (
          <div className="fullview__empty">No playbooks yet.</div>
        ) : (
          <div className="fullview__grid">{list.map(card)}</div>
        )}
      </section>
    </div>
  );

  return (
    <>
      <Widget title="Playbooks" icon={BookOpen} count={count} hint={hint} expandable renderFull={renderFull}>
        {visible.length > 0 && (
          <div className="wlist">
            {visible.map((pb) => {
              const Icon = ICONS[pb.icon ?? ''] || Zap;
              return (
                <button key={pb.id} type="button" className="wrow wrow--button" onClick={() => setSelected(pb)}>
                  <span className="wrow__icon">
                    <Icon size={13} strokeWidth={1.5} />
                  </span>
                  <span className="wrow__main">
                    <span className="wrow__name">{pb.name}</span>
                    <span className="wrow__meta">{metaLine(pb)}</span>
                  </span>
                  <span className={`badge ${statusClass(pb.status)}`}>{pb.status === 'active' ? 'Active' : 'Draft'}</span>
                </button>
              );
            })}
            {overflow > 0 && <div className="wlist__more">+{overflow} more</div>}
          </div>
        )}
      </Widget>
      {selected && <PlaybookDetail playbook={selected} onClose={() => setSelected(null)} />}
    </>
  );
}

function PlaybookDetail({ playbook, onClose }: { playbook: RawPlaybook; onClose: () => void }) {
  const Icon = ICONS[playbook.icon ?? ''] || Zap;
  const stepRows = steps(playbook);
  const tags = Array.isArray(playbook.tags) ? playbook.tags : [];
  const run = playbook.last_run;

  // Close on Escape.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-label={playbook.name}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal__header">
          <span className="modal__icon">
            <Icon size={20} strokeWidth={1.5} />
          </span>
          <div className="modal__heading">
            <h2 className="modal__title">{playbook.name}</h2>
            {playbook.description && <p className="modal__sub">{playbook.description}</p>}
          </div>
          <button type="button" className="modal__close" onClick={onClose} aria-label="Close">
            <X size={18} strokeWidth={1.75} />
          </button>
        </div>

        <div className="modal__body">
          <div className="pb-info">
            <span className={`badge ${statusClass(playbook.status)}`}>
              {playbook.status === 'active' ? 'Active' : 'Draft'}
            </span>
            <span className="pb-info__item">Trigger: {triggerLabel(playbook.trigger)}</span>
            {tags.length > 0 && <span className="pb-info__item">Tags: {tags.join(', ')}</span>}
          </div>

          <h3 className="pb-section-title">Steps ({stepRows.length})</h3>
          {stepRows.length === 0 ? (
            <p className="pb-empty">No steps defined.</p>
          ) : (
            <ol className="pb-steps">
              {stepRows.map((step, i) => (
                <li key={step.id ?? i} className="pb-step">
                  <span className="pb-step__num" style={{ background: STEP_COLORS[step.type ?? 'action'] }}>
                    {step.order ?? i + 1}
                  </span>
                  <div className="pb-step__body">
                    <span className="pb-step__name">{step.name || `Step ${i + 1}`}</span>
                    {step.description && <span className="pb-step__desc">{step.description}</span>}
                  </div>
                  {step.type && <span className="badge badge--read pb-step__type">{step.type}</span>}
                </li>
              ))}
            </ol>
          )}

          {run && (
            <div className="pb-lastrun">
              <CheckCircle2 size={15} strokeWidth={1.75} />
              <span>
                Last run: {run.status ?? 'unknown'}
                {run.steps_total != null && ` — ${run.steps_completed ?? 0}/${run.steps_total} steps`}
                {run.triggered_by && ` · ${run.triggered_by}`}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
