import { Bot, BookOpen, Briefcase, Compass, FolderOpen, LayoutDashboard, Rocket, Sparkles, Zap, type LucideIcon } from 'lucide-react';
import type { ProjectView } from './useProjects';

// Project visual identity shared by the Projects page and the project dashboard,
// matching the desktop: an icon badge derived from the project's stored icon
// name and a deterministic, asset-free banner tint per project name.

// Icon names stored on the project (e.g. "Briefcase") → lucide glyphs. Unknown
// names fall back to the generic project / My-Space icon.
const PROJECT_ICONS: Record<string, LucideIcon> = {
  Sparkles,
  FolderOpen,
  Briefcase,
  Compass,
  Rocket,
  Zap,
  Bot,
  BookOpen,
  LayoutDashboard,
};

export function projectIcon(project: ProjectView): LucideIcon {
  if (project.icon && PROJECT_ICONS[project.icon]) return PROJECT_ICONS[project.icon];
  return project.isDefault ? Sparkles : FolderOpen;
}

// Curated, muted, cool-leaning tones that harmonize with the Arbi teal + slate
// palette. Ported from the desktop projectGradient.
const PROJECT_BANNER_TONES: Array<[number, number, number]> = [
  [172, 32, 44],
  [186, 28, 45],
  [200, 26, 47],
  [212, 24, 50],
  [224, 20, 50],
  [160, 26, 43],
  [215, 14, 46],
];

export function projectGradient(name: string): string {
  let hash = 0;
  for (let i = 0; i < name.length; i++) hash = (hash * 31 + name.charCodeAt(i)) >>> 0;
  const [h, s, l] = PROJECT_BANNER_TONES[hash % PROJECT_BANNER_TONES.length];
  return `linear-gradient(180deg, hsl(${h} ${s}% ${l + 6}% / 0.55), hsl(${h} ${s}% ${l - 8}% / 0.5))`;
}
