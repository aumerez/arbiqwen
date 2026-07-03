import { Zap } from 'lucide-react';
import type { SkillDemo } from '../demo-data';

// Read-only skill row, styled like the desktop SkillCard. No toggle/configure.
export function SkillCard({ item }: { item: SkillDemo }) {
  const active = item.status === 'Active';
  return (
    <li className="card" data-card="skill">
      <span className="card__icon">
        <Zap size={18} strokeWidth={1.5} />
      </span>
      <div className="card__content">
        <p className="card__name">{item.name}</p>
        <p className="card__desc">{item.description}</p>
      </div>
      <div className="card__meta">
        <span className="card__metric">{item.category}</span>
        <span className={`badge ${active ? 'badge--on' : 'badge--off'}`}>{item.status}</span>
      </div>
    </li>
  );
}
