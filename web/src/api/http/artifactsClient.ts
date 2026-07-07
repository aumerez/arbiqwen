// Fetches raw artifact content (GET /artifacts/{id}/content) for the preview
// panel. Returns the body text plus its content type so the panel can render
// HTML dashboards in an iframe and markdown/text via the markdown renderer.

import { BrowserReadError } from './httpClient';

export interface ArtifactContent {
  contentType: string;
  text: string;
}

export interface ArtifactsClient {
  getContent(id: number | string): Promise<ArtifactContent>;
}

const defaultFetch: typeof fetch = (input, init) => globalThis.fetch(input, init);

export interface ArtifactsClientConfig {
  baseUrl?: string;
  getToken?: () => string | null | undefined;
  fetchImpl?: typeof fetch;
}

export function createArtifactsClient(config: ArtifactsClientConfig = {}): ArtifactsClient {
  const base = (config.baseUrl ?? '').replace(/\/$/, '');
  const doFetch = config.fetchImpl ?? defaultFetch;

  return {
    async getContent(id) {
      const headers: Record<string, string> = {};
      const token = config.getToken?.();
      if (token) headers.Authorization = `Bearer ${token}`;

      let response: Response;
      try {
        response = await doFetch(`${base}/artifacts/${encodeURIComponent(String(id))}/content`, { headers });
      } catch {
        throw new BrowserReadError('network', 'Network request failed');
      }
      if (!response.ok) {
        throw new BrowserReadError('http', `Request failed with status ${response.status}`, response.status);
      }
      const contentType = response.headers?.get?.('content-type') ?? '';
      const text = await response.text();
      return { contentType, text };
    },
  };
}
