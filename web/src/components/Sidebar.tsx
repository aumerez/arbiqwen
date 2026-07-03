import type { LucideIcon } from 'lucide-react';
import { Building } from 'lucide-react';

export interface NavItem {
  id: string;
  label: string;
  icon: LucideIcon;
}

interface SidebarProps {
  items: NavItem[];
  activeId: string;
  onNavigate: (id: string) => void;
}

// Mono-chrome sidebar. Exposes exactly the in-scope sections; nav items switch
// the active view (client-side only). No Agents/Chat/Settings entries.
export function Sidebar({ items, activeId, onNavigate }: SidebarProps) {
  return (
    <nav className="sidebar" aria-label="Sections">
      <div className="sidebar__project">
        <Building size={20} strokeWidth={1.5} className="sidebar__project-icon" />
        <span className="sidebar__project-name">Browser Demo</span>
      </div>
      <div className="sidebar__sep" />
      <div className="sidebar__label">Workspace</div>
      <div className="sidebar__nav">
        {items.map((item) => {
          const Icon = item.icon;
          const active = item.id === activeId;
          return (
            <button
              key={item.id}
              type="button"
              className={`sidebar__link${active ? ' sidebar__link--active' : ''}`}
              aria-current={active ? 'page' : undefined}
              onClick={() => onNavigate(item.id)}
            >
              <Icon size={16} strokeWidth={1.5} className="sidebar__link-icon" />
              {item.label}
            </button>
          );
        })}
      </div>
      <div className="sidebar__spacer" />
      <div className="sidebar__foot">Read-only preview</div>
    </nav>
  );
}
