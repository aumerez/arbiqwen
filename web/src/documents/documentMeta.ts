import { File, FileImage, FileJson, FileSpreadsheet, FileText, type LucideIcon } from 'lucide-react';

// Document presentation helpers, ported from the desktop DocumentContext +
// fileIcon. Pure formatting — no I/O. Shared by the Documents page rows.

export interface DocumentRow {
  id: number | string;
  filename?: string;
  mimetype?: string;
  size?: number;
  status?: string;
  index_mode?: string | null;
  project_id?: number | null;
  project_name?: string | null;
  created_at?: string;
}

// Map a MIME type to a lucide icon. Coarse buckets matching the desktop
// FileTypeIcon (spreadsheets, images, json, everything-else as a document).
export function fileIcon(mimetype?: string): LucideIcon {
  const m = (mimetype ?? '').toLowerCase();
  if (m.startsWith('image/')) return FileImage;
  if (m.includes('json')) return FileJson;
  if (m.includes('csv') || m.includes('spreadsheet') || m.includes('excel') || m.includes('ms-excel')) {
    return FileSpreadsheet;
  }
  if (m.includes('pdf') || m.includes('word') || m.includes('text') || m.includes('document') || m.includes('markdown')) {
    return FileText;
  }
  return File;
}

// "0 B" / "1.5 MB" / "2.3 GB" — base-1024, one decimal above KB.
export function formatFileSize(bytes?: number): string {
  if (bytes == null || Number.isNaN(bytes)) return '';
  if (bytes === 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  const value = bytes / Math.pow(1024, i);
  return `${i === 0 ? value : value.toFixed(1)} ${units[i]}`;
}

// Relative for recent ("just now", "5m ago", "3h ago", "2d ago"), short date
// otherwise ("Jan 15"). Mirrors the desktop formatDate.
export function formatDate(dateStr?: string): string {
  if (!dateStr) return '';
  const then = new Date(dateStr).getTime();
  if (Number.isNaN(then)) return '';
  const diff = Date.now() - then;
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d ago`;
  return new Date(then).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

// Status pill class suffix + label. Index-mode badge handled separately.
export function statusBadge(status?: string): { cls: string; label: string } {
  switch (status) {
    case 'indexed':
      return { cls: 'badge--on', label: 'Indexed' };
    case 'processing':
      return { cls: 'badge--info', label: 'Processing' };
    case 'error':
      return { cls: 'badge--error', label: 'Error' };
    case 'queued':
    default:
      return { cls: 'badge--off', label: status ? status[0].toUpperCase() + status.slice(1) : 'Queued' };
  }
}

// Index-mode badge: 'full' is the default and shows nothing; 'stub' (tabular)
// and 'none' (external dataset) get an informational badge.
export function indexModeBadge(mode?: string | null): { cls: string; label: string } | null {
  if (mode === 'stub') return { cls: 'badge--info', label: 'Queryable' };
  if (mode === 'none') return { cls: 'badge--read', label: 'Connected' };
  return null;
}
