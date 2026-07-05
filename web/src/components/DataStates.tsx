import { BrowserReadError } from '../api/http/httpClient';

// Loading / error presentation for the live read sections. Error text is
// generic and non-secret — it never echoes the backend body, status detail,
// token, or URL. A network failure additionally shows a configuration hint.

export function LoadingState() {
  return (
    <div className="state" role="status">
      <p className="state__msg">Loading workspace…</p>
    </div>
  );
}

export function ErrorState({ error, onRetry }: { error: BrowserReadError | null; onRetry: () => void }) {
  const network = error?.kind === 'network';
  return (
    <div className="state" role="alert">
      <p className="state__msg">
        {network ? 'Could not reach the backend.' : 'Something went wrong loading this workspace.'}
      </p>
      {network && <SetupHint />}
      <button type="button" className="state__retry" onClick={onRetry}>
        Retry
      </button>
    </div>
  );
}

function SetupHint() {
  return (
    <ul className="setup-hint">
      <li>Set VITE_API_BASE_URL to the backend origin when it runs on a separate host.</li>
      <li>Add this site&apos;s origin to the backend&apos;s CORS_ALLOWED_ORIGINS allowlist.</li>
      <li>Seed the browser-demo workspace on the backend.</li>
      <li>Set BROWSER_DEMO_PASSWORD on the server before signing in.</li>
    </ul>
  );
}
