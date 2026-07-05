// Loads the three in-scope sections (Integrations, Skills, RAG sources) from the
// read adapter after sign-in. Reads only — no writes, no driver/admin calls.
// Exposes a single state machine (loading | ready | error) plus a reload for the
// retry control. Errors are typed BrowserReadErrors so the UI can show a safe,
// non-secret message and decide whether to surface a setup hint.

import { useCallback, useEffect, useState } from 'react';
import type { ReadAdapter } from './api/http/readAdapter';
import { BrowserReadError } from './api/http/httpClient';
import { toIntegrationCards, toRagCards, toSkillCards } from './mappers';
import type { IntegrationDemo, RagSourceDemo, SkillDemo } from './viewModels';

export type SectionsState = 'loading' | 'ready' | 'error';

export interface SectionsData {
  integrations: IntegrationDemo[];
  skills: SkillDemo[];
  ragSources: RagSourceDemo[];
}

export interface UseSections {
  state: SectionsState;
  data: SectionsData | null;
  error: BrowserReadError | null;
  reload: () => void;
}

export function useSections(adapter: ReadAdapter): UseSections {
  const [state, setState] = useState<SectionsState>('loading');
  const [data, setData] = useState<SectionsData | null>(null);
  const [error, setError] = useState<BrowserReadError | null>(null);

  const load = useCallback(async () => {
    setState('loading');
    setError(null);
    try {
      const [integrations, skills, ragSources] = await Promise.all([
        adapter.integrations.list(),
        adapter.skills.list(),
        adapter.ragSources.list(),
      ]);
      setData({
        integrations: toIntegrationCards(integrations),
        skills: toSkillCards(skills),
        ragSources: toRagCards(ragSources),
      });
      setState('ready');
    } catch (err) {
      setError(
        err instanceof BrowserReadError ? err : new BrowserReadError('network', 'Unable to load the workspace'),
      );
      setState('error');
    }
  }, [adapter]);

  useEffect(() => {
    void load();
  }, [load]);

  return { state, data, error, reload: () => void load() };
}
