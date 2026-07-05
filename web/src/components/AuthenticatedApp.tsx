import { useMemo, useState } from 'react';
import { Database, Plug, Zap } from 'lucide-react';
import { AppShell } from './AppShell';
import type { NavItem } from './Sidebar';
import { Section } from './Section';
import { IntegrationCard } from './IntegrationCard';
import { SkillCard } from './SkillCard';
import { RagSourceCard } from './RagSourceCard';
import { LoadingState, ErrorState } from './DataStates';
import { createReadAdapter } from '../api/http/readAdapter';
import { getApiBaseUrl } from '../config';
import { getToken } from '../session';
import { useSections } from '../useSections';

// The signed-in surface: desktop-style shell framing exactly three read-only
// sections backed by live adapter reads. The adapter is built from the
// configured backend origin and the in-memory token getter, so every request
// carries the current access token without persisting it. Only safe controls
// (section nav, sign out, retry) are present — nothing connects, runs, or
// mutates.
const NAV: NavItem[] = [
  { id: 'integrations', label: 'Integrations', icon: Plug },
  { id: 'skills', label: 'Skills', icon: Zap },
  { id: 'rag-sources', label: 'Knowledge Bases', icon: Database },
];

export function AuthenticatedApp({ onLogout }: { onLogout: () => void }) {
  const adapter = useMemo(() => createReadAdapter({ baseUrl: getApiBaseUrl(), getToken }), []);
  const [active, setActive] = useState('integrations');
  const section = NAV.find((nav) => nav.id === active) ?? NAV[0];
  const { state, data, error, reload } = useSections(adapter);

  return (
    <AppShell
      items={NAV}
      activeId={active}
      sectionLabel={section.label}
      onNavigate={setActive}
      onLogout={onLogout}
    >
      {state === 'loading' && <LoadingState />}
      {state === 'error' && <ErrorState error={error} onRetry={reload} />}
      {state === 'ready' && data && (
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
  );
}
