// In-memory access token for the browser demo.
//
// The token is held only in module memory for the lifetime of the page. It is
// never written to localStorage, sessionStorage, cookies, IndexedDB, the
// filesystem, or any native secure store, and there is no hardcoded default.
// Logout clears it.

let accessToken: string | null = null;

export function getToken(): string | null {
  return accessToken;
}

export function setToken(token: string): void {
  accessToken = token;
}

export function clearToken(): void {
  accessToken = null;
}
