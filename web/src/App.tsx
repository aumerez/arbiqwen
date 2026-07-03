import { INTEGRATIONS, SKILLS, RAG_SOURCES } from './demo-data';
import { Section } from './components/Section';
import { IntegrationCard } from './components/IntegrationCard';
import { SkillCard } from './components/SkillCard';
import { RagSourceCard } from './components/RagSourceCard';
import './App.css';

// Read-only browser preview. It exposes exactly three surfaces — Integrations,
// Skills, and RAG sources — as view-only content backed by local demo data.
//
// There is no navigation to, or rendering of, any other surface, and no control
// that connects, runs, edits, or removes anything. In-page navigation uses
// hash anchors only. The app renders with no backend, session, token, or
// global bridge object.
const NAV = [
  { id: 'integrations', label: 'Integrations' },
  { id: 'skills', label: 'Skills' },
  { id: 'rag-sources', label: 'RAG sources' },
];

export default function App() {
  return (
    <div className="app">
      <header className="app__header">
        <div className="app__brand">
          <h1 className="app__title">Arbi</h1>
          <p className="app__subtitle">Read-only preview</p>
        </div>
        <nav className="app__nav" aria-label="Preview sections">
          {NAV.map((entry) => (
            <a key={entry.id} className="app__navlink" href={`#${entry.id}`}>
              {entry.label}
            </a>
          ))}
        </nav>
      </header>

      <main className="app__main">
        <Section
          id="integrations"
          title="Integrations"
          blurb="Data sources available to a workspace, shown as read-only entries."
          count={INTEGRATIONS.length}
          emptyLabel="No integrations to show."
        >
          {INTEGRATIONS.map((item) => (
            <IntegrationCard key={item.id} item={item} />
          ))}
        </Section>

        <Section
          id="skills"
          title="Skills"
          blurb="Reusable capabilities a workspace can offer, listed for reference."
          count={SKILLS.length}
          emptyLabel="No skills to show."
        >
          {SKILLS.map((item) => (
            <SkillCard key={item.id} item={item} />
          ))}
        </Section>

        <Section
          id="rag-sources"
          title="RAG sources"
          blurb="Knowledge collections that ground answers, listed with high-level stats."
          count={RAG_SOURCES.length}
          emptyLabel="No knowledge sources to show."
        >
          {RAG_SOURCES.map((item) => (
            <RagSourceCard key={item.id} item={item} />
          ))}
        </Section>
      </main>

      <footer className="app__footer">
        <p>This preview is view-only and does not modify any data.</p>
      </footer>
    </div>
  );
}
