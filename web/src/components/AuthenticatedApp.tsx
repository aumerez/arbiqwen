import { useEffect, useMemo, useState } from 'react';
import { Database, FolderKanban, Plug, Zap } from 'lucide-react';
import { AppShell } from './AppShell';
import { Sidebar, type NavItem } from './Sidebar';
import { Section } from './Section';
import { IntegrationCard } from './IntegrationCard';
import { SkillCard } from './SkillCard';
import { RagSourceCard } from './RagSourceCard';
import { LoadingState, ErrorState } from './DataStates';
import { ChatView } from './chat/ChatView';
import { ProjectsView } from './ProjectsView';
import { ProjectDashboard } from './ProjectDashboard';
import { ArtifactPanel, ArtifactPanelProvider } from './chat/ArtifactPanel';
import { createArtifactsClient } from '../api/http/artifactsClient';
import { createReadAdapter } from '../api/http/readAdapter';
import { createChatClient } from '../api/http/chatClient';
import { createProjectsClient } from '../api/http/projectsClient';
import { createWorkspaceClient } from '../api/http/workspaceClient';
import { getApiBaseUrl } from '../config';
import { getToken } from '../session';
import { useSections } from '../useSections';
import { useProjects } from '../projects/useProjects';
import { useConversations } from '../chat/useConversations';

// Signed-in surface: a desktop-style shell with a project-aware sidebar. The
// Assistant (chat) is the primary view, scoped to the active project; Projects,
// Integrations, Skills, and Knowledge Bases are reachable from the bottom nav.
// Read-only beyond chat: nothing else connects, runs, or mutates.
const NAV: NavItem[] = [
  { id: 'projects', label: 'Projects', icon: FolderKanban },
  { id: 'integrations', label: 'Integrations', icon: Plug },
  { id: 'skills', label: 'Skills', icon: Zap },
  { id: 'rag-sources', label: 'Knowledge Bases', icon: Database },
];

const SECTION_LABELS: Record<string, string> = {
  integrations: 'Integrations',
  skills: 'Skills',
  'rag-sources': 'RAG Sources',
  projects: 'Projects',
};

export function AuthenticatedApp({ onLogout }: { onLogout: () => void }) {
  const baseUrl = getApiBaseUrl();
  const adapter = useMemo(() => createReadAdapter({ baseUrl, getToken }), [baseUrl]);
  const chatClient = useMemo(() => createChatClient({ baseUrl, getToken }), [baseUrl]);
  const projectsClient = useMemo(() => createProjectsClient({ baseUrl, getToken }), [baseUrl]);
  const workspaceClient = useMemo(() => createWorkspaceClient({ baseUrl, getToken }), [baseUrl]);
  const artifactsClient = useMemo(() => createArtifactsClient({ baseUrl, getToken }), [baseUrl]);

  const projects = useProjects(projectsClient);
  const convo = useConversations(chatClient, projects.currentProject?.id ?? null);
  const { state, data, error, reload } = useSections(adapter);

  const [active, setActive] = useState('home');

  // Documents feed the My Space Documents widget (read-only).
  const [documents, setDocuments] = useState<{ id?: number | string; filename?: string }[]>([]);
  useEffect(() => {
    let cancelled = false;
    void adapter.documents
      .list()
      .then((docs) => {
        if (!cancelled) setDocuments(docs as { id?: number | string; filename?: string }[]);
      })
      .catch(() => {
        if (!cancelled) setDocuments([]);
      });
    return () => {
      cancelled = true;
    };
  }, [adapter]);

  // My Space is the home, not a listed project — the grid shows the rest.
  const otherProjects = projects.projects.filter((p) => !p.isDefault);

  const sectionLabel =
    active === 'home'
      ? (projects.currentProject?.name ?? 'My Space')
      : active === 'chat'
        ? (projects.currentProject?.name ?? 'Assistant')
        : SECTION_LABELS[active] ?? '';

  const sidebar = (
    <Sidebar
      workspaceName="Arbi Browser Demo"
      projects={projects.projects}
      currentProject={projects.currentProject}
      onGoToMySpace={() => {
        projects.goToMySpace();
        setActive('home');
      }}
      onOpenProject={() => setActive('home')}
      chats={convo.chats}
      currentChatId={convo.currentChatId}
      onSelectChat={(id) => {
        convo.selectChat(id);
        setActive('chat');
      }}
      onNewChat={() => {
        convo.newChat();
        setActive('chat');
      }}
      items={NAV}
      activeId={active}
      onNavigate={setActive}
    />
  );

  return (
    <ArtifactPanelProvider client={artifactsClient}>
      <AppShell sidebar={sidebar} sectionLabel={sectionLabel} onLogout={onLogout}>
      {active === 'home' && projects.currentProject && (
        <ProjectDashboard
          project={projects.currentProject}
          subtitle="Arbi Browser Demo workspace"
          otherProjects={otherProjects}
          onSelectProject={(id) => {
            projects.selectProject(id);
            setActive('home');
          }}
          documents={documents}
          adapter={adapter}
          projectsClient={projectsClient}
          workspaceClient={workspaceClient}
        />
      )}

      {active === 'chat' && (
        <ChatView
          messages={convo.messages}
          sending={convo.sending}
          error={convo.error}
          onSend={convo.send}
          onStop={convo.stop}
        />
      )}

      {active === 'projects' && (
        <ProjectsView
          projects={otherProjects}
          currentId={projects.currentProject?.id ?? null}
          onSelect={(id) => {
            projects.selectProject(id);
            setActive('home');
          }}
        />
      )}

      {active !== 'home' && active !== 'chat' && active !== 'projects' && state === 'loading' && <LoadingState />}
      {active !== 'home' && active !== 'chat' && active !== 'projects' && state === 'error' && (
        <ErrorState error={error} onRetry={reload} />
      )}
      {active !== 'home' && active !== 'chat' && active !== 'projects' && state === 'ready' && data && (
        <>
          {active === 'integrations' && (
            <Section
              id="integrations"
              title="Integrations"
              description="Data sources available to this workspace, shown as read-only entries."
              count={data.integrations.length}
              emptyLabel="No integrations to show."
            >
              {data.integrations.map((item) => (
                <IntegrationCard key={item.id} item={item} />
              ))}
            </Section>
          )}

          {active === 'skills' && (
            <Section
              id="skills"
              title="Skills"
              description="Reusable capabilities available to this workspace, listed for reference."
              count={data.skills.length}
              emptyLabel="No skills to show."
            >
              {data.skills.map((item) => (
                <SkillCard key={item.id} item={item} />
              ))}
            </Section>
          )}

          {active === 'rag-sources' && (
            <Section
              id="rag-sources"
              title="RAG Sources"
              description="Knowledge collections that ground answers, listed with high-level stats."
              count={data.ragSources.length}
              emptyLabel="No knowledge sources to show."
            >
              {data.ragSources.map((item) => (
                <RagSourceCard key={item.id} item={item} />
              ))}
            </Section>
          )}
        </>
      )}
      </AppShell>
      <ArtifactPanel />
    </ArtifactPanelProvider>
  );
}
