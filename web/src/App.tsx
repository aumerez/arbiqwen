import { PREVIEW_SECTIONS } from './demo-data';
import './App.css';

// Read-only browser preview surface. It exposes exactly three sections —
// Integrations, Skills, and RAG sources — as static, view-only content.
//
// There is intentionally no navigation to or rendering of any other surface,
// and no control that connects, executes, edits, or deletes anything. The
// component renders without any global bridge object and without a backend.
export default function App() {
  return (
    <div className="app">
      <header className="app__header">
        <h1 className="app__title">Arbi</h1>
        <p className="app__subtitle">Read-only preview</p>
      </header>

      <main className="app__main">
        {PREVIEW_SECTIONS.map((section) => (
          <section
            key={section.id}
            className="section"
            aria-labelledby={`heading-${section.id}`}
            data-section={section.id}
          >
            <h2 id={`heading-${section.id}`} className="section__title">
              {section.title}
            </h2>
            <p className="section__blurb">{section.blurb}</p>
            <ul className="section__list">
              {section.items.map((item) => (
                <li key={item.name} className="card">
                  <span className="card__name">{item.name}</span>
                  <span className="card__detail">{item.detail}</span>
                </li>
              ))}
            </ul>
          </section>
        ))}
      </main>

      <footer className="app__footer">
        <p>This preview is view-only and does not modify any data.</p>
      </footer>
    </div>
  );
}
