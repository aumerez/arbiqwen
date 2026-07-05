// Browser-safe UI view models for the read-only preview cards. These hold only
// non-secret display fields; the adapter mappers populate them and never copy
// integration/skill config, tokens, or raw metadata.

/** A read-only integration entry as shown in the preview. */
export interface IntegrationDemo {
  id: string;
  name: string;
  description: string;
  category: string;
  /** Non-secret connection state for display only. */
  status: 'Connected' | 'Available';
  /** Optional count of read-only tools the integration surfaces. */
  toolCount?: number;
  /** Optional human-readable last-activity label. */
  lastActivity?: string;
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
