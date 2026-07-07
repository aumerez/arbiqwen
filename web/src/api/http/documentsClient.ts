// Fetches a document's file (GET /documents/{id}/file) for the preview panel.
// Binary types (PDF/image) come back as a blob URL for an iframe; text/markdown/
// HTML come back as text.

import { BrowserReadError } from './httpClient';

export interface DocumentFile {
  contentType: string;
  text?: string;
  url?: string;
}

export interface DocumentsClient {
  getFile(id: number | string): Promise<DocumentFile>;
}

const defaultFetch: typeof fetch = (input, init) => globalThis.fetch(input, init);

export interface DocumentsClientConfig {
  baseUrl?: string;
  getToken?: () => string | null | undefined;
  fetchImpl?: typeof fetch;
}

export function createDocumentsClient(config: DocumentsClientConfig = {}): DocumentsClient {
  const base = (config.baseUrl ?? '').replace(/\/$/, '');
  const doFetch = config.fetchImpl ?? defaultFetch;

  return {
    async getFile(id) {
      const headers: Record<string, string> = {};
      const token = config.getToken?.();
      if (token) headers.Authorization = `Bearer ${token}`;

      let response: Response;
      try {
        response = await doFetch(`${base}/documents/${encodeURIComponent(String(id))}/file`, { headers });
      } catch {
        throw new BrowserReadError('network', 'Network request failed');
      }
      if (!response.ok) {
        throw new BrowserReadError('http', `Request failed with status ${response.status}`, response.status);
      }
      const contentType = response.headers?.get?.('content-type') ?? '';
      const ct = contentType.toLowerCase();
      if (ct.includes('pdf') || ct.includes('image/')) {
        const blob = await response.blob();
        return { contentType, url: URL.createObjectURL(blob) };
      }
      const text = await response.text();
      return { contentType, text };
    },
  };
}
