import type { SkillDemo } from '../demo-data';

// Read-only card for a single skill. No action controls.
export function SkillCard({ item }: { item: SkillDemo }) {
  return (
    <li className="card" data-card="skill">
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
      </dl>
    </li>
  );
}
