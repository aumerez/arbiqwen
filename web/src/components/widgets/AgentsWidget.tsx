import { useEffect, useMemo, useState } from 'react';
import { Bot } from 'lucide-react';
import type { WorkspaceClient, RawAgent } from '../../api/http/workspaceClient';
import { Widget } from './Widget';

// Ported from the desktop ActiveAgentsWidget (read-only subset). Agents are
// created and edited through chat (the assistant invokes create_agent_task);
// this widget lists them. The maximize button opens a full-page overlay split
// into Active runs and History, plus a Marketplace stub. No create / delete /
// edit-in-chat / templates (write + chat surfaces, out of scope for the demo).

const ACTIVE = new Set(['queued', 'working']);

function statusLabel(status?: string): string {
  return status && status.length > 0 ? status : 'draft';
}

function metaFor(a: RawAgent, showProject: boolean): string {
  const parts: string[] = [];
  if (showProject && a.project_id != null) parts.push(`Project ${a.project_id}`);
  parts.push(statusLabel(a.status));
  return parts.join(' · ');
}

const LIMIT = 5;

interface AgentsWidgetProps {
  workspaceClient: WorkspaceClient;
  projectId: number;
  isDefault: boolean;
}

export function AgentsWidget({ workspaceClient, projectId, isDefault }: AgentsWidgetProps) {
  const [agents, setAgents] = useState<RawAgent[] | null>(null);

  useEffect(() => {
    let cancelled = false;
    workspaceClient
      .listAgents()
      .then((r) => {
        if (!cancelled) setAgents(r);
      })
      .catch(() => {
        if (!cancelled) setAgents([]);
      });
    return () => {
      cancelled = true;
    };
  }, [workspaceClient]);

  // My Space shows every agent; a project shows only its own.
  const scoped = useMemo(
    () => (agents ?? []).filter((a) => isDefault || a.project_id === projectId),
    [agents, isDefault, projectId],
  );

  const count = scoped.length;
  const hint = agents && count === 0 ? 'No agents yet' : undefined;
  const visible = scoped.slice(0, LIMIT);
  const overflow = count - visible.length;

  const active = scoped.filter((a) => ACTIVE.has(a.status ?? ''));
  const history = scoped.filter((a) => !ACTIVE.has(a.status ?? ''));

  const card = (a: RawAgent) => (
    <div key={a.id} className="fullview__card fullview__card--static" title={a.title}>
      <div className="fullview__card-head">
        <span className="fullview__card-icon">
          <Bot size={16} strokeWidth={1.5} />
        </span>
        <span className="fullview__card-title">{a.title}</span>
      </div>
      <div className="fullview__card-foot">
        <span className="wrow__tag">{statusLabel(a.status)}</span>
        {isDefault && a.project_id != null && <span className="fullview__card-meta">Project {a.project_id}</span>}
      </div>
    </div>
  );

  const renderFull = () => (
    <div className="fullview">
      <section>
        <h3 className="fullview__section-title">
          Active runs<span className="fullview__lead">{active.length}</span>
        </h3>
        {active.length === 0 ? (
          <div className="fullview__empty">No active runs.</div>
        ) : (
          <div className="fullview__grid">{active.map(card)}</div>
        )}
      </section>

      <section>
        <h3 className="fullview__section-title">
          History<span className="fullview__lead">{history.length}</span>
        </h3>
        {history.length === 0 ? (
          <div className="fullview__empty">No past runs.</div>
        ) : (
          <div className="fullview__grid">{history.map(card)}</div>
        )}
      </section>

      <section>
        <h3 className="fullview__section-title">Marketplace</h3>
        <div className="fullview__stub">Shared agents aren't part of this demo yet.</div>
      </section>
    </div>
  );

  return (
    <Widget title="Active Agents" icon={Bot} count={count} hint={hint} expandable renderFull={renderFull}>
      {visible.length > 0 && (
        <div className="wlist">
          {visible.map((a) => (
            <div key={a.id} className="wrow wrow--static" title={a.title}>
              <span className="wrow__icon">
                <Bot size={13} strokeWidth={1.5} />
              </span>
              <span className="wrow__main">
                <span className="wrow__name">{a.title}</span>
                <span className="wrow__meta">{metaFor(a, isDefault)}</span>
              </span>
            </div>
          ))}
          {overflow > 0 && <div className="wlist__more">+{overflow} more</div>}
        </div>
      )}
    </Widget>
  );
}
