import { Database } from 'lucide-react';
import type { RagSourceDemo } from '../viewModels';

// Read-only knowledge-source row, styled like the desktop RAG source card.
// No create/validate/delete controls.
export function RagSourceCard({ item }: { item: RagSourceDemo }) {
  const ready = item.status === 'Ready';
  return (
    <li className="card" data-card="rag-source">
      <span className="card__icon">
        <Database size={18} strokeWidth={1.5} />
      </span>
      <div className="card__content">
        <p className="card__name">{item.name}</p>
        <p className="card__desc">{item.description}</p>
      </div>
      <div className="card__meta">
        <span className="card__metric">{item.type}</span>
        {typeof item.documentCount === 'number' && (
          <span className="card__metric">{item.documentCount} docs</span>
        )}
        <span className={`badge ${ready ? 'badge--on' : 'badge--off'}`}>{item.status}</span>
      </div>
    </li>
  );
}
