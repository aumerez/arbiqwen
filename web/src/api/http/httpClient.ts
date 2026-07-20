// Minimal browser-local HTTP client for view-only reads.
//
// Everything is injected: the base URL, a memory-only token getter, and the
// fetch implementation (so tests can supply a stub). Nothing is persisted —
// no storage, no cookies, no module-level token. Errors are typed and never
// echo backend response bodies, tokens, headers, or credentials.

export type BrowserReadErrorKind = 'network' | 'http' | 'parse' | 'too_large';

export class BrowserReadError extends Error {
  readonly kind: BrowserReadErrorKind;
  /** Present for 'http' errors only. */
  readonly status?: number;

  constructor(kind: BrowserReadErrorKind, message: string, status?: number) {
    super(message);
    this.name = 'BrowserReadError';
    this.kind = kind;
    this.status = status;
  }
}

export interface HttpClientConfig {
  /** Base URL prepended to every path. Empty string means same-origin. */
  baseUrl?: string;
  /** Memory-only token source. Returns a token to attach, or nothing. */
  getToken?: () => string | null | undefined;
  /** Injectable fetch. Defaults to the global browser fetch. */
  fetchImpl?: typeof fetch;
}

export interface HttpGetOptions {
  /** Query parameters, encoded with URLSearchParams. */
  query?: Record<string, string>;
}

const defaultFetch: typeof fetch = (input, init) => globalThis.fetch(input, init);

export class HttpClient {
  private readonly baseUrl: string;
  private readonly getToken?: () => string | null | undefined;
  private readonly fetchImpl: typeof fetch;

  constructor(config: HttpClientConfig = {}) {
    this.baseUrl = config.baseUrl ?? '';
    this.getToken = config.getToken;
    this.fetchImpl = config.fetchImpl ?? defaultFetch;
  }

  /**
   * Issue a GET and parse JSON. Attaches a bearer header only when a token is
   * available. Rejects with a typed, non-secret BrowserReadError on network
   * failure, non-2xx status, or invalid JSON.
   */
  async getJson<T>(path: string, options: HttpGetOptions = {}): Promise<T> {
    const url = this.buildUrl(path, options.query);

    const headers: Record<string, string> = { Accept: 'application/json' };
    const token = this.getToken?.();
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    let response: Response;
    try {
      response = await this.fetchImpl(url, { method: 'GET', headers });
    } catch {
      // Do not surface the underlying error — it may carry URL/host detail.
      throw new BrowserReadError('network', 'Network request failed');
    }

    if (!response.ok) {
      // Status only — never the response body.
      throw new BrowserReadError('http', `Request failed with status ${response.status}`, response.status);
    }

    try {
      return (await response.json()) as T;
    } catch {
      throw new BrowserReadError('parse', 'Received an invalid response');
    }
  }

  private buildUrl(path: string, query?: Record<string, string>): string {
    // Strip a trailing slash from the base only; the path keeps its own shape
    // (e.g. '/documents/' must preserve its trailing slash).
    const base = this.baseUrl.replace(/\/$/, '');
    let url = `${base}${path}`;
    if (query && Object.keys(query).length > 0) {
      url += `?${new URLSearchParams(query).toString()}`;
    }
    return url;
  }
}
