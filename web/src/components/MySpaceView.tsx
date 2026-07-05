import { BarChart3, BookOpen, Bot, LayoutDashboard, Sparkles } from 'lucide-react';
import { Widget } from './widgets/Widget';
import { ProjectsWidget } from './widgets/ProjectsWidget';
import { DocumentsWidget, type DocLike } from './widgets/DocumentsWidget';
import type { ProjectView } from '../projects/useProjects';

// My Space home, ported from the desktop ProjectDashboard (default-project
// layout): a cover + header (avatar, project name, subtitle) over a 2-column
// widget grid — KPIs (full), Projects + Dashboards, Playbooks + Active Agents,
// Documents (full). Projects and Documents show live data; the others render
// their genuine empty states (their data isn't exposed to the browser demo).
// Read-only: no write controls, no Settings modal, no Quick Actions.
interface MySpaceViewProps {
  projectName: string;
  subtitle: string;
  projects: ProjectView[];
  onSelectProject: (id: number) => void;
  documents: DocLike[];
}

export function MySpaceView({ projectName, subtitle, projects, onSelectProject, documents }: MySpaceViewProps) {
  return (
    <div className="dashboard">
      <div className="dashboard__cover" aria-hidden="true" />

      <div className="dashboard__header">
        <span className="dashboard__avatar">
          <Sparkles size={24} strokeWidth={1.5} />
        </span>
        <div>
          <h1 className="dashboard__name">{projectName}</h1>
          <p className="dashboard__sub">{subtitle}</p>
        </div>
      </div>

      <div className="dashboard__grid">
        <div className="grid-full">
          <Widget title="KPIs" icon={BarChart3} count={0} hint="No KPIs yet" />
        </div>
        <div className="grid-one">
          <ProjectsWidget projects={projects} onSelect={onSelectProject} />
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
      </div>
    </div>
  );
}
