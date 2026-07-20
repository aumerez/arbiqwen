import {
  Bot,
  Boxes,
  Calendar,
  Cloud,
  CloudSun,
  Cog,
  Database,
  FileSpreadsheet,
  FileText,
  Globe,
  Link,
  Mail,
  MessageSquare,
  Plug,
  Puzzle,
  Server,
  ShieldCheck,
  Table,
  Webhook,
  Zap,
  type LucideIcon,
} from 'lucide-react';

// Curated driver-icon map for the read-only Integrations list. The desktop
// resolves any lucide icon by name from the full namespace; importing all of
// lucide would bloat the demo bundle, so we map the icon names the seeded
// drivers actually use and fall back to Puzzle (the desktop's fallback) for
// anything unknown. Add entries here as new drivers appear.
const INTEGRATION_ICONS: Record<string, LucideIcon> = {
  Bot,
  Boxes,
  Calendar,
  Cloud,
  CloudSun,
  Cog,
  Database,
  FileSpreadsheet,
  FileText,
  Globe,
  Link,
  Mail,
  MessageSquare,
  Plug,
  Server,
  ShieldCheck,
  Slack: MessageSquare,
  Table,
  Webhook,
  Zap,
};

export function integrationIcon(iconName?: string): LucideIcon {
  return INTEGRATION_ICONS[iconName ?? ''] ?? Puzzle;
}
