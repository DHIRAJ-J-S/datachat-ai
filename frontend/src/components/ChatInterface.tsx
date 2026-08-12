import React, { useRef, useEffect } from 'react';
import { Message, ChartSpec } from '../types';
import { ChatMessage } from './ChatMessage';
import { ChatInput } from './ChatInput';
import { WelcomeScreen } from './WelcomeScreen';
import { ThinkingIndicator } from './ThinkingIndicator';
import './ChatInterface.css';

interface Props {
  messages: Message[];
  isLoading: boolean;
  dbName?: string;
  onSendMessage: (msg: string) => void;
  onPinChart?: (spec: ChartSpec) => void;
  onPinDiagram?: (code: string) => void;
}

export const ChatInterface: React.FC<Props> = ({ 
  messages, 
  isLoading, 
  dbName,
  onSendMessage,
  onPinChart,
  onPinDiagram
}) => {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  return (
    <div className="chat-interface">
      <div className="messages-container">
        {messages.length === 0 ? (
          <WelcomeScreen onSelectQuery={onSendMessage} />
        ) : (
          <div className="messages-wrapper">
            {messages.map(msg => (
              <ChatMessage 
                key={msg.id} 
                message={msg} 
                dbName={dbName}
                onPinChart={onPinChart}
                onPinDiagram={onPinDiagram}
              />
            ))}
            {isLoading && messages[messages.length - 1]?.role !== 'assistant' && (
              <div style={{ marginBottom: '1rem' }}><ThinkingIndicator /></div>
            )}
            <div ref={endRef} />
          </div>
        )}
      </div>
      <ChatInput onSend={onSendMessage} isLoading={isLoading} />
    </div>
  );
};