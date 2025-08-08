import { useState, useCallback, useRef } from 'react';
import { ChatMessage, StreamChunk } from '../types';

const API_BASE = process.env.NODE_ENV === 'production' 
  ? (process.env.REACT_APP_BACKEND_URL || 'https://agent-softcatala.onrender.com')
  : 'http://localhost:8000';

export const useChat = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(async (
    messages: ChatMessage[],
    sessionId: string,
    onChunk: (chunk: StreamChunk) => void
  ) => {
    setIsLoading(true);
    setError(null);

    // Cancel any existing request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    abortControllerRef.current = new AbortController();

    try {
      const response = await fetch(`${API_BASE}/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages: messages.map(msg => ({
            role: msg.role,
            content: msg.content,
            timestamp: msg.timestamp,
          })),
          session_id: sessionId,
        }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body');
      }

      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            
            if (data === '[DONE]') {
              setIsLoading(false);
              return;
            }

            try {
              const parsedChunk: StreamChunk = JSON.parse(data);
              onChunk(parsedChunk);
            } catch (e) {
              console.warn('Failed to parse chunk:', data);
            }
          }
        }
      }
    } catch (error: any) {
      if (error.name === 'AbortError') {
        console.log('Request aborted');
      } else {
        console.error('Chat error:', error);
        setError(error.message || 'An error occurred while sending the message');
      }
    } finally {
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  }, []);

  const stopGeneration = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsLoading(false);
    }
  }, []);

  const checkHealth = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/health`);
      return response.ok;
    } catch {
      return false;
    }
  }, []);

  const getModels = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/models`);
      if (response.ok) {
        const data = await response.json();
        return data.models || [];
      }
      return [];
    } catch {
      return [];
    }
  }, []);

  return {
    sendMessage,
    stopGeneration,
    checkHealth,
    getModels,
    isLoading,
    error,
  };
};
