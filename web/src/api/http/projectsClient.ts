// Browser-local projects reader. Lists the workspace's projects (GET /projects —
// not under /api) so the sidebar can show "My Space" (the default project) and
// let the visitor switch projects. Read-only: no create/update/delete.

import { HttpClient, type HttpClientConfig } from './httpClient';

export interface RawProject {
  id: number;
  name: string;
  description?: string | null;
  icon?: string | null;
  is_default: boolean;
}

export interface ProjectsClient {
  list(): Promise<RawProject[]>;
}

export function createProjectsClient(config: HttpClientConfig = {}): ProjectsClient {
  const http = new HttpClient(config);
  return {
    list: () => http.getJson<RawProject[]>('/projects'),
  };
}
