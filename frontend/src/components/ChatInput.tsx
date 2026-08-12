import React, { useState, useRef, useEffect } from 'react';
import { Send, Square } from 'lucide-react';
import './ChatInput.css';

interface Props {
  onSend: (msg: string) => void;
  isLoading: boolean;
}

export const ChatInput: React.FC<Props> = ({ onSend, isLoading }) => {
  const [text, setText] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [text]);

  const handleSend = () => {
    if (text.trim() && !isLoading) {
      onSend(text.trim());
      setText('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-input-container">
      {isLoading && (
        <button className="stop-btn">
          <Square size={12} style={{ display: 'inline', marginRight: '4px' }} /> Stop generating
        </button>
      )}
      <div className="chat-input-wrapper">
        <textarea
          ref={textareaRef}
          className="chat-textarea"
          placeholder="Ask a question about your data..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={1}
          disabled={isLoading}
        />
        <button 
          className="send-btn" 
          onClick={handleSend}
          disabled={!text.trim() || isLoading}
        >
          <Send size={18} />
        </button>
      </div>
    </div>
  );
};