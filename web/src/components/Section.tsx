import type { ReactNode } from 'react';

interface SectionProps {
  id: string;
  title: string;
  description: string;
  count: number;
  emptyLabel: string;
  children: ReactNode;
}

// A read-only page section: header (title + blurb) and either a card list or a
// safe empty state. No action controls.
export function Section({ id, title, description, count, emptyLabel, children }: SectionProps) {
  return (
    <section data-section={id} aria-labelledby={`heading-${id}`}>
      <div className="page__header">
        <h1 id={`heading-${id}`} className="page__title">
          {title}
        </h1>
        <p className="page__desc">{description}</p>
      </div>
      {count === 0 ? (
        <p className="empty" role="status">
          {emptyLabel}
        </p>
      ) : (
        <ul className="card-list">{children}</ul>
      )}
    </section>
  );
}
