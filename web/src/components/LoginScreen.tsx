import { useState, type FormEvent } from 'react';
import { Hexagon } from 'lucide-react';
import { login } from '../api/http/authClient';
import { BrowserReadError } from '../api/http/httpClient';
import { getApiBaseUrl, getDemoEmail } from '../config';

// Sign-in screen for the browser demo. The password is always entered at
// runtime — never prefilled, stored, or placed in the URL. The email may be
// prefilled from the non-secret VITE_DEMO_EMAIL for convenience. On success the
// in-memory access token is handed up via onSuccess.

function messageFor(err: unknown): string {
  if (err instanceof BrowserReadError) {
    if (err.kind === 'http' && err.status === 401) return 'Invalid email or password.';
    if (err.kind === 'network') return 'Could not reach the backend. Check the configuration and try again.';
  }
  return 'Sign-in failed. Please try again.';
}

export function LoginScreen({ onSuccess }: { onSuccess: (token: string) => void }) {
  const [email, setEmail] = useState(getDemoEmail());
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const token = await login({ baseUrl: getApiBaseUrl(), email, password });
      onSuccess(token);
    } catch (err) {
      setError(messageFor(err));
      setBusy(false);
    }
  }

  return (
    <div className="auth">
      <form className="auth__card" onSubmit={handleSubmit} aria-label="Sign in">
        <div className="auth__brand">
          <span className="auth__mark">
            <Hexagon size={16} strokeWidth={2} />
          </span>
          Arbi
        </div>
        <p className="auth__subtitle">Read-only workspace preview</p>

        <label className="auth__field">
          <span className="auth__label">Email</span>
          <input
            className="auth__input"
            type="email"
            name="email"
            autoComplete="username"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
        </label>

        <label className="auth__field">
          <span className="auth__label">Password</span>
          <input
            className="auth__input"
            type="password"
            name="password"
            autoComplete="current-password"
            minLength={8}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
        </label>

        {error && (
          <p className="auth__error" role="alert">
            {error}
          </p>
        )}

        <button className="auth__button" type="submit" disabled={busy}>
          {busy ? 'Signing in…' : 'Sign in'}
        </button>
      </form>
    </div>
  );
}
