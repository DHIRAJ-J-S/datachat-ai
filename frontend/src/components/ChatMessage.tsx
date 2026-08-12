import React, { useState } from 'react';
import { Message } from '../types';
import { MarkdownRenderer } from './MarkdownRenderer';
import { SqlPreview } from './SqlPreview';
import { ChevronDown, ChevronUp, Wrench } from 'lucide-react';
import './ChatMessage.css';

interface Props {
  message: Message;
  dbName?: string;
  onPinChart?: (spec: any) => void;
  onPinDiagram?: (code: string) => void;
}

export const ChatMessage: React.FC<Props> = ({ message, dbName, onPinChart, onPinDiagram }) => {
  const isUser = message.role === 'user';

  const [expandedTools, setExpandedTools] = useState<Record<number, boolean>>({});

  const toggleTool = (index: number) => {
    setExpandedTools(prev => ({ ...prev, [index]: !prev[index] }));
  };

  return (
    <div className={`message-row ${isUser ? 'user' : 'assistant'}`}>
      <div className="message-bubble">
        {message.toolCalls && message.toolCalls.length > 0 && (
          <div className="message-tools">
            {message.toolCalls.map((tool, idx) => (
              <div key={idx} className="tool-call">
                <div className="tool-header" onClick={() => toggleTool(idx)}>
                  <div className="tool-status">
                    <Wrench size={14} />
                    <span>Using tool: {tool.tool}</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span className={`status-indicator ${tool.status}`} />
                    {expandedTools[idx] ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                  </div>
                </div>
                {expandedTools[idx] && (
                  <div className="tool-details">
                    <div><strong>Args:</strong> {JSON.stringify(tool.args)}</div>
                    {tool.result && <div style={{ marginTop: '0.5rem' }}><strong>Raw Result:</strong> {JSON.stringify(tool.result).substring(0, 200)}...</div>}
                  </div>
                )}
                {/* Automatically render visual tool results if the LLM fails to echo them */}
                {tool.status === 'completed' && tool.result && typeof tool.result === 'string' && (tool.result.includes('```chart') || tool.result.includes('```mermaid')) && (
                  <div className="tool-visual-result" style={{ marginTop: '0.75rem', padding: '0.5rem', background: 'var(--bg-primary)', borderRadius: '0.5rem', border: '1px solid var(--border-light)' }}>
                    <MarkdownRenderer 
                      content={tool.result} 
                      onPinChart={onPinChart}
                      onPinDiagram={onPinDiagram}
                    />
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
        
        {message.sqlPreview && <SqlPreview sql={message.sqlPreview} dbName={dbName} />}
        
        <MarkdownRenderer 
          content={message.content} 
          onPinChart={onPinChart}
          onPinDiagram={onPinDiagram}
        />
      </div>
    </div>
  );
};