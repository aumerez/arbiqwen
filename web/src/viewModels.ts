// Browser-safe UI view models for the read-only preview cards. These hold only
// non-secret display fields; the adapter mappers populate them and never copy
// integration/skill config, tokens, or raw metadata.

/** A read-only integration entry as shown in the preview. */
export interface IntegrationDemo {
  id: string;
  /** Primary line — the instance alias (desktop's instanceAlias). */
  name: string;
  description: string;
  category: string;
  /** lucide icon name from the driver (desktop iconName). Falls back to Puzzle. */
  iconName?: string;
  /** Driver version, rendered as a "vX" chip next to the name. */
  version?: string;
  /** Driver display name — shown as a subtitle when it differs from the alias. */
  driverName?: string;
  /** Non-secret workspace label from metadata, appended to the subtitle. */
  workspaceName?: string;
  /** Non-secret connection state for display only. */
  status: 'Connected' | 'Disconnected';
}

/** A read-only skill entry as shown in the preview. */
export interface SkillDemo {
  id: string;
  name: string;
  description: string;
  category: string;
  status: 'Active' | 'Available';
}

/** A read-only knowledge-source entry as shown in the preview. */
export interface RagSourceDemo {
  id: string;
  name: string;
  description: string;
  type: string;
  status: 'Ready' | 'Pending';
  /** Optional document tally for display only. */
  documentCount?: number;
}
