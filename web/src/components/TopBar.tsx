import { ArbiWordmark } from './brand/ArbiWordmark';

// Mono-chrome top bar: brand wordmark, breadcrumb to the active section, the
// (inert) tenant identity, and a sign-out control. View-only — the only action
// is sign out, which clears the in-memory session and performs no backend
// mutation.
export function TopBar({ section, onLogout }: { section: string; onLogout?: () => void }) {
  return (
    <header className="topbar">
      <div className="topbar__brand">
        <ArbiWordmark size={16} />
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
      {onLogout && (
        <button type="button" className="topbar__logout" onClick={onLogout}>
          Sign out
        </button>
      )}
    </header>
  );
}
