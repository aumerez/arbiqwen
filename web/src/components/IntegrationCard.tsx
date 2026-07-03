import type { IntegrationDemo } from '../demo-data';

// Read-only card for a single integration. Optional fields are rendered
// defensively and omitted entirely when absent. No action controls.
export function IntegrationCard({ item }: { item: IntegrationDemo }) {
  return (
    <li className="card" data-card="integration">
      <div className="card__top">
        <span className="card__name">{item.name}</span>
        <span className={`badge badge--${item.status.toLowerCase()}`}>{item.status}</span>
      </div>
      <p className="card__detail">{item.description}</p>
      <dl className="meta">
        <div className="meta__row">
          <dt>Category</dt>
          <dd>{item.category}</dd>
        </div>
        {typeof item.toolCount === 'number' && (
          <div className="meta__row">
            <dt>Tools</dt>
            <dd>{item.toolCount}</dd>
          </div>
        )}
        {item.lastActivity && (
          <div className="meta__row">
            <dt>Last activity</dt>
            <dd>{item.lastActivity}</dd>
          </div>
        )}
      </dl>
    </li>
  );
}
