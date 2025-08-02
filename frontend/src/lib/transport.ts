// Simple message interface for our chat
export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

// Convert messages to backend format
const convertToBackendMessage = (message: ChatMessage) => ({
  role: message.role,
  content: message.content,
  timestamp: new Date().toISOString(),
});

// Simple fetch function for streaming chat responses
export const streamChatResponse = async (
  messages: ChatMessage[],
  onUpdate: (content: string) => void,
  signal?: AbortSignal
) => {
  const baseUrl = process.env.NODE_ENV === 'production' 
    ? window.location.origin 
    : 'http://localhost:8000';

  try {
    const response = await fetch(`${baseUrl}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        messages: messages.map(convertToBackendMessage),
        session_id: crypto.randomUUID(),
      }),
      signal,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('No response body');
    }

    const decoder = new TextDecoder();
    let accumulatedContent = '';

    while (true) {
      const { done, value } = await reader.read();
      
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          
          if (data === '[DONE]') {
            return accumulatedContent;
          }

          try {
            const parsedChunk = JSON.parse(data);
            
            if (parsedChunk.type === 'content' && parsedChunk.content) {
              accumulatedContent += parsedChunk.content;
              onUpdate(accumulatedContent);
            }
          } catch (e) {
            console.warn('Failed to parse chunk:', data);
          }
        }
      }
    }

    return accumulatedContent;
  } catch (error: any) {
    if (error.name !== 'AbortError') {
      throw error;
    }
    return '';
  }
};