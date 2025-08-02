import React, { useState, useEffect, useRef } from 'react';
import { ChatSession, ChatMessage, StreamChunk, ToolCall } from './types';
import { storage } from './utils/storage';
import { useChat } from './hooks/useChat';
import { Sidebar } from './components/Sidebar';
import { ChatMessage as ChatMessageComponent } from './components/ChatMessage';
import { ToolCallDisplay } from './components/ToolCallDisplay';
import './App.css';

function App() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [input, setInput] = useState('');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState<ChatMessage | null>(null);
  const [currentToolCalls, setCurrentToolCalls] = useState<ToolCall[]>([]);
  const [executingTools, setExecutingTools] = useState<Set<string>>(new Set());

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { sendMessage, stopGeneration, isLoading, error } = useChat();

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
    setCurrentSessionId(sessionId);
    storage.setCurrentSessionId(sessionId);
    // Clear any streaming state when switching sessions
    setStreamingMessage(null);
    setCurrentToolCalls([]);
    setExecutingTools(new Set());
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

  const handleSendMessage = async () => {
    if (!input.trim() || isLoading) return;

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
      content: input.trim(),
      timestamp: new Date().toISOString(),
    };

    // Add user message to storage
    storage.addMessage(sessionId, userMessage);
    
    // Update local state
    setSessions(prev => prev.map(s => 
      s.id === sessionId 
        ? { ...s, messages: [...s.messages, userMessage] }
        : s
    ));

    setInput('');
    setCurrentToolCalls([]);
    setExecutingTools(new Set());

    // Prepare assistant message
    const assistantMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
    };

    setStreamingMessage(assistantMessage);

    // Get all messages for context
    const session = storage.getSession(sessionId);
    if (!session) return;

    const allMessages = [...session.messages, userMessage];

    try {
      await sendMessage(allMessages, sessionId, (chunk: StreamChunk) => {
        switch (chunk.type) {
          case 'content':
            setStreamingMessage(prev => prev ? {
              ...prev,
              content: prev.content + (chunk.content || '')
            } : null);
            break;

          case 'tool_call':
            if (chunk.tool && chunk.parameters) {
              const newToolCall: ToolCall = {
                tool: chunk.tool,
                parameters: chunk.parameters,
              };
              setCurrentToolCalls(prev => [...prev, newToolCall]);
              setExecutingTools(prev => new Set([...prev, chunk.tool!]));
            }
            break;

          case 'tool_result':
            if (chunk.tool && chunk.result) {
              setCurrentToolCalls(prev => 
                prev.map(tc => 
                  tc.tool === chunk.tool && !tc.result && !tc.error
                    ? { ...tc, result: chunk.result }
                    : tc
                )
              );
              setExecutingTools(prev => {
                const newSet = new Set(prev);
                newSet.delete(chunk.tool!);
                return newSet;
              });
            }
            break;

          case 'tool_error':
            if (chunk.tool && chunk.error) {
              setCurrentToolCalls(prev => 
                prev.map(tc => 
                  tc.tool === chunk.tool && !tc.result && !tc.error
                    ? { ...tc, error: chunk.error }
                    : tc
                )
              );
              setExecutingTools(prev => {
                const newSet = new Set(prev);
                newSet.delete(chunk.tool!);
                return newSet;
              });
            }
            break;

          case 'error':
            console.error('Stream error:', chunk.error);
            break;
        }
      });

      // Finalize the assistant message
      if (streamingMessage) {
        const finalMessage = { ...streamingMessage };
        storage.addMessage(sessionId, finalMessage);
        setSessions(prev => prev.map(s => 
          s.id === sessionId 
            ? { ...s, messages: [...s.messages, finalMessage] }
            : s
        ));
      }

    } catch (error) {
      console.error('Error sending message:', error);
    } finally {
      setStreamingMessage(null);
      setCurrentToolCalls([]);
      setExecutingTools(new Set());
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
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
          <h1>Chat Agent</h1>
          {currentSession && (
            <div className="session-info">
              <span className="session-name">{currentSession.name}</span>
              <span className="message-count">
                {currentSession.messages.length} messages
              </span>
            </div>
          )}
        </div>

        <div className="messages-container">
          {!currentSession ? (
            <div className="welcome-screen">
              <h2>Welcome to Chat Agent</h2>
              <p>Start a new conversation to begin chatting with the AI agent.</p>
              <button className="start-chat-button" onClick={handleNewSession}>
                Start New Chat
              </button>
            </div>
          ) : (
            <>
              {currentSession.messages.map((message) => (
                <ChatMessageComponent key={message.id} message={message} />
              ))}

              {currentToolCalls.map((toolCall, index) => (
                <ToolCallDisplay
                  key={`${toolCall.tool}-${index}`}
                  toolCall={toolCall}
                  isExecuting={executingTools.has(toolCall.tool)}
                />
              ))}

              {streamingMessage && (
                <ChatMessageComponent 
                  message={streamingMessage} 
                  isStreaming={true}
                />
              )}

              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {error && (
          <div className="error-banner">
            <span>⚠️ {error}</span>
          </div>
        )}

        <div className="input-container">
          <div className="input-wrapper">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={currentSession ? "Type your message..." : "Start a new chat to begin"}
              className="message-input"
              rows={1}
              disabled={!currentSession}
            />
            <button
              onClick={isLoading ? stopGeneration : handleSendMessage}
              disabled={(!input.trim() && !isLoading) || !currentSession}
              className={`send-button ${isLoading ? 'stop' : 'send'}`}
            >
              {isLoading ? '⏹️' : '📤'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;