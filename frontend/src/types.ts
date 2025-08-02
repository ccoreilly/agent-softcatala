export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  id: string;
}

export interface ChatSession {
  id: string;
  name: string;
  messages: ChatMessage[];
  createdAt: string;
  updatedAt: string;
}

export interface ToolCall {
  tool: string;
  parameters: Record<string, any>;
  result?: any;
  error?: string;
}

export interface StreamChunk {
  type: 'content' | 'tool_call' | 'tool_result' | 'tool_error' | 'error';
  content?: string;
  tool?: string;
  parameters?: Record<string, any>;
  result?: any;
  error?: string;
  timestamp: string;
}

export interface ApiConfig {
  backendUrl: string;
}