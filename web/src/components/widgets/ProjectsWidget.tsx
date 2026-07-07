import { FolderOpen } from 'lucide-react';
import { Widget } from './Widget';
import type { ProjectView } from '../../projects/useProjects';

// Projects widget, ported from the desktop ProjectsWidget: a compact list of the
// workspace's projects (My Space excluded — it's the home, not a card). Selecting
// a row activates that project. Read-only: no create/delete here.
export function ProjectsWidget({ projects, onSelect }: { projects: ProjectView[]; onSelect: (id: number) => void }) {
  const hint = projects.length === 0 ? 'No projects yet' : undefined;
  const visible = projects.slice(0, 5);
  const overflow = projects.length - visible.length;
  return (
    <Widget title="Projects" icon={FolderOpen} count={projects.length} hint={hint}>
      {visible.length > 0 && (
        <div className="wlist">
          {visible.map((p) => (
            <button key={p.id} type="button" className="wrow" onClick={() => onSelect(p.id)}>
              <span className="wrow__icon">
                <FolderOpen size={13} strokeWidth={1.5} />
              </span>
              <span className="wrow__main">
                <span className="wrow__name">{p.name}</span>
                {p.description && <span className="wrow__meta">{p.description}</span>}
              </span>
            </button>
          ))}
          {overflow > 0 && <div className="wlist__more">+{overflow} more</div>}
        </div>
      )}
    </Widget>
  );
}
