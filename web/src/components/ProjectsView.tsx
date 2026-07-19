import type { ProjectView } from '../projects/useProjects';
import { projectIcon } from '../projects/projectVisual';

// "My Space / Projects" view — a grid of the workspace's projects. Selecting one
// makes it the active project and returns to the conversation view. Read-only:
// no create/edit/delete.
interface ProjectsViewProps {
  projects: ProjectView[];
  currentId: number | null;
  onSelect: (id: number) => void;
}

export function ProjectsView({ projects, currentId, onSelect }: ProjectsViewProps) {
  return (
    <section data-section="projects" aria-labelledby="heading-projects">
      <div className="page__header">
        <h1 id="heading-projects" className="page__title">
          Projects
        </h1>
        <p className="page__desc">Workspaces you can explore. Select one to scope the assistant and its sources.</p>
      </div>

      {projects.length === 0 ? (
        <p className="empty">No projects to show.</p>
      ) : (
        <ul className="card-list">
          {projects.map((project) => {
            const Icon = projectIcon(project);
            const active = project.id === currentId;
            return (
              <li key={project.id} className="card card--project" data-card="project">
                <button
                  type="button"
                  className={`card__hit${active ? ' card__hit--active' : ''}`}
                  onClick={() => onSelect(project.id)}
                  aria-current={active ? 'true' : undefined}
                >
                  <span className="card__icon">
                    <Icon size={18} strokeWidth={1.5} />
                  </span>
                  <div className="card__content">
                    <p className="card__name">
                      {project.name}
                      {project.isDefault && <span className="badge badge--read">My Space</span>}
                    </p>
                    {project.description && <p className="card__desc">{project.description}</p>}
                  </div>
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
