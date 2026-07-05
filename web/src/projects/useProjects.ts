import { useCallback, useEffect, useMemo, useState } from 'react';
import type { ProjectsClient, RawProject } from '../api/http/projectsClient';

// Loads the workspace's projects and tracks the active one. The default project
// ("My Space") is auto-selected on load, mirroring the desktop app.

export interface ProjectView {
  id: number;
  name: string;
  description?: string;
  icon?: string;
  isDefault: boolean;
}

function toProject(raw: RawProject): ProjectView {
  return {
    id: raw.id,
    name: raw.name,
    description: raw.description ?? undefined,
    icon: raw.icon ?? undefined,
    isDefault: raw.is_default,
  };
}

export interface UseProjects {
  projects: ProjectView[];
  currentProject: ProjectView | null;
  loading: boolean;
  selectProject: (id: number) => void;
  goToMySpace: () => void;
}

export function useProjects(client: ProjectsClient): UseProjects {
  const [projects, setProjects] = useState<ProjectView[]>([]);
  const [currentId, setCurrentId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        const raw = await client.list();
        if (cancelled) return;
        const mapped = raw.map(toProject);
        setProjects(mapped);
        const fallback = mapped.find((p) => p.isDefault) ?? mapped[0] ?? null;
        setCurrentId((prev) => prev ?? fallback?.id ?? null);
      } catch {
        if (!cancelled) setProjects([]);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [client]);

  const currentProject = useMemo(
    () => projects.find((p) => p.id === currentId) ?? null,
    [projects, currentId],
  );

  const selectProject = useCallback((id: number) => setCurrentId(id), []);
  const goToMySpace = useCallback(() => {
    setCurrentId((prev) => projects.find((p) => p.isDefault)?.id ?? prev);
  }, [projects]);

  return { projects, currentProject, loading, selectProject, goToMySpace };
}
