import { Hexagon } from 'lucide-react';

// Mono-chrome top bar: brand mark, breadcrumb to the active section, and the
// (inert) tenant identity. View-only — no menus or actions.
export function TopBar({ section }: { section: string }) {
  return (
    <header className="topbar">
      <div className="topbar__brand">
        <span className="topbar__mark">
          <Hexagon size={13} strokeWidth={2} />
        </span>
        Arbi
      </div>
      <span className="topbar__crumb-sep">/</span>
      <div className="topbar__crumb">
        <span className="topbar__crumb-current">{section}</span>
      </div>
      <div className="topbar__spacer" />
      <div className="topbar__tenant">
        <span className="topbar__tenant-logo">HB</span>
        <span className="topbar__tenant-name">Arbi Browser Demo</span>
      </div>
    </header>
  );
}
