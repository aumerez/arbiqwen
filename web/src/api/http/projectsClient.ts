// Browser-local projects client. Lists the workspace's projects and, for a
// given project, reads and toggles which integrations / RAG sources are enabled
// (the project "Information Sources" controls). Enable/disable are real backend
// writes (POST/DELETE /projects/{id}/...-config/...). All chat/project network
// access for these lives here, in the approved HTTP adapter layer; errors are
// typed and non-secret.

import { BrowserReadError } from './httpClient';

export interface ProjectsClientConfig {
  baseUrl?: string;
  getToken?: () => string | null | undefined;
  fetchImpl?: typeof fetch;
}

export interface RawProject {
  id: number;
  name: string;
  description?: string | null;
  icon?: string | null;
  is_default: boolean;
}

export interface ProjectIntegrationsConfig {
  integration_ids: number[];
  integration_keys: string[];
}

export interface ProjectsClient {
  list(): Promise<RawProject[]>;
  listEnabledIntegrations(projectId: number): Promise<ProjectIntegrationsConfig>;
  listEnabledRagSources(projectId: number): Promise<number[]>;
  enableIntegration(projectId: number, instanceId: number): Promise<void>;
  disableIntegration(projectId: number, instanceId: number): Promise<void>;
  enableRagSource(projectId: number, sourceId: number): Promise<void>;
  disableRagSource(projectId: number, sourceId: number): Promise<void>;
}

const defaultFetch: typeof fetch = (input, init) => globalThis.fetch(input, init);

export function createProjectsClient(config: ProjectsClientConfig = {}): ProjectsClient {
  const base = (config.baseUrl ?? '').replace(/\/$/, '');
  const doFetch = config.fetchImpl ?? defaultFetch;
  const enc = encodeURIComponent;

  async function request<T>(method: string, path: string): Promise<T> {
    const headers: Record<string, string> = { Accept: 'application/json' };
    const token = config.getToken?.();
    if (token) headers.Authorization = `Bearer ${token}`;

    let response: Response;
    try {
      response = await doFetch(`${base}${path}`, { method, headers });
    } catch {
      throw new BrowserReadError('network', 'Network request failed');
    }
    if (!response.ok) {
      throw new BrowserReadError('http', `Request failed with status ${response.status}`, response.status);
    }
    if (response.status === 204) return undefined as T;
    try {
      return (await response.json()) as T;
    } catch {
      throw new BrowserReadError('parse', 'Received an invalid response');
    }
  }

  return {
    list: () => request<RawProject[]>('GET', '/projects'),
    listEnabledIntegrations: (projectId) =>
      request<ProjectIntegrationsConfig>('GET', `/projects/${enc(String(projectId))}/integrations-config`),
    listEnabledRagSources: (projectId) =>
      request<number[]>('GET', `/projects/${enc(String(projectId))}/rag-sources`),
    enableIntegration: (projectId, instanceId) =>
      request<void>('POST', `/projects/${enc(String(projectId))}/integrations-config/${enc(String(instanceId))}`),
    disableIntegration: (projectId, instanceId) =>
      request<void>('DELETE', `/projects/${enc(String(projectId))}/integrations-config/${enc(String(instanceId))}`),
    enableRagSource: (projectId, sourceId) =>
      request<void>('POST', `/projects/${enc(String(projectId))}/rag-sources/${enc(String(sourceId))}`),
    disableRagSource: (projectId, sourceId) =>
      request<void>('DELETE', `/projects/${enc(String(projectId))}/rag-sources/${enc(String(sourceId))}`),
  };
}
