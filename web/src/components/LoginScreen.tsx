import { useState, type FormEvent } from 'react';
import { ArbiWordmark } from './brand/ArbiWordmark';
import { login } from '../api/http/authClient';
import { BrowserReadError } from '../api/http/httpClient';
import { getApiBaseUrl, getDemoEmail } from '../config';

// Sign-in screen, styled to match the desktop LoginScreen: centered card with the
// Arbi wordmark + subtitle, a Google provider button, an "or" divider, and
// the email/password form. The password is always entered at runtime and the
// access token is held in memory only. Google sign-in (live OAuth) isn't part of
// the browser demo, so its button explains that and the email/password path is
// the supported one.
const GOOGLE_NOTE = 'Google sign-in isn’t available in the browser demo — use email and password.';

function messageFor(err: unknown): string {
  if (err instanceof BrowserReadError) {
    if (err.kind === 'http' && err.status === 401) return 'Invalid email or password.';
    if (err.kind === 'network') return 'Could not reach the backend. Check the configuration and try again.';
  }
  return 'Sign-in failed. Please try again.';
}

function GoogleIcon() {
  return (
    <svg className="login__provider-icon" viewBox="0 0 48 48" aria-hidden="true">
      <path
        fill="#EA4335"
        d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"
      />
      <path
        fill="#4285F4"
        d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"
      />
      <path
        fill="#FBBC05"
        d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"
      />
      <path
        fill="#34A853"
        d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"
      />
    </svg>
  );
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
    <div className="login">
      <div className="login__card">
        <div className="login__header">
          <ArbiWordmark size={40} className="login__logo" />
          <p className="login__subtitle">AI Work Station</p>
        </div>

        {error && (
          <p className="login__error" role="alert">
            {error}
          </p>
        )}

        <div className="login__providers">
          <button
            type="button"
            className="login__provider"
            aria-label="Continue with Google"
            disabled={busy}
            onClick={() => setError(GOOGLE_NOTE)}
          >
            <GoogleIcon />
            <span>Continue with Google</span>
          </button>
        </div>

        <div className="login__divider" aria-hidden="true">
          <span>or</span>
        </div>

        <form className="login__form" onSubmit={handleSubmit} aria-label="Sign in" noValidate>
          <div className="login__field">
            <label htmlFor="login-email" className="login__label">
              Email
            </label>
            <input
              id="login-email"
              className="login__input"
              type="email"
              name="email"
              autoComplete="username"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="you@company.com"
              required
            />
          </div>

          <div className="login__field">
            <label htmlFor="login-password" className="login__label">
              Password
            </label>
            <input
              id="login-password"
              className="login__input"
              type="password"
              name="password"
              autoComplete="current-password"
              minLength={8}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Enter your password"
              required
            />
          </div>

          <button className="login__submit" type="submit" disabled={busy}>
            {busy ? 'Signing in…' : 'Sign in'}
          </button>
        </form>

        <div className="login__footer">
          <p className="login__foot-text">
            Don’t have an account?{' '}
            <a href="#" className="login__link" onClick={(event) => event.preventDefault()}>
              Contact your administrator
            </a>
          </p>
          <p className="login__foot-note">
            Protected by encryption.
            <br />
            Your credentials are never stored locally.
          </p>
          <p className="login__version">
            <span className="login__env-pill">Demo</span>
          </p>
        </div>
      </div>
    </div>
  );
}
