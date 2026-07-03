import type { ReactNode } from 'react';
import { Sidebar, type NavItem } from './Sidebar';
import { TopBar } from './TopBar';
import { StatusBar } from './StatusBar';

interface AppShellProps {
  items: NavItem[];
  activeId: string;
  sectionLabel: string;
  onNavigate: (id: string) => void;
  children: ReactNode;
}

// Recreates the desktop frame: full-width top bar, Mono sidebar + scrolling
// content in the middle, status bar at the bottom.
export function AppShell({ items, activeId, sectionLabel, onNavigate, children }: AppShellProps) {
  return (
    <div className="shell">
      <TopBar section={sectionLabel} />
      <div className="shell__body">
        <Sidebar items={items} activeId={activeId} onNavigate={onNavigate} />
        <main className="shell__content">{children}</main>
      </div>
      <StatusBar />
    </div>
  );
}
