import { useCallback, useEffect, useState } from 'react';
import { BookOpen, Layers, Plug } from 'lucide-react';
import { Widget } from './Widget';
import type { ReadAdapter } from '../../api/http/readAdapter';
import type { ProjectsClient } from '../../api/http/projectsClient';
import { BrowserReadError } from '../../api/http/httpClient';

// Information Sources widget, ported from the desktop InfoSourcesWidget: a
// Knowledge Bases card and an Integrations card, each row toggled on/off for the
// active project. Toggling is a real backend write (enable/disable the source
// for this project). A failed toggle (e.g. 403) reverts and shows a safe note.
interface Row {
  id: number;
  name: string;
}

interface InfoSourcesWidgetProps {
  projectId: number;
  adapter: ReadAdapter;
  projectsClient: ProjectsClient;
}

function Toggle({
  checked,
  disabled,
  onChange,
  label,
}: {
  checked: boolean;
  disabled: boolean;
  onChange: (next: boolean) => void;
  label: string;
}) {
  return (
    <label className="toggle">
      <input
        type="checkbox"
        className="toggle__input"
        checked={checked}
        disabled={disabled}
        onChange={(event) => onChange(event.target.checked)}
        aria-label={label}
      />
      <span className="toggle__slider" />
    </label>
  );
}

export function InfoSourcesWidget({ projectId, adapter, projectsClient }: InfoSourcesWidgetProps) {
  const [integrations, setIntegrations] = useState<Row[]>([]);
  const [ragSources, setRagSources] = useState<Row[]>([]);
  const [enabledInts, setEnabledInts] = useState<number[]>([]);
  const [enabledRags, setEnabledRags] = useState<number[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);
  const [note, setNote] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    const [intView, rags, cfg, enabledRagIds] = await Promise.all([
      adapter.integrations.list().catch(() => ({ drivers: [], instances: [] })),
      adapter.ragSources.list().catch(() => []),
      projectsClient.listEnabledIntegrations(projectId).catch(() => ({ integration_ids: [], integration_keys: [] })),
      projectsClient.listEnabledRagSources(projectId).catch(() => []),
    ]);
    setIntegrations(
      intView.instances.map((i) => ({ id: Number(i.id), name: i.instanceAlias || i.name || i.key || 'Integration' })),
    );
    setRagSources(rags.map((r) => ({ id: Number(r.id), name: r.label || r.ragKey || 'Knowledge base' })));
    setEnabledInts(Array.isArray(cfg.integration_ids) ? cfg.integration_ids : []);
    setEnabledRags(Array.isArray(enabledRagIds) ? enabledRagIds : []);
    setLoading(false);
  }, [adapter, projectsClient, projectId]);

  useEffect(() => {
    void load();
  }, [load]);

  function failNote(err: unknown) {
    setNote(
      err instanceof BrowserReadError && err.status === 403
        ? "You don't have permission to change this."
        : "Couldn't update this source.",
    );
  }

  async function toggleIntegration(id: number, enable: boolean) {
    setNote(null);
    setBusy(`int-${id}`);
    const prev = enabledInts;
    setEnabledInts(enable ? [...prev, id] : prev.filter((x) => x !== id));
    try {
      if (enable) await projectsClient.enableIntegration(projectId, id);
      else await projectsClient.disableIntegration(projectId, id);
    } catch (err) {
      setEnabledInts(prev);
      failNote(err);
    } finally {
      setBusy(null);
    }
  }

  async function toggleRag(id: number, enable: boolean) {
    setNote(null);
    setBusy(`rag-${id}`);
    const prev = enabledRags;
    setEnabledRags(enable ? [...prev, id] : prev.filter((x) => x !== id));
    try {
      if (enable) await projectsClient.enableRagSource(projectId, id);
      else await projectsClient.disableRagSource(projectId, id);
    } catch (err) {
      setEnabledRags(prev);
      failNote(err);
    } finally {
      setBusy(null);
    }
  }

  const total = integrations.length + ragSources.length;

  return (
    <Widget title="Information Sources" icon={Layers} count={total}>
      {loading ? (
        <p className="wempty">Loading sources…</p>
      ) : (
        <div className="infogrid">
          <div className="infocard">
            <div className="infocard__title">Knowledge Bases</div>
            {ragSources.length === 0 ? (
              <div className="infocard__empty">No knowledge bases</div>
            ) : (
              ragSources.map((s) => (
                <div key={s.id} className="infocard__row">
                  <BookOpen size={14} className="infocard__icon" />
                  <span className="infocard__name">{s.name}</span>
                  <Toggle
                    checked={enabledRags.includes(s.id)}
                    disabled={busy === `rag-${s.id}`}
                    onChange={(next) => toggleRag(s.id, next)}
                    label={`Enable ${s.name}`}
                  />
                </div>
              ))
            )}
          </div>

          <div className="infocard">
            <div className="infocard__title">Integrations</div>
            {integrations.length === 0 ? (
              <div className="infocard__empty">No integrations</div>
            ) : (
              integrations.map((i) => (
                <div key={i.id} className="infocard__row">
                  <Plug size={14} className="infocard__icon" />
                  <span className="infocard__name">{i.name}</span>
                  <Toggle
                    checked={enabledInts.includes(i.id)}
                    disabled={busy === `int-${i.id}`}
                    onChange={(next) => toggleIntegration(i.id, next)}
                    label={`Enable ${i.name}`}
                  />
                </div>
              ))
            )}
          </div>
        </div>
      )}
      {note && (
        <p className="infonote" role="status">
          {note}
        </p>
      )}
    </Widget>
  );
}
