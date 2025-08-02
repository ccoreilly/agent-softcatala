import React from 'react';
import { marked } from 'marked';
import { ChatMessage as ChatMessageType } from '../types';
import { formatDistanceToNow } from 'date-fns';
import './ChatMessage.css';

interface ChatMessageProps {
  message: ChatMessageType;
  isStreaming?: boolean;
}

// Configure marked for better security
marked.setOptions({
  breaks: true,
  gfm: true,
});

export const ChatMessage: React.FC<ChatMessageProps> = ({ 
  message, 
  isStreaming = false 
}) => {
  const renderContent = () => {
    if (message.role === 'user') {
      return <div className="message-text">{message.content}</div>;
    }

    // For assistant messages, render as markdown
    const htmlContent = marked.parse(message.content, { async: false }) as string;
    
    return (
      <div 
        className="message-text markdown"
        dangerouslySetInnerHTML={{ __html: htmlContent }}
      />
    );
  };

  return (
    <div className={`chat-message ${message.role} ${isStreaming ? 'streaming' : ''}`}>
      <div className="message-avatar">
        {message.role === 'user' ? '👤' : '🤖'}
      </div>
      <div className="message-content">
        <div className="message-header">
          <span className="message-role">
            {message.role === 'user' ? 'You' : 'Assistant'}
          </span>
          <span className="message-timestamp">
            {formatDistanceToNow(new Date(message.timestamp), { addSuffix: true })}
          </span>
        </div>
        {renderContent()}
        {isStreaming && (
          <div className="streaming-indicator">
            <span></span>
            <span></span>
            <span></span>
          </div>
        )}
      </div>
    </div>
  );
};