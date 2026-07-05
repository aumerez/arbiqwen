import { Database, FolderKanban, MessageSquarePlus, Plug, Zap } from 'lucide-react';

// "My Space" home — the default landing after sign-in, mirroring the desktop
// project dashboard: a hero header plus a grid of summary tiles for the things
// this demo surfaces (Projects, Integrations, Skills, Knowledge Bases) and a
// primary action to start a conversation. The chat composer lives in the chat
// view, not here.
interface MySpaceViewProps {
  title: string;
  subtitle: string;
  counts: {
    projects: number;
    integrations: number | null;
    skills: number | null;
    rag: number | null;
  };
  onStartConversation: () => void;
  onNavigate: (id: string) => void;
}

function fmt(n: number | null): string {
  return n === null ? '—' : String(n);
}

export function MySpaceView({ title, subtitle, counts, onStartConversation, onNavigate }: MySpaceViewProps) {
  const tiles = [
    { id: 'projects', label: 'Projects', icon: FolderKanban, count: counts.projects },
    { id: 'integrations', label: 'Integrations', icon: Plug, count: counts.integrations },
    { id: 'skills', label: 'Skills', icon: Zap, count: counts.skills },
    { id: 'rag-sources', label: 'Knowledge Bases', icon: Database, count: counts.rag },
  ];

  return (
    <section className="home" aria-labelledby="heading-home">
      <div className="home__hero">
        <h1 id="heading-home" className="home__title">
          {title}
        </h1>
        <p className="home__subtitle">{subtitle}</p>
      </div>

      <button type="button" className="home__cta" onClick={onStartConversation}>
        <MessageSquarePlus size={18} strokeWidth={1.75} />
        Start a conversation
      </button>

      <ul className="home__grid">
        {tiles.map((tile) => {
          const Icon = tile.icon;
          return (
            <li key={tile.id} className="stat-card">
              <button type="button" className="stat-card__hit" onClick={() => onNavigate(tile.id)}>
                <span className="stat-card__icon">
                  <Icon size={18} strokeWidth={1.5} />
                </span>
                <span className="stat-card__count">{fmt(tile.count)}</span>
                <span className="stat-card__label">{tile.label}</span>
              </button>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
