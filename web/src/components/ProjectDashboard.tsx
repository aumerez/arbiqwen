import { useCallback } from 'react';
import { BarChart3, BookOpen, Users } from 'lucide-react';
import { Widget } from './widgets/Widget';
import { ProjectsWidget } from './widgets/ProjectsWidget';
import { DocumentsWidget, type DocLike } from './widgets/DocumentsWidget';
import { InfoSourcesWidget } from './widgets/InfoSourcesWidget';
import { DashboardsWidget } from './widgets/DashboardsWidget';
import { AgentsWidget } from './widgets/AgentsWidget';
import { ListWidget, type ListRow } from './widgets/ListWidget';
import type { ProjectView } from '../projects/useProjects';
import { projectIcon, projectGradient } from '../projects/projectVisual';
import type { ReadAdapter } from '../api/http/readAdapter';
import type { ProjectsClient } from '../api/http/projectsClient';
import type { WorkspaceClient } from '../api/http/workspaceClient';

// Ported from the desktop ProjectDashboard. My Space layout for the default
// project; project layout (with Information Sources + integration/RAG toggles)
// for the rest. Playbooks, Dashboards, and Active Agents load real data scoped
// to the active project; KPIs stay an empty placeholder (no browser endpoint).
// The header icon badge + non-default banner tint come from projectVisual.
interface ProjectDashboardProps {
  project: ProjectView;
  subtitle: string;
  otherProjects: ProjectView[];
  onSelectProject: (id: number) => void;
  documents: DocLike[];
  adapter: ReadAdapter;
  projectsClient: ProjectsClient;
  workspaceClient: WorkspaceClient;
  onUseTemplate?: (prompt: string) => void;
}

export function ProjectDashboard({
  project,
  subtitle,
  otherProjects,
  onSelectProject,
  documents,
  adapter,
  projectsClient,
  workspaceClient,
  onUseTemplate,
}: ProjectDashboardProps) {
  const isDefault = project.isDefault;
  const HeaderIcon = projectIcon(project);
  const projectId = project.id;

  const loadPlaybooks = useCallback(
    (): Promise<ListRow[]> =>
      workspaceClient
        .listPlaybooks(projectId)
        .then((items) => items.map((p) => ({ id: String(p.id), label: p.name, status: p.status }))),
    [workspaceClient, projectId],
  );
  const playbooks = (
    <ListWidget title="Playbooks" icon={BookOpen} rowIcon={BookOpen} emptyHint="No playbooks yet" loader={loadPlaybooks} />
  );
  const dashboards = (
    <DashboardsWidget workspaceClient={workspaceClient} projectId={projectId} isDefault={isDefault} />
  );
  const agents = (
    <AgentsWidget
      workspaceClient={workspaceClient}
      projectId={projectId}
      isDefault={isDefault}
      onUseTemplate={onUseTemplate}
    />
  );

  return (
    <div className="dashboard">
      <div
        className="dashboard__cover"
        aria-hidden="true"
        style={isDefault ? undefined : { background: projectGradient(project.name) }}
      />

      <div className="dashboard__header">
        <span className="dashboard__avatar">
          <HeaderIcon size={24} strokeWidth={1.5} />
        </span>
        <div>
          <h1 className="dashboard__name">{project.name}</h1>
          <p className="dashboard__sub">{isDefault ? subtitle : project.description || subtitle}</p>
        </div>
      </div>

      <div className="dashboard__grid">
        {isDefault ? (
          <>
            <div className="grid-full">
              <Widget title="KPIs" icon={BarChart3} count={0} hint="No KPIs yet" />
            </div>
            <div className="grid-one">
              <ProjectsWidget projects={otherProjects} onSelect={onSelectProject} />
            </div>
            <div className="grid-one">{dashboards}</div>
            <div className="grid-one">{playbooks}</div>
            <div className="grid-one">{agents}</div>
            <div className="grid-full">
              <DocumentsWidget documents={documents} />
            </div>
          </>
        ) : (
          <>
            <div className="grid-one">
              <Widget title="Members" icon={Users} count={0} hint="No members" />
            </div>
            <div className="grid-one">{dashboards}</div>
            <div className="grid-one">{playbooks}</div>
            <div className="grid-one">{agents}</div>
            <div className="grid-full">
              <DocumentsWidget documents={documents} />
            </div>
            <div className="grid-full">
              <InfoSourcesWidget projectId={project.id} adapter={adapter} projectsClient={projectsClient} />
            </div>
          </>
        )}
      </div>
    </div>
  );
}
