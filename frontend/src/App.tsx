import React, { useState, useEffect } from 'react';
import { AssistantRuntimeProvider, useLocalRuntime, Thread, Composer } from '@assistant-ui/react';
import { chatAgentAdapter } from './lib/transport';
import { ChatSession } from './types';
import { storage } from './utils/storage';
import { Sidebar } from './components/Sidebar';
import { cn } from './lib/utils';
import '@assistant-ui/react/styles/index.css';
import './App.css';

function ChatInterface({ runtime }: { runtime: ReturnType<typeof useLocalRuntime> }) {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(true);

  // Load sessions from storage
  useEffect(() => {
    try {
      const loadedSessions = storage.getSessions();
      setSessions(loadedSessions);
      
      if (loadedSessions.length > 0 && !currentSessionId) {
        setCurrentSessionId(loadedSessions[0].id);
      }
    } catch (error) {
      console.error('Failed to load sessions:', error);
      setSessions([]);
    }
  }, [currentSessionId]);

  // Save sessions to storage whenever they change
  useEffect(() => {
    try {
      storage.saveSessions(sessions);
    } catch (error) {
      console.error('Failed to save sessions:', error);
    }
  }, [sessions]);

  const handleNewSession = () => {
    const newSession: ChatSession = {
      id: crypto.randomUUID(),
      name: 'Nova Conversa',
      messages: [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    setSessions(prev => [newSession, ...prev]);
    setCurrentSessionId(newSession.id);
    
    // Note: assistant-ui runtime doesn't have switchToNewThread method
    // The Thread component will automatically handle new conversations
  };

  const handleDeleteSession = (sessionId: string) => {
    setSessions(prev => prev.filter(s => s.id !== sessionId));
    
    if (currentSessionId === sessionId) {
      const remainingSessions = sessions.filter(s => s.id !== sessionId);
      if (remainingSessions.length > 0) {
        setCurrentSessionId(remainingSessions[0].id);
      } else {
        setCurrentSessionId(null);
      }
    }
  };

  const handleSessionSelect = (sessionId: string) => {
    setCurrentSessionId(sessionId);
    // Note: In a full implementation, you'd want to restore the conversation history
    // This would require additional assistant-ui API calls
  };

  const handleRenameSession = (sessionId: string, newName: string) => {
    setSessions(prev => prev.map(session => 
      session.id === sessionId 
        ? { ...session, name: newName, updatedAt: new Date().toISOString() }
        : session
    ));
  };

  const handleToggleCollapse = () => {
    setSidebarCollapsed(prev => !prev);
  };

  const currentSession = sessions.find(s => s.id === currentSessionId);

  return (
    <div className={cn("h-screen flex bg-white text-gray-900")}>
      {/* Sidebar */}
      <div className={cn(
        "transition-all duration-300 overflow-hidden",
        sidebarCollapsed ? "w-0" : "w-80"
      )}>
        <Sidebar
          sessions={sessions}
          currentSessionId={currentSessionId}
          onNewSession={handleNewSession}
          onSelectSession={handleSessionSelect}
          onDeleteSession={handleDeleteSession}
          onRenameSession={handleRenameSession}
          isCollapsed={sidebarCollapsed}
          onToggleCollapse={handleToggleCollapse}
        />
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <div className="border-b border-gray-200 p-4 bg-white flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              aria-label="Toggle menu"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <h1 className="text-xl font-semibold">
              {currentSession?.name || 'Agent de Softcatalà'}
            </h1>
          </div>
          {currentSession && (
            <span className="text-sm text-gray-600">
              {currentSession.messages?.length || 0} missatges
            </span>
          )}
        </div>

        {/* Chat Area */}
        <div className="flex-1 flex flex-col min-h-0">
          {currentSession ? (
            <>
              {/* Thread Component from assistant-ui */}
              <div className="flex-1 overflow-hidden h-full">
                <Thread />
              </div>

              {/* Composer Component from assistant-ui */}
              <div className="border-t border-gray-200 p-4 bg-white">
                <Composer />
              </div>
            </>
          ) : (
            /* Empty State */
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <div className="w-16 h-16 mx-auto mb-4 bg-blue-100 rounded-full flex items-center justify-center">
                  <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                  </svg>
                </div>
                <h2 className="text-2xl font-semibold text-gray-900 mb-2">Benvingut a l'Agent de Softcatalà</h2>
                <p className="text-gray-600 mb-6">
                  Inicia una nova conversa per començar a parlar amb l'Agent de Softcatalà.
                </p>
                <button 
                  className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  onClick={handleNewSession}
                >
                  Iniciar Nova Conversa
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function App() {
  // Create the assistant runtime with our custom adapter
  const runtime = useLocalRuntime(chatAgentAdapter);
  
  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <ChatInterface runtime={runtime} />
    </AssistantRuntimeProvider>
  );
}

export default App;