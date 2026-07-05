// Non-secret browser configuration, read from Vite env at call time so values
// can differ per environment without code changes. Anything in a VITE_* var is
// baked into the public bundle — never put secrets here.

export function getApiBaseUrl(): string {
  // Backend origin (no /api suffix). Empty means same-origin. One trailing
  // slash is stripped so endpoint paths join cleanly.
  const raw = (import.meta.env.VITE_API_BASE_URL ?? '').trim();
  return raw.replace(/\/$/, '');
}

export function getDemoEmail(): string {
  // Optional, non-secret email used only to prefill the sign-in field.
  return (import.meta.env.VITE_DEMO_EMAIL ?? '').trim();
}
