import { ChatSession, ChatMessage } from '../types';

const SESSIONS_KEY = 'chat-sessions';
const CURRENT_SESSION_KEY = 'current-session-id';

export const storage = {
  // Get all sessions
  getSessions(): ChatSession[] {
    try {
      const data = localStorage.getItem(SESSIONS_KEY);
      return data ? JSON.parse(data) : [];
    } catch (error) {
      console.error('Error loading sessions:', error);
      return [];
    }
  },

  // Save all sessions
  saveSessions(sessions: ChatSession[]): void {
    try {
      localStorage.setItem(SESSIONS_KEY, JSON.stringify(sessions));
    } catch (error) {
      console.error('Error saving sessions:', error);
    }
  },

  // Get specific session
  getSession(id: string): ChatSession | undefined {
    const sessions = this.getSessions();
    return sessions.find(session => session.id === id);
  },

  // Create new session
  createSession(name: string): ChatSession {
    const session: ChatSession = {
      id: crypto.randomUUID(),
      name,
      messages: [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    const sessions = this.getSessions();
    sessions.unshift(session); // Add to beginning
    this.saveSessions(sessions);

    return session;
  },

  // Update session
  updateSession(id: string, updates: Partial<ChatSession>): void {
    const sessions = this.getSessions();
    const index = sessions.findIndex(session => session.id === id);
    
    if (index !== -1) {
      sessions[index] = {
        ...sessions[index],
        ...updates,
        updatedAt: new Date().toISOString(),
      };
      this.saveSessions(sessions);
    }
  },

  // Add message to session
  addMessage(sessionId: string, message: ChatMessage): void {
    const sessions = this.getSessions();
    const session = sessions.find(s => s.id === sessionId);
    
    if (session) {
      session.messages.push(message);
      session.updatedAt = new Date().toISOString();
      this.saveSessions(sessions);
    }
  },

  // Delete session
  deleteSession(id: string): void {
    const sessions = this.getSessions();
    const filteredSessions = sessions.filter(session => session.id !== id);
    this.saveSessions(filteredSessions);

    // Clear current session if it was deleted
    if (this.getCurrentSessionId() === id) {
      this.setCurrentSessionId(null);
    }
  },

  // Current session management
  getCurrentSessionId(): string | null {
    return localStorage.getItem(CURRENT_SESSION_KEY);
  },

  setCurrentSessionId(id: string | null): void {
    if (id) {
      localStorage.setItem(CURRENT_SESSION_KEY, id);
    } else {
      localStorage.removeItem(CURRENT_SESSION_KEY);
    }
  },

  // Clear all data
  clearAll(): void {
    localStorage.removeItem(SESSIONS_KEY);
    localStorage.removeItem(CURRENT_SESSION_KEY);
  },

  // Export sessions for backup
  exportSessions(): string {
    const sessions = this.getSessions();
    return JSON.stringify(sessions, null, 2);
  },

  // Import sessions from backup
  importSessions(data: string): boolean {
    try {
      const sessions = JSON.parse(data);
      if (Array.isArray(sessions)) {
        this.saveSessions(sessions);
        return true;
      }
      return false;
    } catch (error) {
      console.error('Error importing sessions:', error);
      return false;
    }
  },
};