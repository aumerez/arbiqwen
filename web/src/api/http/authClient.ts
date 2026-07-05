// Browser-local sign-in for the view-only demo.
//
// Issues a single POST to {baseUrl}/auth/login and returns the access token.
// The refresh token, if present, is intentionally ignored — this demo holds
// only an in-memory access token and never refreshes. Errors are typed and
// non-secret: they never carry the URL, token, password, request/response
// headers, or the backend response body.

import { BrowserReadError } from './httpClient';

export interface LoginParams {
  /** Backend origin (no /api suffix). */
  baseUrl: string;
  email: string;
  password: string;
  /** Injectable fetch for tests. Defaults to the global browser fetch. */
  fetchImpl?: typeof fetch;
}

const defaultFetch: typeof fetch = (input, init) => globalThis.fetch(input, init);

/**
 * Authenticate with email + password and resolve to the access token string.
 * Rejects with a typed BrowserReadError on bad credentials, non-2xx status,
 * network failure, malformed JSON, or a missing access token.
 */
export async function login(params: LoginParams): Promise<string> {
  const { email, password } = params;
  const doFetch = params.fetchImpl ?? defaultFetch;
  const base = params.baseUrl.replace(/\/$/, '');
  const url = `${base}/auth/login`;

  let response: Response;
  try {
    response = await doFetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify({ email, password }),
    });
  } catch {
    throw new BrowserReadError('network', 'Unable to reach the backend');
  }

  if (response.status === 401) {
    throw new BrowserReadError('http', 'Invalid credentials', 401);
  }
  if (!response.ok) {
    throw new BrowserReadError('http', 'Sign-in failed', response.status);
  }

  let data: unknown;
  try {
    data = await response.json();
  } catch {
    throw new BrowserReadError('parse', 'Received an invalid response');
  }

  const token = (data as { accessToken?: unknown } | null)?.accessToken;
  if (typeof token !== 'string' || token.length === 0) {
    throw new BrowserReadError('parse', 'Sign-in response was incomplete');
  }
  return token;
}
