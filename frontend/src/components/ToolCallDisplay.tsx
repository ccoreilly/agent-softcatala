import React, { useState } from 'react';
import { ToolCall } from '../types';
import './ToolCallDisplay.css';

interface ToolCallDisplayProps {
  toolCall: ToolCall;
  isExecuting?: boolean;
}

export const ToolCallDisplay: React.FC<ToolCallDisplayProps> = ({
  toolCall,
  isExecuting = false,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const formatJson = (obj: any) => {
    return JSON.stringify(obj, null, 2);
  };

  const getToolIcon = (toolName: string) => {
    switch (toolName) {
      case 'web_browser':
        return '🌐';
      default:
        return '🔧';
    }
  };

  const getStatusIcon = () => {
    if (isExecuting) return '⏳';
    if (toolCall.error) return '❌';
    if (toolCall.result) return '✅';
    return '🔧';
  };

  const getStatusText = () => {
    if (isExecuting) return 'Executing...';
    if (toolCall.error) return 'Error';
    if (toolCall.result) return 'Completed';
    return 'Pending';
  };

  return (
    <div className={`tool-call-display ${isExecuting ? 'executing' : ''}`}>
      <div className="tool-call-header" onClick={() => setIsExpanded(!isExpanded)}>
        <div className="tool-info">
          <span className="tool-icon">{getToolIcon(toolCall.tool)}</span>
          <span className="tool-name">{toolCall.tool}</span>
          <span className="tool-status">
            {getStatusIcon()} {getStatusText()}
          </span>
        </div>
        <button className="expand-button" type="button">
          {isExpanded ? '▼' : '▶'}
        </button>
      </div>

      {isExpanded && (
        <div className="tool-call-details">
          <div className="parameters-section">
            <h4>Parameters:</h4>
            <pre className="json-display">
              {formatJson(toolCall.parameters)}
            </pre>
          </div>

          {toolCall.result && (
            <div className="result-section">
              <h4>Result:</h4>
              {toolCall.tool === 'web_browser' && toolCall.result.status === 'success' ? (
                <div className="web-result">
                  <div className="web-result-header">
                    <strong>{toolCall.result.title}</strong>
                    <a
                      href={toolCall.result.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="url-link"
                    >
                      {toolCall.result.url}
                    </a>
                  </div>
                  <div className="web-content">
                    {toolCall.result.content.substring(0, 500)}
                    {toolCall.result.content.length > 500 && '...'}
                  </div>
                  {toolCall.result.links && toolCall.result.links.length > 0 && (
                    <div className="extracted-links">
                      <h5>Extracted Links:</h5>
                      <ul>
                        {toolCall.result.links.slice(0, 5).map((link: any, index: number) => (
                          <li key={index}>
                            <a href={link.url} target="_blank" rel="noopener noreferrer">
                              {link.text}
                            </a>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ) : (
                <pre className="json-display">
                  {formatJson(toolCall.result)}
                </pre>
              )}
            </div>
          )}

          {toolCall.error && (
            <div className="error-section">
              <h4>Error:</h4>
              <div className="error-message">{toolCall.error}</div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};