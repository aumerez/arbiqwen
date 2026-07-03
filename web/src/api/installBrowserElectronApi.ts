// Attach the browser-local preview API at window.electronAPI.
//
// Idempotent and non-destructive: if a bridge is already present (for example
// a future real adapter, or one injected by a test), it is left untouched.
// The installer makes no network call, touches no persistent storage, and
// imports no Electron or desktop runtime code.

import { createBrowserElectronApi } from './browserElectronApi';
import type { BrowserElectronApi } from './types';

export function installBrowserElectronApi(target: Window = window): BrowserElectronApi {
  const existing = target.electronAPI;
  if (existing) {
    return existing;
  }
  const api = createBrowserElectronApi();
  target.electronAPI = api;
  return api;
}
