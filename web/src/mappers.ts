// Map browser-safe read-adapter views into the UI card view models.
//
// Only non-secret display fields are carried across. Integration/skill config,
// raw metadata, connection secrets, and tokens are never read here — the
// adapter already drops config, and these mappers select a fixed allowlist of
// fields rather than spreading whole objects.

import type { IntegrationListView, RagSourceView, SkillView } from './api/http/readAdapter';
import type { IntegrationDemo, RagSourceDemo, SkillDemo } from './viewModels';

function isConnected(status: string | undefined, connectedAt: string | null | undefined): boolean {
  if (connectedAt) return true;
  return (status ?? '').toLowerCase() === 'connected';
}

export function toIntegrationCards(view: IntegrationListView): IntegrationDemo[] {
  return view.instances.map((inst) => {
    const alias = inst.instanceAlias || inst.name || inst.key || 'Integration';
    const driverName = inst.name && inst.name !== alias ? inst.name : undefined;
    // workspace_name is a non-secret display label some drivers report; the
    // desktop card appends it to the subtitle. Read it defensively.
    const meta = (inst.metadata ?? null) as { workspace_name?: unknown } | null;
    const workspaceName = typeof meta?.workspace_name === 'string' ? meta.workspace_name : undefined;
    return {
      id: String(inst.id),
      name: alias,
      description: inst.description ?? '',
      category: inst.category ?? 'Integration',
      iconName: inst.iconName,
      version: inst.version || undefined,
      driverName,
      workspaceName,
      status: isConnected(inst.status, inst.connectedAt) ? 'Connected' : 'Disconnected',
    };
  });
}

export function toSkillCards(views: SkillView[]): SkillDemo[] {
  return views.map((skill) => ({
    id: skill.key,
    name: skill.name ?? skill.key,
    description: skill.description ?? '',
    category: skill.category ?? 'Skill',
    status: skill.enabled ? 'Active' : 'Available',
  }));
}

export function toRagCards(views: RagSourceView[]): RagSourceDemo[] {
  return views.map((source) => ({
    id: String(source.id),
    name: source.label ?? source.ragKey ?? 'Knowledge base',
    description: source.description ?? '',
    type: source.driverKey ?? 'Knowledge base',
    status: source.enabled ? 'Ready' : 'Pending',
  }));
}
