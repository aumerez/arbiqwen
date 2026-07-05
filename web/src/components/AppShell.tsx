import type { ReactNode } from 'react';
import { TopBar } from './TopBar';
import { StatusBar } from './StatusBar';

interface AppShellProps {
  sidebar: ReactNode;
  sectionLabel: string;
  onLogout?: () => void;
  children: ReactNode;
}

// Desktop frame: full-width top bar, sidebar + scrolling content in the middle,
// status bar at the bottom. The sidebar is composed by the caller so it can carry
// project/conversation state.
export function AppShell({ sidebar, sectionLabel, onLogout, children }: AppShellProps) {
  return (
    <div className="shell">
      <TopBar section={sectionLabel} onLogout={onLogout} />
      <div className="shell__body">
        {sidebar}
        <main className="shell__content">{children}</main>
      </div>
      <StatusBar />
    </div>
  );
}
