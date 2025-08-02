import React, { useState, useEffect, useRef } from 'react';
import { ChatSession } from './types';
import { ChatMessage, streamChatResponse } from './lib/transport';
import { storage } from './utils/storage';
import { Sidebar } from './components/Sidebar';
import { cn } from './lib/utils';
import { Send, StopCircle } from 'lucide-react';
import './App.css';

// Simple message component
const MessageBubble: React.FC<{ message: ChatMessage; isStreaming?: boolean }> = ({ 
  message, 
  isStreaming 
}) => {
  return (
    <div className={cn(
      "flex w-full",
      message.role === 'user' ? 'justify-end' : 'justify-start'
    )}>
      <div className={cn(
        "max-w-[80%] rounded-lg px-4 py-2 mb-4",
        message.role === 'user' 
          ? 'bg-blue-600 text-white ml-12' 
          : 'bg-gray-100 text-gray-900 mr-12'
      )}>
        <div className="prose prose-sm max-w-none dark:prose-invert">
          {message.content}
          {isStreaming && <span className="animate-pulse">|</span>}
        </div>
      </div>
    </div>
  );
};

// Simple composer component
const MessageComposer: React.FC<{
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
}> = ({ onSend, disabled, placeholder = "Type your message..." }) => {
  const [input, setInput] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !disabled) {
      onSend(input.trim());
      setInput('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <textarea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled}
        className="flex-1 min-h-[60px] max-h-[200px] resize-none border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
        rows={2}
      />
      <button
        type="submit"
        disabled={!input.trim() || disabled}
        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
      >
        <Send size={16} />
        Send
      </button>
    </form>
  );
};

function App() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState<ChatMessage | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Load sessions from localStorage on mount
  useEffect(() => {
    const savedSessions = storage.getSessions();
    setSessions(savedSessions);
    
    const savedCurrentSession = storage.getCurrentSessionId();
    if (savedCurrentSession && savedSessions.find(s => s.id === savedCurrentSession)) {
      setCurrentSessionId(savedCurrentSession);
    }
  }, []);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [currentSession?.messages, streamingMessage]);

  const currentSession = sessions.find(s => s.id === currentSessionId);

  const handleNewSession = () => {
    const session = storage.createSession(`Chat ${sessions.length + 1}`);
    setSessions([session, ...sessions]);
    setCurrentSessionId(session.id);
    storage.setCurrentSessionId(session.id);
  };

  const handleSelectSession = (sessionId: string) => {
    // Cancel any ongoing requests when switching sessions
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setCurrentSessionId(sessionId);
    storage.setCurrentSessionId(sessionId);
    setStreamingMessage(null);
    setIsLoading(false);
  };

  const handleDeleteSession = (sessionId: string) => {
    storage.deleteSession(sessionId);
    const updatedSessions = sessions.filter(s => s.id !== sessionId);
    setSessions(updatedSessions);
    
    if (currentSessionId === sessionId) {
      const nextSession = updatedSessions[0];
      if (nextSession) {
        setCurrentSessionId(nextSession.id);
        storage.setCurrentSessionId(nextSession.id);
      } else {
        setCurrentSessionId(null);
        storage.setCurrentSessionId(null);
      }
    }
  };

  const handleRenameSession = (sessionId: string, newName: string) => {
    storage.updateSession(sessionId, { name: newName });
    setSessions(sessions.map(s => 
      s.id === sessionId ? { ...s, name: newName } : s
    ));
  };

  const handleSendMessage = async (content: string) => {
    if (isLoading) return;

    // Create session if none exists
    let sessionId = currentSessionId;
    if (!sessionId) {
      const newSession = storage.createSession('New Chat');
      setSessions([newSession, ...sessions]);
      setCurrentSessionId(newSession.id);
      storage.setCurrentSessionId(newSession.id);
      sessionId = newSession.id;
    }

    // Create user message
    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    };

    // Add user message to storage and state
    storage.addMessage(sessionId, userMessage);
    setSessions(prev => prev.map(s => 
      s.id === sessionId 
        ? { ...s, messages: [...s.messages, userMessage] }
        : s
    ));

    // Prepare streaming assistant message
    const assistantMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
    };

    setStreamingMessage(assistantMessage);
    setIsLoading(true);

    // Cancel any existing request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    try {
      // Get all messages for context
      const session = storage.getSession(sessionId);
      if (!session) return;

      const allMessages = [...session.messages, userMessage];

      // Convert to the format expected by streamChatResponse
      const coreMessages = allMessages.map(msg => ({
        role: msg.role as 'user' | 'assistant' | 'system',
        content: msg.content,
      }));

      await streamChatResponse(
        coreMessages,
        (content) => {
          setStreamingMessage(prev => prev ? { ...prev, content } : null);
        },
        abortControllerRef.current.signal
      );

      // Finalize the assistant message
      if (streamingMessage) {
        const finalMessage = { ...assistantMessage, content: streamingMessage.content };
        storage.addMessage(sessionId, finalMessage);
        setSessions(prev => prev.map(s => 
          s.id === sessionId 
            ? { ...s, messages: [...s.messages, finalMessage] }
            : s
        ));
      }

    } catch (error: any) {
      if (error.name !== 'AbortError') {
        console.error('Error sending message:', error);
      }
    } finally {
      setStreamingMessage(null);
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  };

  const handleStopGeneration = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsLoading(false);
      setStreamingMessage(null);
    }
  };

  return (
    <div className="app">
      <Sidebar
        sessions={sessions}
        currentSessionId={currentSessionId}
        onSelectSession={handleSelectSession}
        onNewSession={handleNewSession}
        onDeleteSession={handleDeleteSession}
        onRenameSession={handleRenameSession}
        isCollapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
      />

      <div className="main-content">
        <div className="chat-header">
          <h1 className="text-2xl font-bold">Chat Agent</h1>
          {currentSession && (
            <div className="flex items-center gap-4">
              <span className="text-lg font-medium">{currentSession.name}</span>
                               <span className="text-sm text-gray-600">
                   {currentSession.messages.length} messages
                 </span>
            </div>
          )}
        </div>

        <div className="flex-1 flex flex-col">
          {!currentSession ? (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center space-y-4">
                <h2 className="text-3xl font-bold">Welcome to Chat Agent</h2>
                <p className="text-gray-600">
                  Start a new conversation to begin chatting with the AI agent.
                </p>
                <button 
                  className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  onClick={handleNewSession}
                >
                  Start New Chat
                </button>
              </div>
            </div>
          ) : (
            <>
              <div className="flex-1 overflow-y-auto p-4">
                                 {currentSession.messages.length === 0 && (
                   <div className="text-center text-gray-600 py-8">
                     <p>Hello! I'm your AI assistant. How can I help you today?</p>
                   </div>
                 )}
                
                {currentSession.messages.map((message) => (
                  <MessageBubble key={message.id} message={message} />
                ))}

                {streamingMessage && (
                  <MessageBubble message={streamingMessage} isStreaming={true} />
                )}

                <div ref={messagesEndRef} />
              </div>
              
              <div className="border-t p-4">
                <MessageComposer
                  onSend={handleSendMessage}
                  disabled={isLoading}
                  placeholder={isLoading ? "AI is thinking..." : "Type your message..."}
                />
                
                {isLoading && (
                  <div className="flex justify-center mt-2">
                                         <button
                       onClick={handleStopGeneration}
                       className="px-3 py-1 text-sm bg-red-500 text-white rounded hover:bg-red-600 transition-colors flex items-center gap-1"
                     >
                       <StopCircle size={14} />
                       Stop Generation
                     </button>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;