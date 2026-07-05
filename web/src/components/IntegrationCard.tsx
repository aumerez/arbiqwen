import { Check, Plug } from 'lucide-react';
import type { IntegrationDemo } from '../viewModels';

// Read-only integration row, styled like the desktop IntegrationCard:
// Mono icon chip, name + description, and a non-secret status indicator.
// No connect/edit/execute controls.
export function IntegrationCard({ item }: { item: IntegrationDemo }) {
  const connected = item.status === 'Connected';
  return (
    <li className="card" data-card="integration">
      <span className="card__icon">
        <Plug size={18} strokeWidth={1.5} />
      </span>
      <div className="card__content">
        <p className="card__name">{item.name}</p>
        <p className="card__desc">{item.description}</p>
      </div>
      <div className="card__meta">
        {typeof item.toolCount === 'number' && <span className="card__metric">{item.toolCount} tools</span>}
        {item.lastActivity && <span className="card__metric">{item.lastActivity}</span>}
        {connected ? (
          <span className="connected-check" title="Connected" aria-label="Connected">
            <Check size={16} strokeWidth={2} />
          </span>
        ) : (
          <span className="badge badge--off">{item.status}</span>
        )}
      </div>
    </li>
  );
}
