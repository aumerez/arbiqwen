import { useState } from 'react';
import { Database, Plug, Zap } from 'lucide-react';
import { AppShell } from './components/AppShell';
import type { NavItem } from './components/Sidebar';
import { Section } from './components/Section';
import { IntegrationCard } from './components/IntegrationCard';
import { SkillCard } from './components/SkillCard';
import { RagSourceCard } from './components/RagSourceCard';
import { INTEGRATIONS, RAG_SOURCES, SKILLS } from './demo-data';

// Read-only browser preview, styled to match the desktop app. The shell
// (top bar, Mono sidebar, status bar) frames exactly three sections —
// Integrations, Skills, RAG sources — backed by local demo data. Sidebar nav
// switches the active section client-side; nothing connects, runs, or mutates.
const NAV: NavItem[] = [
  { id: 'integrations', label: 'Integrations', icon: Plug },
  { id: 'skills', label: 'Skills', icon: Zap },
  { id: 'rag-sources', label: 'Knowledge Bases', icon: Database },
];

export default function App() {
  const [active, setActive] = useState('integrations');
  const section = NAV.find((n) => n.id === active) ?? NAV[0];

  return (
    <AppShell items={NAV} activeId={active} sectionLabel={section.label} onNavigate={setActive}>
      {active === 'integrations' && (
        <Section
          id="integrations"
          title="Integrations"
          description="Data sources available to this workspace, shown as read-only entries."
          count={INTEGRATIONS.length}
          emptyLabel="No integrations to show."
        >
          {INTEGRATIONS.map((item) => (
            <IntegrationCard key={item.id} item={item} />
          ))}
        </Section>
      )}

      {active === 'skills' && (
        <Section
          id="skills"
          title="Skills"
          description="Reusable capabilities available to this workspace, listed for reference."
          count={SKILLS.length}
          emptyLabel="No skills to show."
        >
          {SKILLS.map((item) => (
            <SkillCard key={item.id} item={item} />
          ))}
        </Section>
      )}

      {active === 'rag-sources' && (
        <Section
          id="rag-sources"
          title="RAG Sources"
          description="Knowledge collections that ground answers, listed with high-level stats."
          count={RAG_SOURCES.length}
          emptyLabel="No knowledge sources to show."
        >
          {RAG_SOURCES.map((item) => (
            <RagSourceCard key={item.id} item={item} />
          ))}
        </Section>
      )}
    </AppShell>
  );
}
