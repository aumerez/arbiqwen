import { CircleCheck } from 'lucide-react';
import type { IntegrationDemo } from '../viewModels';
import { integrationIcon } from '../integrations/integrationIcons';

// Read-only integration row, ported from the desktop IntegrationCard: the
// driver-specific icon chip, the instance alias (with a version chip), a
// subtitle of driver name + workspace, and a non-secret status indicator
// (CircleCheck when connected, a "Disconnected" badge otherwise). No
// connect/manage/delete/execute controls — those stay out of the read-only demo.
export function IntegrationCard({ item }: { item: IntegrationDemo }) {
  const connected = item.status === 'Connected';
  const Icon = integrationIcon(item.iconName);

  // Subtitle composition mirrors the desktop card: driver name and/or the
  // workspace label, falling back to the plain description.
  const subtitleParts = [item.driverName, item.workspaceName].filter(Boolean);
  const subtitle = subtitleParts.length > 0 ? subtitleParts.join(' — ') : item.description;

  return (
    <li className="card" data-card="integration">
      <span className="card__icon">
        <Icon size={18} strokeWidth={1.5} />
      </span>
      <div className="card__content">
        <p className="card__name">
          {item.name}
          {item.version && <span className="card__version">v{item.version}</span>}
        </p>
        {subtitle && <p className="card__desc">{subtitle}</p>}
      </div>
      <div className="card__meta">
        {connected ? (
          <span className="connected-check" title="Connected" aria-label="Connected">
            <CircleCheck size={16} strokeWidth={2} />
          </span>
        ) : (
          <span className="badge badge--off">Disconnected</span>
        )}
      </div>
    </li>
  );
}
