// Bottom status bar mirroring the desktop StatusBar chrome: a connection dot,
// a status label, the workspace document count, then (right-aligned) an
// environment pill and the build label. Static and view-only — the desktop's
// clickable model/docs shortcuts and the running-agents trigger are omitted
// (no settings navigation and no agent execution in the read-only demo).
export function StatusBar({ docCount }: { docCount?: number | null }) {
  return (
    <footer className="statusbar">
      <span className="statusbar__dot" aria-hidden="true" />
      <span>Connected</span>
      {docCount != null && (
        <>
          <span className="statusbar__sep">|</span>
          <span>{docCount.toLocaleString()} docs</span>
        </>
      )}
      <span className="statusbar__spacer" />
      <span className="statusbar__pill">Read-only preview</span>
      <span className="statusbar__sep">|</span>
      <span>Demo</span>
    </footer>
  );
}
