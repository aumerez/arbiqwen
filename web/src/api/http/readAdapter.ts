// Browser-local view-only read adapter.
//
// Maps the approved read methods to explicit endpoints (mindful that /skills,
// /documents/, and /integrations/{key}/schema are NOT under /api), shapes
// responses into browser-safe view models, and drops sensitive fields before
// they reach the browser. Only reads are implemented here; writes/OAuth/native
// stay fail-closed in the API boundary and never reach this module.

import { BrowserReadError, HttpClient, type HttpClientConfig } from './httpClient';

// ---- Browser-facing view models (camelCase, non-secret) --------------------

export interface IntegrationInstanceView {
  id: number | string;
  key?: string;
  name?: string;
  instanceAlias?: string;
  description?: string;
  category?: string;
  iconName?: string;
  version?: string;
  configMode?: string;
  status?: string;
  metadata?: unknown;
  connectedAt?: string | null;
  dashboardEnabled?: boolean;
}

export interface IntegrationDriverView {
  key?: string;
  name?: string;
  description?: string;
  category?: string;
  requiredScopes?: string[];
}

export interface IntegrationListView {
  drivers: IntegrationDriverView[];
  instances: IntegrationInstanceView[];
}

export interface MarketplaceTileView {
  key?: string;
  name?: string;
  description?: string;
  category?: string;
  iconName?: string;
  version?: string;
}

export interface LinkedIntegrationView {
  key?: string;
  name?: string;
  provider?: string;
  status?: string;
  connectedAt?: string | null;
}

export interface IntegrationToolsView {
  integration: unknown;
  tools: unknown[];
}

export type IntegrationSchemaView = unknown;

export interface IntegrationStatusView {
  id: number | string;
  instanceAlias?: string;
  status?: string;
  connectedAt?: string | null;
  metadata?: unknown;
}

export interface SkillView {
  key: string;
  name?: string;
  description?: string;
  category?: string;
  icon?: string;
  enabled?: boolean;
  version?: string;
  package?: string;
  // NOTE: `config` is intentionally never carried here.
}

export interface RagSourceView {
  id: number | string;
  ragKey?: string;
  driverKey?: string;
  label?: string;
  description?: string;
  writable?: boolean;
  enabled?: boolean;
  createdAt?: string;
  updatedAt?: string | null;
}

export interface RagDriverView {
  key?: string;
  label?: string;
  description?: string;
  configSchema?: unknown;
}

export type DocumentView = unknown;

export interface ReadAdapter {
  integrations: {
    list(): Promise<IntegrationListView>;
    marketplace(): Promise<{ tiles: MarketplaceTileView[] }>;
    listTools(id: number | string): Promise<IntegrationToolsView>;
    schema(key: string): Promise<IntegrationSchemaView>;
    status(id: number | string): Promise<IntegrationStatusView>;
    oauthLinked(): Promise<{ linked_integrations: LinkedIntegrationView[] }>;
  };
  skills: {
    list(): Promise<SkillView[]>;
  };
  ragSources: {
    list(): Promise<RagSourceView[]>;
    stats(): Promise<Record<string, unknown>>;
    listDrivers(): Promise<RagDriverView[]>;
  };
  documents: {
    list(): Promise<DocumentView[]>;
  };
}

// ---- Shaping helpers -------------------------------------------------------

type Raw = Record<string, unknown>;

function asArray(value: unknown): Raw[] {
  return Array.isArray(value) ? (value as Raw[]) : [];
}

function shapeInstance(raw: Raw): IntegrationInstanceView {
  return {
    id: raw.id as number | string,
    key: raw.key as string | undefined,
    name: raw.name as string | undefined,
    instanceAlias: raw.instance_alias as string | undefined,
    description: raw.description as string | undefined,
    category: raw.category as string | undefined,
    iconName: raw.icon_name as string | undefined,
    version: raw.version as string | undefined,
    configMode: raw.config_mode as string | undefined,
    status: raw.status as string | undefined,
    metadata: raw.metadata,
    connectedAt: (raw.connected_at as string | null | undefined) ?? null,
    dashboardEnabled: !!raw.dashboard_enabled,
  };
}

function shapeDriver(raw: Raw): IntegrationDriverView {
  return {
    key: raw.key as string | undefined,
    name: raw.name as string | undefined,
    description: raw.description as string | undefined,
    category: raw.category as string | undefined,
    requiredScopes: raw.required_scopes as string[] | undefined,
  };
}

function shapeMarketplaceTile(raw: Raw): MarketplaceTileView {
  return {
    key: raw.key as string | undefined,
    name: raw.name as string | undefined,
    description: raw.description as string | undefined,
    category: raw.category as string | undefined,
    iconName: raw.icon_name as string | undefined,
    version: raw.version as string | undefined,
  };
}

function shapeLinked(raw: Raw): LinkedIntegrationView {
  return {
    key: raw.key as string | undefined,
    name: raw.name as string | undefined,
    provider: raw.provider as string | undefined,
    status: raw.status as string | undefined,
    connectedAt: (raw.connected_at as string | null | undefined) ?? null,
  };
}

function shapeSkill(raw: Raw): SkillView {
  // Build a fresh object that picks only non-secret fields. `config` (which can
  // hold tenant secrets) is never copied.
  return {
    key: raw.key as string,
    name: raw.name as string | undefined,
    description: raw.description as string | undefined,
    category: raw.category as string | undefined,
    icon: raw.icon_name as string | undefined,
    enabled: raw.enabled as boolean | undefined,
    version: raw.version as string | undefined,
    package: raw.package as string | undefined,
  };
}

function shapeRagSource(raw: Raw): RagSourceView {
  return {
    id: raw.id as number | string,
    ragKey: raw.rag_key as string | undefined,
    driverKey: raw.driver_key as string | undefined,
    label: raw.label as string | undefined,
    description: raw.description as string | undefined,
    writable: raw.writable as boolean | undefined,
    enabled: raw.enabled as boolean | undefined,
    createdAt: raw.created_at as string | undefined,
    updatedAt: (raw.updated_at as string | null | undefined) ?? null,
  };
}

function shapeRagDriver(raw: Raw): RagDriverView {
  return {
    key: raw.key as string | undefined,
    label: raw.label as string | undefined,
    description: raw.description as string | undefined,
    configSchema: raw.config_schema,
  };
}

function shapeStatus(raw: Raw): IntegrationStatusView {
  return {
    id: raw.id as number | string,
    instanceAlias: raw.instance_alias as string | undefined,
    status: raw.status as string | undefined,
    connectedAt: (raw.connected_at as string | null | undefined) ?? null,
    metadata: raw.metadata,
  };
}

// ---- Adapter ---------------------------------------------------------------

export function createReadAdapter(config: HttpClientConfig = {}): ReadAdapter {
  const http = new HttpClient(config);
  const enc = encodeURIComponent;

  return {
    integrations: {
      async list() {
        const raw = await http.getJson<Raw>('/api/integrations/');
        return {
          drivers: asArray(raw.drivers).map(shapeDriver),
          instances: asArray(raw.instances).map(shapeInstance),
        };
      },
      async marketplace() {
        const raw = await http.getJson<Raw>('/api/integrations/marketplace');
        return { tiles: asArray(raw.tiles).map(shapeMarketplaceTile) };
      },
      async listTools(id) {
        const raw = await http.getJson<Raw>(`/api/integrations/instances/${enc(String(id))}/tools`);
        return { integration: raw.integration ?? null, tools: asArray(raw.tools) };
      },
      async schema(key) {
        // Non-/api package route. Field-definition schema only (no secret values).
        return http.getJson<IntegrationSchemaView>(`/integrations/${enc(key)}/schema`);
      },
      async status(id) {
        const raw = await http.getJson<Raw>(`/api/integrations/instances/${enc(String(id))}/status`);
        return shapeStatus(raw);
      },
      async oauthLinked() {
        const raw = await http.getJson<Raw>('/api/integrations/oauth/linked-integrations');
        return { linked_integrations: asArray(raw.linked_integrations).map(shapeLinked) };
      },
    },

    skills: {
      async list() {
        // Non-/api route.
        const raw = await http.getJson<unknown>('/skills');
        return asArray(raw).map(shapeSkill);
      },
    },

    ragSources: {
      async list() {
        const raw = await http.getJson<unknown>('/api/rag-sources');
        return asArray(raw).map(shapeRagSource);
      },
      async stats() {
        return http.getJson<Record<string, unknown>>('/api/rag-sources/stats');
      },
      async listDrivers() {
        // Admin-gated endpoint. A read-only role cannot see drivers, so a 403
        // degrades to an empty list rather than an error. Any other failure
        // (including other statuses) propagates.
        try {
          const raw = await http.getJson<unknown>('/api/rag-sources/drivers');
          return asArray(raw).map(shapeRagDriver);
        } catch (err) {
          if (err instanceof BrowserReadError && err.status === 403) {
            return [];
          }
          throw err;
        }
      },
    },

    documents: {
      async list() {
        // Non-/api route with a significant trailing slash.
        const raw = await http.getJson<Raw>('/documents/', {
          query: { include_all: 'true', limit: '100' },
        });
        return asArray(raw.documents);
      },
    },
  };
}
