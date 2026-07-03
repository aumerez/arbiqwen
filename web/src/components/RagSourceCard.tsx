import type { RagSourceDemo } from '../demo-data';

// Read-only card for a single knowledge source. Optional document tally is
// rendered defensively and omitted when absent. No action controls.
export function RagSourceCard({ item }: { item: RagSourceDemo }) {
  return (
    <li className="card" data-card="rag-source">
      <div className="card__top">
        <span className="card__name">{item.name}</span>
        <span className={`badge badge--${item.status.toLowerCase()}`}>{item.status}</span>
      </div>
      <p className="card__detail">{item.description}</p>
      <dl className="meta">
        <div className="meta__row">
          <dt>Type</dt>
          <dd>{item.type}</dd>
        </div>
        {typeof item.documentCount === 'number' && (
          <div className="meta__row">
            <dt>Documents</dt>
            <dd>{item.documentCount}</dd>
          </div>
        )}
      </dl>
    </li>
  );
}
