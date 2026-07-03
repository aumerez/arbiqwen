// Narrow, browser-local types for the preview's window.electronAPI-compatible
// surface. These are redefined here on purpose — the browser client never
// imports the desktop preload interface or any Electron type. Shapes mirror
// only the small subset of fields the preview's startup path needs; they are
// intentionally not the full desktop contract.

import type {
  DocumentView,
  IntegrationDriverView,
  IntegrationInstanceView,
  IntegrationSchemaView,
  IntegrationStatusView,
  IntegrationToolsView,
  LinkedIntegrationView,
  MarketplaceTileView,
  RagDriverView,
  RagSourceView,
  SkillView,
} from './http/readAdapter';

export type Unsubscribe = () => void;

/** Reported environment for the preview: no remote backend is wired. */
export interface BrowserEnvironmentInfo {
  env: 'demo';
  baseUrl: string;
  label: string;
  configured: boolean;
}

/** Sync is never active in the preview. */
export interface BrowserSyncState {
  isOnline: boolean;
  syncStatus: string;
  lastSyncTime: string | null;
  offlineQueueLength: number;
}

/** Auth session shape; the preview returns null until demo auth exists. */
export interface BrowserAuthSession {
  userId: string;
  email: string;
  role: string;
}

export interface BrowserBranding {
  tenant_id: number;
  tenant_name: string;
  logo_url: string | null;
  colors: { primary: string; background: string; text: string; accent: string };
}

export interface BrowserTenantConfig {
  tenant_id: number;
  system_prompt: string | null;
  model_config: { temperature: number; max_tokens: number };
  prompt_version: string;
}

export interface BrowserNotificationList {
  items: never[];
  unreadCount: number;
  total: number;
}

export interface BrowserIntegrationList {
  drivers: IntegrationDriverView[];
  instances: IntegrationInstanceView[];
}

type FailClosed = (...args: unknown[]) => Promise<never>;

/**
 * The minimal API the browser preview attaches at window.electronAPI.
 *
 * Supported members return deterministic, side-effect-free values for startup.
 * Every member typed as FailClosed rejects with a typed error and performs no
 * backend, native, OAuth, execution, or mutation behavior.
 */
export interface BrowserElectronApi {
  app: {
    getSetting: (key: string) => Promise<unknown>;
    setSetting: FailClosed;
  };
  environment: {
    get: () => Promise<BrowserEnvironmentInfo>;
  };
  getSyncState: () => Promise<BrowserSyncState>;
  onSyncUpdate: (cb: (...args: unknown[]) => void) => Unsubscribe;
  onSyncQueueUpdate: (cb: (...args: unknown[]) => void) => Unsubscribe;
  onNetworkChange: (cb: (...args: unknown[]) => void) => Unsubscribe;

  auth: {
    getSession: () => Promise<BrowserAuthSession | null>;
    login: FailClosed;
    loginGoogle: FailClosed;
    logout: () => Promise<void>;
  };

  branding: {
    getBranding: (tenantId?: number) => Promise<BrowserBranding>;
  };
  tenantConfig: {
    fetch: (tenantId?: number) => Promise<BrowserTenantConfig>;
    save: FailClosed;
  };
  aiConfig: {
    listModels: (type?: string) => Promise<never[]>;
    createModel: FailClosed;
    updateModel: FailClosed;
    deleteModel: FailClosed;
  };
  projects: {
    list: () => Promise<never[]>;
  };
  documents: {
    list: (projectId?: number, includeAll?: boolean) => Promise<DocumentView[]>;
  };
  sources: {
    list: (projectId?: number) => Promise<never[]>;
  };

  integrations: {
    list: () => Promise<BrowserIntegrationList>;
    marketplace: () => Promise<{ tiles: MarketplaceTileView[] }>;
    listTools: (id: number | string) => Promise<IntegrationToolsView>;
    schema: (key: string) => Promise<IntegrationSchemaView | null>;
    status: (id: number | string) => Promise<IntegrationStatusView | null>;
    oauthLinked: () => Promise<{ linked_integrations: LinkedIntegrationView[] }>;
    connect: FailClosed;
    update: FailClosed;
    disconnect: FailClosed;
    reconnect: FailClosed;
    delete: FailClosed;
    toggleDashboard: FailClosed;
    testConnection: FailClosed;
    executeTool: FailClosed;
    startOAuth: FailClosed;
    oauthDisconnect: FailClosed;
  };
  skills: {
    list: () => Promise<SkillView[]>;
    toggle: FailClosed;
  };
  ragSources: {
    list: () => Promise<RagSourceView[]>;
    stats: () => Promise<Record<string, unknown>>;
    listDrivers: () => Promise<RagDriverView[]>;
    create: FailClosed;
    update: FailClosed;
    delete: FailClosed;
    validate: FailClosed;
    generateDescription: FailClosed;
  };

  agents: {
    list: () => Promise<never[]>;
    run: FailClosed;
    rerun: FailClosed;
    delete: FailClosed;
  };
  notifications: {
    connect: () => Promise<void>;
    onPush: (cb: (...args: unknown[]) => void) => Unsubscribe;
    list: () => Promise<BrowserNotificationList>;
    markRead: FailClosed;
    dismiss: FailClosed;
    readAll: FailClosed;
  };
  chat: {
    list: () => Promise<never[]>;
    send: FailClosed;
    stream: FailClosed;
  };
  updates: {
    getState: FailClosed;
    check: FailClosed;
    download: FailClosed;
    install: FailClosed;
  };
  dialog: {
    showOpen: FailClosed;
    showSave: FailClosed;
  };
  localDrive: {
    read: FailClosed;
    write: FailClosed;
  };
}

declare global {
  interface Window {
    electronAPI?: BrowserElectronApi;
  }
}
