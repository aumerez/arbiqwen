// Read-only lists for the dashboard widgets that aren't covered by the read
// adapter: playbooks, dashboards, and agents. All GET reads.

import { HttpClient, type HttpClientConfig } from './httpClient';

export interface RawPlaybook {
  id: string | number;
  name: string;
  status?: string;
  project_id?: number;
}

export interface RawDashboard {
  id: number;
  title: string;
  project_id?: number;
}

export interface RawAgent {
  id: number;
  title: string;
  status?: string;
  project_id?: number | null;
}

export interface WorkspaceClient {
  listPlaybooks(projectId?: number | null): Promise<RawPlaybook[]>;
  listDashboards(projectId?: number | null): Promise<RawDashboard[]>;
  listAgents(): Promise<RawAgent[]>;
}

export function createWorkspaceClient(config: HttpClientConfig = {}): WorkspaceClient {
  const http = new HttpClient(config);
  const projectQuery = (projectId?: number | null) =>
    projectId === undefined || projectId === null ? undefined : { project_id: String(projectId) };

  return {
    listPlaybooks: (projectId) => http.getJson<RawPlaybook[]>('/playbooks', { query: projectQuery(projectId) }),
    listDashboards: (projectId) => http.getJson<RawDashboard[]>('/dashboards', { query: projectQuery(projectId) }),
    listAgents: () => http.getJson<RawAgent[]>('/api/agents'),
  };
}
