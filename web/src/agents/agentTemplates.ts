import {
  Activity,
  AlertTriangle,
  FileSignature,
  HardDrive,
  ListChecks,
  MessagesSquare,
  Presentation,
  Search,
  UserCheck,
  type LucideIcon,
} from 'lucide-react';

// Agent templates — the "Templates to get started" gallery from the desktop
// ActiveAgentsWidget full view, ported read-only for the browser demo. Each card
// shows what kind of agent the platform can spawn; clicking one drafts a fresh
// chat seeded with the prompt (chat is the demo's one interactive surface — the
// user reviews the draft and sends it, which is what makes the agent register).
//
// The desktop resolves placeholders through a pre-flight modal; here we ship the
// English prompts with their default values already substituted so the draft is
// runnable as-is. The `requires` label is informational (the desktop gates cards
// on installed integrations/skills; the demo shows every template so the gallery
// advertises the full surface).
export interface AgentTemplate {
  id: string;
  title: string;
  hook: string;
  icon: LucideIcon;
  /** Featured templates show in the default grid; the rest reveal on "Show more". */
  featured: boolean;
  /** Optional informational chip, e.g. "Requires Google Drive". */
  requires?: string;
  /** Seeded into the chat composer as an editable draft (not auto-sent). */
  prompt: string;
}

export const AGENT_TEMPLATES: AgentTemplate[] = [
  {
    id: 'organize-google-drive',
    title: 'Search and organize my Google Drive',
    hook: "Your Drive's a mess. Let an agent sort it.",
    icon: HardDrive,
    featured: true,
    requires: 'Requires Google Drive',
    prompt: `Spawn an agent that:

1. Reads my Google Drive starting at My Drive (root) and inventories every file with its size, last-modified date, and MIME type.
2. Identifies duplicates by content (same hash, or near-duplicate by filename + size).
3. Reads the first ~2 KB of each file (or the full text for small docs) to infer what it's about.
4. Proposes a folder structure based on content themes, and a list of duplicate-removal candidates.
5. Surfaces the proposal as a markdown report. Do NOT rename or move anything until I confirm specific actions.`,
  },
  {
    id: 'triage-tickets',
    title: "Triage today's tickets",
    hook: 'Skip Monday-morning ticket reading — get the urgent shortlist.',
    icon: ListChecks,
    featured: true,
    requires: 'Needs a project-management integration',
    prompt: `Spawn an agent that:

1. Pulls all tickets created in the last 7 days from the connected project-management tool (Plane / Jira / Asana / etc.) in all projects.
2. For each one, reads the title + description and classifies severity as critical / high / medium / low based on content (impact, urgency, blockers mentioned), NOT labels.
3. Ranks the critical + high tickets by a combination of severity and age.
4. Returns a markdown shortlist with: ticket title, project, your-classified severity, one-line justification, and the original ticket URL.`,
  },
  {
    id: 'synthesize-feedback',
    title: "Synthesize this week's customer feedback",
    hook: '80 feedback items → 5 themes you can act on.',
    icon: MessagesSquare,
    featured: true,
    prompt: `Spawn an agent that:

1. Searches the knowledge base for customer-feedback documents from the last 7 days.
2. Reads each one and extracts the core complaint / suggestion / praise.
3. Clusters the items into 5 themes by topic similarity (NOT keyword matching — read the meaning).
4. For each theme, returns: theme name, item count, 2–3 representative quotes, and a one-sentence "what this might mean" interpretation.
5. Output as markdown ready to paste into a sprint retro.`,
  },
  {
    id: 'quarterly-board-summary',
    title: 'Summarize last quarter for the board',
    hook: 'Project data → a dashboard you\'d be proud to ship.',
    icon: Presentation,
    featured: true,
    requires: 'Needs project management + the dashboard skill',
    prompt: `Spawn an agent that:

1. Pulls data from the connected project-management tool for the last 90 days: projects shipped, tickets closed, notable cycles.
2. Cross-references with knowledge-base documents tagged for the same period (releases, customer wins, incidents).
3. Synthesizes a 4-section narrative for the executive board: shipped / numbers / wins / risks.
4. Calls skill_dashboard_draw to render the numbers section as charts (tickets by priority, ship cadence, close rate trend).
5. Returns the full report as markdown plus the embedded dashboard artifact.`,
  },
  {
    id: 'find-stale-docs',
    title: 'Find stale or duplicate documents',
    hook: 'Knowledge base is bloated. Time to clean house.',
    icon: Search,
    featured: false,
    prompt: `Spawn an agent that:

1. Reads the metadata of every document in the knowledge base.
2. Flags documents older than 12 months that haven't been retrieved in roughly half that period.
3. Identifies near-duplicates by content embedding similarity (>0.95 cosine).
4. Returns a markdown report grouping the candidates as: stale / duplicates / safe-to-keep, with suggested actions for each. No documents are deleted without my confirmation.`,
  },
  {
    id: 'screen-contracts',
    title: 'Screen new uploads for contract clauses',
    hook: 'Find liability + termination + payment terms before legal does.',
    icon: FileSignature,
    featured: false,
    prompt: `Spawn an agent that:

1. Reads contract documents uploaded in the last 7 days.
2. For each, extracts: parties, term length, termination clauses, payment terms, liability caps, indemnification language, governing law.
3. Flags any unusual or aggressive language (auto-renewal, non-standard liability, unilateral termination rights).
4. Returns a markdown summary per contract plus an aggregate risk-flag list.`,
  },
  {
    id: 'match-resumes',
    title: 'Match candidate resumes to open positions',
    hook: 'Score and rank applicants in minutes, not hours.',
    icon: UserCheck,
    featured: false,
    prompt: `Spawn an agent that:

1. Reads every resume uploaded in the last 14 days.
2. For each open job posting (provided in the chat or pulled from a project tagged "hiring"), scores the candidate match on: skill overlap, years of experience, role fidelity, and any unusual signals (career changes, gaps).
3. Ranks candidates per role with a 1–10 score and a one-paragraph justification.
4. Returns markdown with shortlists per role. Does NOT contact candidates — that stays with the user.`,
  },
  {
    id: 'at-risk-accounts',
    title: 'Identify at-risk accounts in the portfolio',
    hook: 'Spot churn signals before the renewal call.',
    icon: AlertTriangle,
    featured: false,
    requires: 'Needs a project-management integration',
    prompt: `Spawn an agent that:

1. Pulls open tickets per customer from the connected project-management tool over the last 30 days.
2. Cross-references with knowledge-base notes tagged as customer-success.
3. Looks for combined signals: SLA breaches + ticket volume spike + sentiment shift in notes.
4. Ranks the top 10 accounts by composite risk score with a 2-sentence "why" each, and concrete next-step suggestions.
5. Returns as markdown plus optional dashboard.`,
  },
  {
    id: 'metric-anomalies',
    title: 'Detect anomalies in operational metrics',
    hook: 'Find pattern breaks beyond the threshold rules.',
    icon: Activity,
    featured: false,
    prompt: `Spawn an agent that:

1. Reads the last 24 hours of operational metrics from the configured RAG source.
2. Detects pattern anomalies (NOT just threshold breaches): a metric holding steady while a correlated one drifts, a series that flatlined, or a trend breaking from its usual baseline.
3. Returns the top 5–10 anomalies with: the metric or source, the pattern observed, a hypothesis, and a recommended next-step query.`,
  },
];

export const FEATURED_TEMPLATE_COUNT = 4;
