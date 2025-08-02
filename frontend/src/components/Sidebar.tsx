import React, { useState } from 'react';
import { ChatSession } from '../types';
import { formatDistanceToNow } from 'date-fns';
import './Sidebar.css';

interface SidebarProps {
  sessions: ChatSession[];
  currentSessionId: string | null;
  onSelectSession: (sessionId: string) => void;
  onNewSession: () => void;
  onDeleteSession: (sessionId: string) => void;
  onRenameSession: (sessionId: string, newName: string) => void;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  sessions,
  currentSessionId,
  onSelectSession,
  onNewSession,
  onDeleteSession,
  onRenameSession,
  isCollapsed,
  onToggleCollapse,
}) => {
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editingName, setEditingName] = useState('');

  const handleRename = (session: ChatSession) => {
    setEditingSessionId(session.id);
    setEditingName(session.name);
  };

  const handleSaveRename = () => {
    if (editingSessionId && editingName.trim()) {
      onRenameSession(editingSessionId, editingName.trim());
    }
    setEditingSessionId(null);
    setEditingName('');
  };

  const handleCancelRename = () => {
    setEditingSessionId(null);
    setEditingName('');
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSaveRename();
    } else if (e.key === 'Escape') {
      handleCancelRename();
    }
  };

  return (
    <div className={`sidebar ${isCollapsed ? 'collapsed' : ''}`}>
      <div className="sidebar-header">
        <button
          className="toggle-button"
          onClick={onToggleCollapse}
          title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {isCollapsed ? '→' : '←'}
        </button>
        {!isCollapsed && (
          <button className="new-chat-button" onClick={onNewSession}>
            + New Chat
          </button>
        )}
      </div>

      {!isCollapsed && (
        <div className="sessions-list">
          {sessions.length === 0 ? (
            <div className="empty-state">
              <p>No chat sessions yet</p>
              <p>Start a new conversation!</p>
            </div>
          ) : (
            sessions.map((session) => (
              <div
                key={session.id}
                className={`session-item ${
                  session.id === currentSessionId ? 'active' : ''
                }`}
                onClick={() => onSelectSession(session.id)}
              >
                {editingSessionId === session.id ? (
                  <input
                    type="text"
                    value={editingName}
                    onChange={(e) => setEditingName(e.target.value)}
                    onBlur={handleSaveRename}
                    onKeyDown={handleKeyPress}
                    className="rename-input"
                    autoFocus
                  />
                ) : (
                  <>
                    <div className="session-content">
                      <div className="session-name">{session.name}</div>
                      <div className="session-meta">
                        <span className="message-count">
                          {session.messages.length} messages
                        </span>
                        <span className="last-updated">
                          {formatDistanceToNow(new Date(session.updatedAt), {
                            addSuffix: true,
                          })}
                        </span>
                      </div>
                    </div>
                    <div className="session-actions">
                      <button
                        className="action-button"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleRename(session);
                        }}
                        title="Rename session"
                      >
                        ✏️
                      </button>
                      <button
                        className="action-button delete"
                        onClick={(e) => {
                          e.stopPropagation();
                          if (
                            window.confirm(
                              `Are you sure you want to delete "${session.name}"?`
                            )
                          ) {
                            onDeleteSession(session.id);
                          }
                        }}
                        title="Delete session"
                      >
                        🗑️
                      </button>
                    </div>
                  </>
                )}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};