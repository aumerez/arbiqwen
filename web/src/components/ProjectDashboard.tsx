import { useCallback } from 'react';
import { BarChart3, BookOpen, Bot, FolderOpen, LayoutDashboard, Sparkles, Users } from 'lucide-react';
import { Widget } from './widgets/Widget';
import { ProjectsWidget } from './widgets/ProjectsWidget';
import { DocumentsWidget, type DocLike } from './widgets/DocumentsWidget';
import { InfoSourcesWidget } from './widgets/InfoSourcesWidget';
import { ListWidget, type ListRow } from './widgets/ListWidget';
import type { ProjectView } from '../projects/useProjects';
import type { ReadAdapter } from '../api/http/readAdapter';
import type { ProjectsClient } from '../api/http/projectsClient';
import type { WorkspaceClient } from '../api/http/workspaceClient';

// Ported from the desktop ProjectDashboard. My Space layout for the default
// project; project layout (with Information Sources + integration/RAG toggles)
// for the rest. Playbooks, Dashboards, and Active Agents load real data scoped
// to the active project; KPIs stay an empty placeholder (no browser endpoint).
interface ProjectDashboardProps {
  project: ProjectView;
  subtitle: string;
  otherProjects: ProjectView[];
  onSelectProject: (id: number) => void;
  documents: DocLike[];
  adapter: ReadAdapter;
  projectsClient: ProjectsClient;
  workspaceClient: WorkspaceClient;
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
}: ProjectDashboardProps) {
  const isDefault = project.isDefault;
  const HeaderIcon = isDefault ? Sparkles : FolderOpen;
  const projectId = project.id;

  const loadPlaybooks = useCallback(
    (): Promise<ListRow[]> =>
      workspaceClient
        .listPlaybooks(projectId)
        .then((items) => items.map((p) => ({ id: String(p.id), label: p.name, status: p.status }))),
    [workspaceClient, projectId],
  );
  const loadDashboards = useCallback(
    (): Promise<ListRow[]> =>
      workspaceClient.listDashboards(projectId).then((items) => items.map((d) => ({ id: String(d.id), label: d.title }))),
    [workspaceClient, projectId],
  );
  const loadAgents = useCallback(
    (): Promise<ListRow[]> =>
      workspaceClient
        .listAgents()
        .then((items) =>
          items
            .filter((a) => a.project_id === projectId)
            .map((a) => ({ id: String(a.id), label: a.title, status: a.status })),
        ),
    [workspaceClient, projectId],
  );

  const playbooks = (
    <ListWidget title="Playbooks" icon={BookOpen} rowIcon={BookOpen} emptyHint="No playbooks yet" loader={loadPlaybooks} />
  );
  const dashboards = (
    <ListWidget
      title="Dashboards"
      icon={LayoutDashboard}
      rowIcon={LayoutDashboard}
      emptyHint="No dashboards yet"
      loader={loadDashboards}
    />
  );
  const agents = (
    <ListWidget title="Active Agents" icon={Bot} rowIcon={Bot} emptyHint="No agents yet" loader={loadAgents} />
  );

  return (
    <div className="dashboard">
      <div className="dashboard__cover" aria-hidden="true" />

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
