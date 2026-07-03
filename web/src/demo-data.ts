// Static placeholder content for the read-only browser preview.
//
// These values are illustrative only. They contain no credentials, no live
// endpoints, and no per-tenant data. The preview never calls a backend; it
// renders this fixed content so the three in-scope surfaces can be shown
// without authentication, network access, or write capability.

export interface PreviewSection {
  id: 'integrations' | 'skills' | 'rag-sources';
  title: string;
  blurb: string;
  items: PreviewItem[];
}

export interface PreviewItem {
  name: string;
  detail: string;
}

export const PREVIEW_SECTIONS: PreviewSection[] = [
  {
    id: 'integrations',
    title: 'Integrations',
    blurb: 'Catalog of data sources available to a workspace, shown as read-only entries.',
    items: [
      { name: 'Project Tracker', detail: 'Work items and status, available to a workspace.' },
      { name: 'Document Store', detail: 'Shared files and folders.' },
      { name: 'Calendar', detail: 'Schedules and events.' },
    ],
  },
  {
    id: 'skills',
    title: 'Skills',
    blurb: 'Reusable capabilities a workspace can offer, listed for reference.',
    items: [
      { name: 'Summarize', detail: 'Condense long content into key points.' },
      { name: 'Extract', detail: 'Pull structured fields from text.' },
      { name: 'Classify', detail: 'Sort items into categories.' },
    ],
  },
  {
    id: 'rag-sources',
    title: 'RAG sources',
    blurb: 'Knowledge collections that ground answers, listed with high-level stats.',
    items: [
      { name: 'Policies', detail: 'Reference documents and guidelines.' },
      { name: 'Product Docs', detail: 'Specifications and how-to material.' },
      { name: 'FAQ', detail: 'Common questions and answers.' },
    ],
  },
];
