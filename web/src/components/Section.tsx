import type { ReactNode } from 'react';

interface SectionProps {
  id: string;
  title: string;
  blurb: string;
  count: number;
  emptyLabel: string;
  children: ReactNode;
}

// Read-only section shell: a labelled heading, a short blurb, and either a grid
// of cards or a safe empty state. It renders no action controls of any kind.
export function Section({ id, title, blurb, count, emptyLabel, children }: SectionProps) {
  return (
    <section className="section" id={id} aria-labelledby={`heading-${id}`} data-section={id}>
      <div className="section__head">
        <h2 id={`heading-${id}`} className="section__title">
          {title}
        </h2>
        <span className="section__count" aria-hidden="true">
          {count}
        </span>
      </div>
      <p className="section__blurb">{blurb}</p>
      {count === 0 ? (
        <p className="section__empty" role="status">
          {emptyLabel}
        </p>
      ) : (
        <ul className="card-grid">{children}</ul>
      )}
    </section>
  );
}
