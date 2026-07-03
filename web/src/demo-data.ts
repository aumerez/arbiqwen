// Local, typed demo content for the read-only browser preview.
//
// Everything here is fictional and browser-safe: no real tenant identifiers,
// no credentials, no tokens, no secrets, no live endpoints, and no dependency
// on any backend seed. The preview renders this fixed content directly.

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

export const INTEGRATIONS: IntegrationDemo[] = [
  {
    id: 'project-tracker',
    name: 'Project Tracker',
    description: 'Work items, boards, and status rolled up for a workspace.',
    category: 'Project management',
    status: 'Connected',
    toolCount: 6,
    lastActivity: '2 hours ago',
  },
  {
    id: 'document-store',
    name: 'Document Store',
    description: 'Shared files and folders organized by team.',
    category: 'Storage',
    status: 'Connected',
    toolCount: 4,
    lastActivity: 'Yesterday',
  },
  {
    id: 'calendar',
    name: 'Calendar',
    description: 'Schedules, events, and availability across the workspace.',
    category: 'Productivity',
    status: 'Connected',
    toolCount: 3,
    lastActivity: 'Today',
  },
  {
    id: 'support-desk',
    name: 'Support Desk',
    description: 'Customer tickets and conversation history.',
    category: 'Support',
    status: 'Available',
  },
];

export const SKILLS: SkillDemo[] = [
  {
    id: 'summarize',
    name: 'Summarize',
    description: 'Condense long content into a short set of key points.',
    category: 'Text',
    status: 'Active',
  },
  {
    id: 'extract',
    name: 'Extract',
    description: 'Pull structured fields out of unstructured text.',
    category: 'Text',
    status: 'Active',
  },
  {
    id: 'classify',
    name: 'Classify',
    description: 'Sort items into a set of predefined categories.',
    category: 'Analysis',
    status: 'Available',
  },
  {
    id: 'translate',
    name: 'Translate',
    description: 'Convert content between supported languages.',
    category: 'Text',
    status: 'Available',
  },
];

export const RAG_SOURCES: RagSourceDemo[] = [
  {
    id: 'policies',
    name: 'Policies',
    description: 'Reference documents and internal guidelines.',
    type: 'Document collection',
    status: 'Ready',
    documentCount: 128,
  },
  {
    id: 'product-docs',
    name: 'Product Docs',
    description: 'Specifications, how-to guides, and release notes.',
    type: 'Document collection',
    status: 'Ready',
    documentCount: 342,
  },
  {
    id: 'faq',
    name: 'FAQ',
    description: 'Common questions paired with vetted answers.',
    type: 'Knowledge base',
    status: 'Ready',
    documentCount: 57,
  },
];
