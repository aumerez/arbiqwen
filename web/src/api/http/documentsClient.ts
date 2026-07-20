// Fetches a document's file (GET /documents/{id}/file) for the preview panel.
// Binary types (PDF/image) come back as a blob URL for an iframe; text/markdown/
// HTML come back as text.

import { BrowserReadError } from './httpClient';
import type { DocumentRow } from '../../documents/documentMeta';

export interface DocumentFile {
  contentType: string;
  text?: string;
  url?: string;
}

export interface DocumentsClient {
  getFile(id: number | string): Promise<DocumentFile>;
  /** Fetch the document's raw bytes (GET /documents/{id}/file) for a browser
   *  save. Returns a Blob; the caller triggers the download. The endpoint needs
   *  the bearer token, so a plain anchor href won't work. */
  getBlob(id: number | string): Promise<Blob>;
  /** GET /documents/{id} — one document's metadata (used to poll index status). */
  get(id: number | string): Promise<DocumentRow>;
  /** POST /documents/upload — multipart upload of a chat attachment. */
  upload(file: File, projectId?: number | null): Promise<DocumentRow>;
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

    async getBlob(id) {
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
      return response.blob();
    },

    async get(id) {
      const headers: Record<string, string> = {};
      const token = config.getToken?.();
      if (token) headers.Authorization = `Bearer ${token}`;

      let response: Response;
      try {
        response = await doFetch(`${base}/documents/${encodeURIComponent(String(id))}`, { headers });
      } catch {
        throw new BrowserReadError('network', 'Network request failed');
      }
      if (!response.ok) {
        throw new BrowserReadError('http', `Request failed with status ${response.status}`, response.status);
      }
      return (await response.json()) as DocumentRow;
    },

    async upload(file, projectId) {
      // Multipart upload, mirroring the desktop's documents upload IPC. The
      // browser sends the real File bytes (the desktop sends a filesystem path);
      // both hit POST /documents/upload with an optional project_id form field.
      // The chat attachment flow is the one write the read-only demo permits.
      const headers: Record<string, string> = {};
      const token = config.getToken?.();
      if (token) headers.Authorization = `Bearer ${token}`;

      const form = new FormData();
      form.append('file', file, file.name);
      if (projectId != null) form.append('project_id', String(projectId));

      let response: Response;
      try {
        response = await doFetch(`${base}/documents/upload`, { method: 'POST', headers, body: form });
      } catch {
        throw new BrowserReadError('network', 'Network request failed');
      }
      if (!response.ok) {
        throw new BrowserReadError('http', `Upload failed with status ${response.status}`, response.status);
      }
      return (await response.json()) as DocumentRow;
    },
  };
}
