import React from 'react';
import './ThinkingIndicator.css';
import { Brain } from 'lucide-react';

export const ThinkingIndicator: React.FC = () => {
  return (
    <div className="thinking-container">
      <Brain size={16} style={{ color: 'var(--accent-purple)' }} />
      <span>Agent is thinking</span>
      <div className="thinking-dots">
        <span></span><span></span><span></span>
      </div>
    </div>
  );
};