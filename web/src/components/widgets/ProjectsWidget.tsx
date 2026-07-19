import { useMemo, useState } from 'react';
import { FolderOpen, Search, X } from 'lucide-react';
import { Widget } from './Widget';
import type { ProjectView } from '../../projects/useProjects';
import { projectIcon } from '../../projects/projectVisual';

// Projects widget, ported from the desktop ProjectsWidget: a compact list of the
// workspace's projects (My Space excluded — it's the home, not a card). Selecting
// a row activates that project. The maximize button opens a full-page overlay
// with a searchable card grid. Read-only: no create/delete (write surfaces).
export function ProjectsWidget({ projects, onSelect }: { projects: ProjectView[]; onSelect: (id: number) => void }) {
  const [query, setQuery] = useState('');
  const hint = projects.length === 0 ? 'No projects yet' : undefined;
  const visible = projects.slice(0, 5);
  const overflow = projects.length - visible.length;

  const normalized = query.trim().toLowerCase();
  const filtered = useMemo(() => {
    if (!normalized) return projects;
    return projects.filter((p) => `${p.name} ${p.description ?? ''}`.toLowerCase().includes(normalized));
  }, [projects, normalized]);

  const renderFull = () => (
    <div className="fullview">
      <div className="fullview__search">
        <Search size={14} strokeWidth={1.75} aria-hidden="true" />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search projects"
          aria-label="Search projects"
        />
        {query && (
          <button type="button" className="widget__expand" onClick={() => setQuery('')} aria-label="Clear search">
            <X size={14} strokeWidth={1.75} />
          </button>
        )}
      </div>

      <section>
        <h3 className="fullview__section-title">
          My projects
          <span className="fullview__lead">
            {normalized ? `${filtered.length} of ${projects.length} match` : `${projects.length} active`}
          </span>
        </h3>
        {projects.length === 0 ? (
          <div className="fullview__empty">No projects yet.</div>
        ) : filtered.length === 0 ? (
          <div className="fullview__empty">No projects match “{query}”.</div>
        ) : (
          <div className="fullview__grid">
            {filtered.map((p) => {
              const Icon = projectIcon(p);
              return (
                <button
                  key={p.id}
                  type="button"
                  className="fullview__card"
                  onClick={() => onSelect(p.id)}
                  title={`Open ${p.name}`}
                >
                  <div className="fullview__card-head">
                    <span className="fullview__card-icon">
                      <Icon size={16} strokeWidth={1.5} />
                    </span>
                    <span className="fullview__card-title">{p.name}</span>
                  </div>
                  {p.description && <span className="fullview__card-desc">{p.description}</span>}
                </button>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );

  return (
    <Widget title="Projects" icon={FolderOpen} count={projects.length} hint={hint} expandable renderFull={renderFull}>
      {visible.length > 0 && (
        <div className="wlist">
          {visible.map((p) => {
            const Icon = projectIcon(p);
            return (
              <button key={p.id} type="button" className="wrow wrow--button" onClick={() => onSelect(p.id)}>
                <span className="wrow__icon">
                  <Icon size={13} strokeWidth={1.5} />
                </span>
                <span className="wrow__main">
                  <span className="wrow__name">{p.name}</span>
                  {p.description && <span className="wrow__meta">{p.description}</span>}
                </span>
              </button>
            );
          })}
          {overflow > 0 && <div className="wlist__more">+{overflow} more</div>}
        </div>
      )}
    </Widget>
  );
}
