// Browser-local implementation of the narrow preview API.
//
// Supported startup methods return fixed, side-effect-free values so the UI can
// boot without a backend, tokens, native runtime, or Electron. Everything that
// would mutate, authenticate externally, execute, stream, or reach native
// behavior is fail-closed via `unsupported(...)`.
//
// Approved view-only read methods delegate to an injected read adapter when one
// is supplied; with no adapter they return the same token-free placeholders.
// This module itself performs no network requests, reads/writes no persistent
// storage, and contains no credentials.

import type { BrowserElectronApi } from './types';
import type { ReadAdapter } from './http/readAdapter';
import { noopSubscribe, unsupported } from './unsupported';

export interface CreateBrowserElectronApiOptions {
  /**
   * Optional read adapter. When provided, the approved view-only read methods
   * delegate to it (live fetch). When omitted, those methods return the same
   * deterministic, token-free placeholders used for safe startup.
   */
  readAdapter?: ReadAdapter;
}

export function createBrowserElectronApi(options: CreateBrowserElectronApiOptions = {}): BrowserElectronApi {
  const adapter = options.readAdapter;

  return {
    app: {
      // Deterministic default so the language bootstrap resolves immediately.
      getSetting: (key: string) => Promise.resolve(key === 'language' ? 'en' : null),
      setSetting: unsupported('app.setSetting'),
    },
    environment: {
      get: () =>
        Promise.resolve({
          env: 'demo',
          baseUrl: '',
          label: 'PREVIEW',
          configured: false,
        }),
    },
    getSyncState: () =>
      Promise.resolve({
        isOnline: false,
        syncStatus: 'idle',
        lastSyncTime: null,
        offlineQueueLength: 0,
      }),
    onSyncUpdate: noopSubscribe,
    onSyncQueueUpdate: noopSubscribe,
    onNetworkChange: noopSubscribe,

    auth: {
      // No active session until demo auth is implemented.
      getSession: () => Promise.resolve(null),
      login: unsupported('auth.login'),
      loginGoogle: unsupported('auth.loginGoogle'),
      logout: () => Promise.resolve(),
    },

    branding: {
      getBranding: () =>
        Promise.resolve({
          tenant_id: 0,
          tenant_name: 'Preview',
          logo_url: null,
          colors: {
            primary: '#4f46e5',
            background: '#0a0a0b',
            text: '#e7e7e9',
            accent: '#22d3ee',
          },
        }),
    },
    tenantConfig: {
      fetch: () =>
        Promise.resolve({
          tenant_id: 0,
          system_prompt: null,
          model_config: { temperature: 0, max_tokens: 0 },
          prompt_version: 'preview',
        }),
      save: unsupported('tenantConfig.save'),
    },
    aiConfig: {
      listModels: () => Promise.resolve([]),
      createModel: unsupported('aiConfig.createModel'),
      updateModel: unsupported('aiConfig.updateModel'),
      deleteModel: unsupported('aiConfig.deleteModel'),
    },
    projects: {
      list: () => Promise.resolve([]),
    },
    documents: {
      list: () => (adapter ? adapter.documents.list() : Promise.resolve([])),
    },
    sources: {
      list: () => Promise.resolve([]),
    },

    integrations: {
      list: () => (adapter ? adapter.integrations.list() : Promise.resolve({ drivers: [], instances: [] })),
      marketplace: () => (adapter ? adapter.integrations.marketplace() : Promise.resolve({ tiles: [] })),
      listTools: (id) =>
        adapter ? adapter.integrations.listTools(id) : Promise.resolve({ integration: null, tools: [] }),
      schema: (key) => (adapter ? adapter.integrations.schema(key) : Promise.resolve(null)),
      status: (id) => (adapter ? adapter.integrations.status(id) : Promise.resolve(null)),
      oauthLinked: () =>
        adapter ? adapter.integrations.oauthLinked() : Promise.resolve({ linked_integrations: [] }),
      connect: unsupported('integrations.connect'),
      update: unsupported('integrations.update'),
      disconnect: unsupported('integrations.disconnect'),
      reconnect: unsupported('integrations.reconnect'),
      delete: unsupported('integrations.delete'),
      toggleDashboard: unsupported('integrations.toggleDashboard'),
      testConnection: unsupported('integrations.testConnection'),
      executeTool: unsupported('integrations.executeTool'),
      startOAuth: unsupported('integrations.startOAuth'),
      oauthDisconnect: unsupported('integrations.oauthDisconnect'),
    },
    skills: {
      list: () => (adapter ? adapter.skills.list() : Promise.resolve([])),
      toggle: unsupported('skills.toggle'),
    },
    ragSources: {
      list: () => (adapter ? adapter.ragSources.list() : Promise.resolve([])),
      stats: () => (adapter ? adapter.ragSources.stats() : Promise.resolve({})),
      listDrivers: () => (adapter ? adapter.ragSources.listDrivers() : Promise.resolve([])),
      create: unsupported('ragSources.create'),
      update: unsupported('ragSources.update'),
      delete: unsupported('ragSources.delete'),
      validate: unsupported('ragSources.validate'),
      generateDescription: unsupported('ragSources.generateDescription'),
    },

    agents: {
      // List only; never any execution behavior.
      list: () => Promise.resolve([]),
      run: unsupported('agents.run'),
      rerun: unsupported('agents.rerun'),
      delete: unsupported('agents.delete'),
    },
    notifications: {
      connect: () => Promise.resolve(),
      onPush: noopSubscribe,
      list: () => Promise.resolve({ items: [], unreadCount: 0, total: 0 }),
      markRead: unsupported('notifications.markRead'),
      dismiss: unsupported('notifications.dismiss'),
      readAll: unsupported('notifications.readAll'),
    },
    chat: {
      list: () => Promise.resolve([]),
      send: unsupported('chat.send'),
      stream: unsupported('chat.stream'),
    },
    updates: {
      getState: unsupported('updates.getState'),
      check: unsupported('updates.check'),
      download: unsupported('updates.download'),
      install: unsupported('updates.install'),
    },
    dialog: {
      showOpen: unsupported('dialog.showOpen'),
      showSave: unsupported('dialog.showSave'),
    },
    localDrive: {
      read: unsupported('localDrive.read'),
      write: unsupported('localDrive.write'),
    },
  };
}
