import { useState, type MouseEvent, type ReactNode } from 'react';
import { TopBar } from './TopBar';
import { StatusBar } from './StatusBar';

interface AppShellProps {
  sidebar: ReactNode;
  sectionLabel: string;
  /** Breadcrumb segments for the top bar (workspace / chat …). */
  crumbs?: string[];
  email?: string;
  tenantName?: string;
  docCount?: number | null;
  onLogout?: () => void;
  children: ReactNode;
}

// Desktop frame: full-width top bar, sidebar + scrolling content in the middle,
// status bar at the bottom. The sidebar is composed by the caller so it can carry
// project/conversation state. On narrow (phone/tablet) viewports the sidebar
// collapses to an off-canvas drawer toggled from the top-bar hamburger.
export function AppShell({
  sidebar,
  sectionLabel,
  crumbs,
  email,
  tenantName,
  docCount,
  onLogout,
  children,
}: AppShellProps) {
  const [drawerOpen, setDrawerOpen] = useState(false);

  // Any interactive control inside the drawer (project, conversation, nav link)
  // triggers navigation and should dismiss the drawer. A capture-phase click
  // that originated on a button covers every case without threading a callback
  // through the Sidebar tree; plain scrolling of the conversation list doesn't
  // hit a button, so it leaves the drawer open.
  const dismissOnNavigate = (e: MouseEvent) => {
    if ((e.target as HTMLElement).closest('button')) setDrawerOpen(false);
  };

  return (
    <div className="shell">
      <TopBar
        section={sectionLabel}
        crumbs={crumbs}
        email={email}
        tenantName={tenantName}
        onLogout={onLogout}
        onToggleSidebar={() => setDrawerOpen((v) => !v)}
      />
      <div className="shell__body">
        {drawerOpen && <div className="shell__backdrop" onClick={() => setDrawerOpen(false)} aria-hidden="true" />}
        <div
          className={`shell__sidebar${drawerOpen ? ' shell__sidebar--open' : ''}`}
          onClickCapture={dismissOnNavigate}
        >
          {sidebar}
        </div>
        <main className="shell__content">{children}</main>
      </div>
      <StatusBar docCount={docCount} />
    </div>
  );
}
