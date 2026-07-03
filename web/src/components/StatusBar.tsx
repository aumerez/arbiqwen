// Bottom status bar mirroring the desktop chrome. Static, view-only.
export function StatusBar() {
  return (
    <footer className="statusbar">
      <span className="statusbar__dot" aria-hidden="true" />
      <span>Connected</span>
      <span className="statusbar__sep">|</span>
      <span>Read-only preview</span>
      <span className="statusbar__spacer" />
      <span>Demo</span>
    </footer>
  );
}
