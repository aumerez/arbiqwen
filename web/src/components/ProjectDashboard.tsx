import { BarChart3, BookOpen, Bot, FolderOpen, LayoutDashboard, Sparkles, Users } from 'lucide-react';
import { Widget } from './widgets/Widget';
import { ProjectsWidget } from './widgets/ProjectsWidget';
import { DocumentsWidget, type DocLike } from './widgets/DocumentsWidget';
import { InfoSourcesWidget } from './widgets/InfoSourcesWidget';
import type { ProjectView } from '../projects/useProjects';
import type { ReadAdapter } from '../api/http/readAdapter';
import type { ProjectsClient } from '../api/http/projectsClient';

// Ported from the desktop ProjectDashboard. Renders the My Space layout for the
// default project and the project layout for the rest. The project layout adds
// the Information Sources widget, where integrations and knowledge bases can be
// enabled/disabled for that project. Data-less widgets render genuine empty
// states; only the source toggles write.
interface ProjectDashboardProps {
  project: ProjectView;
  subtitle: string;
  otherProjects: ProjectView[];
  onSelectProject: (id: number) => void;
  documents: DocLike[];
  adapter: ReadAdapter;
  projectsClient: ProjectsClient;
}

export function ProjectDashboard({
  project,
  subtitle,
  otherProjects,
  onSelectProject,
  documents,
  adapter,
  projectsClient,
}: ProjectDashboardProps) {
  const isDefault = project.isDefault;
  const HeaderIcon = isDefault ? Sparkles : FolderOpen;

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
            <div className="grid-one">
              <Widget title="Dashboards" icon={LayoutDashboard} count={0} hint="No dashboards yet" />
            </div>
            <div className="grid-one">
              <Widget title="Playbooks" icon={BookOpen} count={0} hint="No playbooks yet" />
            </div>
            <div className="grid-one">
              <Widget title="Active Agents" icon={Bot} count={0} hint="No agents yet" />
            </div>
            <div className="grid-full">
              <DocumentsWidget documents={documents} />
            </div>
          </>
        ) : (
          <>
            <div className="grid-one">
              <Widget title="Members" icon={Users} count={0} hint="No members" />
            </div>
            <div className="grid-one">
              <Widget title="Dashboards" icon={LayoutDashboard} count={0} hint="No dashboards yet" />
            </div>
            <div className="grid-one">
              <Widget title="Playbooks" icon={BookOpen} count={0} hint="No playbooks yet" />
            </div>
            <div className="grid-one">
              <Widget title="Active Agents" icon={Bot} count={0} hint="No agents yet" />
            </div>
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
