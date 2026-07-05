import type { LucideIcon } from 'lucide-react';
import { ChevronLeft, FolderOpen, MessageCircle, Plus, Sparkles } from 'lucide-react';
import type { ProjectView } from '../projects/useProjects';
import type { ChatSummary } from '../chat/types';

export interface NavItem {
  id: string;
  label: string;
  icon: LucideIcon;
}

interface SidebarProps {
  workspaceName: string;
  projects: ProjectView[];
  currentProject: ProjectView | null;
  onGoToMySpace: () => void;
  onOpenProject: () => void;
  chats: ChatSummary[];
  currentChatId: number | null;
  onSelectChat: (id: number) => void;
  onNewChat: () => void;
  items: NavItem[];
  activeId: string;
  onNavigate: (id: string) => void;
}

// Mono-chrome sidebar mirroring the desktop layout: workspace header, active
// project (with a "My Space" back link when a non-default project is open),
// the conversation list with a new-conversation control, and bottom navigation.
export function Sidebar({
  workspaceName,
  currentProject,
  onGoToMySpace,
  onOpenProject,
  chats,
  currentChatId,
  onSelectChat,
  onNewChat,
  items,
  activeId,
  onNavigate,
}: SidebarProps) {
  const ProjectIcon = currentProject?.isDefault ? Sparkles : FolderOpen;
  const showBack = currentProject != null && !currentProject.isDefault;

  return (
    <aside className="sidebar">
      <div className="sidebar__header">{workspaceName}</div>

      <div className="sidebar__project-section">
        {showBack && (
          <button type="button" className="sidebar__back" onClick={onGoToMySpace}>
            <ChevronLeft size={14} strokeWidth={2} />
            My Space
          </button>
        )}
        <button
          type="button"
          className="sidebar__project sidebar__project--active"
          onClick={onOpenProject}
          aria-current="page"
        >
          <ProjectIcon size={18} strokeWidth={1.5} className="sidebar__project-icon" />
          <span className="sidebar__project-name">{currentProject?.name ?? 'My Space'}</span>
        </button>
      </div>

      <div className="sidebar__sep" />

      <div className="sidebar__convos">
        <div className="sidebar__label">Conversations</div>
        <button type="button" className="sidebar__new" onClick={onNewChat}>
          <Plus size={14} strokeWidth={2} />
          New conversation
        </button>
        <div className="sidebar__convo-list">
          {chats.length === 0 ? (
            <div className="sidebar__convo-empty">
              <MessageCircle size={18} strokeWidth={1.5} />
              <span>No conversations yet</span>
            </div>
          ) : (
            chats.map((chat) => (
              <button
                key={chat.id}
                type="button"
                className={`sidebar__convo${chat.id === currentChatId ? ' sidebar__convo--active' : ''}`}
                aria-current={chat.id === currentChatId ? 'true' : undefined}
                onClick={() => onSelectChat(chat.id)}
              >
                {chat.title || 'Untitled conversation'}
              </button>
            ))
          )}
        </div>
      </div>

      <div className="sidebar__spacer" />

      <nav className="sidebar__nav" aria-label="Sections">
        {items.map((item) => {
          const Icon = item.icon;
          const active = item.id === activeId;
          return (
            <button
              key={item.id}
              type="button"
              className={`sidebar__link${active ? ' sidebar__link--active' : ''}`}
              aria-current={active ? 'page' : undefined}
              onClick={() => onNavigate(item.id)}
            >
              <Icon size={16} strokeWidth={1.5} className="sidebar__link-icon" />
              {item.label}
            </button>
          );
        })}
      </nav>

      <div className="sidebar__foot">Demo</div>
    </aside>
  );
}
