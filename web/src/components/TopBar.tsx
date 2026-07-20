import { useEffect, useRef, useState } from 'react';
import { LogOut, Menu } from 'lucide-react';
import { ArbiWordmark } from './brand/ArbiWordmark';

// Mono-chrome top bar, matching the desktop TopBar layout: spinning Arbi
// wordmark, a "/"-delimited breadcrumb (workspace / chat), the (inert) tenant
// identity, then a user area — avatar + email with a dropdown whose only action
// is sign out. View-only beyond that: sign out clears the in-memory session and
// performs no backend mutation. The desktop's notification bell is omitted (the
// demo surfaces no notifications). The hamburger (mobile only, hidden by CSS on
// desktop) toggles the off-canvas sidebar drawer.
export function TopBar({
  section,
  crumbs,
  email,
  tenantName = 'Arbi Browser Demo',
  onLogout,
  onToggleSidebar,
}: {
  section?: string;
  /** Breadcrumb segments (workspace / chat …). Falls back to [section]. */
  crumbs?: string[];
  email?: string;
  tenantName?: string;
  onLogout?: () => void;
  onToggleSidebar?: () => void;
}) {
  const segments = (crumbs && crumbs.length > 0 ? crumbs : section ? [section] : []).filter(Boolean);
  const [menuOpen, setMenuOpen] = useState(false);
  const userAreaRef = useRef<HTMLDivElement>(null);

  // Close the user menu on outside click, mirroring the desktop dropdown.
  useEffect(() => {
    if (!menuOpen) return;
    const handler = (e: MouseEvent) => {
      if (userAreaRef.current?.contains(e.target as Node)) return;
      setMenuOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [menuOpen]);

  return (
    <header className="topbar">
      {onToggleSidebar && (
        <button type="button" className="topbar__menu" onClick={onToggleSidebar} aria-label="Toggle navigation">
          <Menu size={16} strokeWidth={2} />
        </button>
      )}

      <div className="topbar__brand">
        <ArbiWordmark size={16} spinSeconds={8} />
      </div>

      <div className="topbar__crumb">
        {segments.map((seg, idx) => (
          <span key={`${idx}-${seg}`} className="topbar__crumb-seg">
            <span className="topbar__crumb-sep">/</span>
            <span className={idx === segments.length - 1 ? 'topbar__crumb-current' : undefined}>{seg}</span>
          </span>
        ))}
      </div>

      <div className="topbar__spacer" />

      <div className="topbar__tenant">
        <span className="topbar__tenant-logo">{initials(tenantName)}</span>
        <span className="topbar__tenant-name">{tenantName}</span>
      </div>

      {onLogout && (
        <>
          <span className="topbar__sep" aria-hidden="true" />
          <div className="topbar__user" ref={userAreaRef}>
            <button
              type="button"
              className="topbar__user-button"
              onClick={() => setMenuOpen((v) => !v)}
              aria-label="Account menu"
              aria-haspopup="menu"
              aria-expanded={menuOpen}
            >
              <span className="topbar__user-avatar">{initials(email)}</span>
              {email && <span className="topbar__user-email">{email}</span>}
            </button>
            {menuOpen && (
              <div className="topbar__user-menu">
                <button type="button" className="topbar__user-menu-item" onClick={onLogout}>
                  <LogOut size={14} strokeWidth={1.5} />
                  <span>Sign out</span>
                </button>
              </div>
            )}
          </div>
        </>
      )}
    </header>
  );
}

// Initials for the avatar/tenant glyph — email local-part or word initials, up
// to two characters. Mirrors the desktop getInitials helper.
function initials(text?: string): string {
  if (!text) return '?';
  if (text.includes('@')) {
    const parts = text.split('@')[0].split(/[._-]/).filter(Boolean);
    if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
    return text.slice(0, 2).toUpperCase();
  }
  const words = text.trim().split(/\s+/).filter(Boolean);
  if (words.length >= 2) return (words[0][0] + words[1][0]).toUpperCase();
  return text.slice(0, 2).toUpperCase();
}
