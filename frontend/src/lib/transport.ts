import type { 
  ChatModelAdapter, 
  ChatModelRunOptions, 
  ChatModelRunResult,
  ThreadMessage,
  ThreadAssistantContentPart 
} from "@assistant-ui/react";

// Convert assistant-ui message format to our backend format
const convertToBackendMessage = (message: ThreadMessage) => ({
  role: message.role,
  content: message.role === 'user' 
    ? Array.isArray(message.content)
      ? message.content.map(part => 
          part.type === 'text' ? part.text : ''
        ).join('')
      : ''
    : message.role === 'assistant'
    ? Array.isArray(message.content)
      ? message.content.map(part => 
          part.type === 'text' ? part.text : ''
        ).join('')
      : ''
    : '',
  timestamp: new Date().toISOString(),
});

// Custom chat model adapter for our backend
export class ChatAgentAdapter implements ChatModelAdapter {
  private baseUrl: string;

  constructor(baseUrl = process.env.NODE_ENV === 'production' 
    ? window.location.origin 
    : 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }

  async run(options: ChatModelRunOptions): Promise<ChatModelRunResult> {
    const { messages, abortSignal } = options;
    const backendMessages = messages.map(convertToBackendMessage);
    
    try {
      const response = await fetch(`${this.baseUrl}/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages: backendMessages,
          session_id: 'default', // You can make this dynamic
        }),
        signal: abortSignal,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      if (!response.body) {
        throw new Error('No response body');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let fullContent = '';

      try {
        while (true) {
          const { done, value } = await reader.read();
          
          if (done) break;
          
          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split('\n');
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6);
              if (data === '[DONE]') {
                break;
              }
              
              try {
                const parsed = JSON.parse(data);
                if (parsed.content) {
                  fullContent += parsed.content;
                }
              } catch (e) {
                // Ignore parsing errors for partial chunks
              }
            }
          }
        }
      } finally {
        reader.releaseLock();
      }

      // Return the expected ChatModelRunResult format
      const content: ThreadAssistantContentPart[] = [{
        type: 'text',
        text: fullContent
      }];

      return {
        content,
        status: { type: 'complete', reason: 'stop' }
      };
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        throw error;
      }
      throw new Error(`Chat request failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }
}

// Create a singleton instance
export const chatAgentAdapter = new ChatAgentAdapter();