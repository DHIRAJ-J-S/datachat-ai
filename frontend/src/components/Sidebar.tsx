import React, { useState } from 'react';
import { Plus, MessageSquare, Star, Trash2 } from 'lucide-react';
import { ChatSessionItem } from '../types';
import './Sidebar.css';

interface Props {
  history: ChatSessionItem[];
  currentSessionId: string | null;
  onNewChat: () => void;
  onSelectSession: (session: ChatSessionItem) => void;
  onToggleFavorite: (id: string) => void;
  onClearHistory: () => void;
  isOpen: boolean;
}

export const Sidebar: React.FC<Props> = ({ history, currentSessionId, onNewChat, onSelectSession, onToggleFavorite, onClearHistory, isOpen }) => {
  const [tab, setTab] = useState<'all' | 'fav'>('all');

  const filteredHistory = tab === 'all' ? history : history.filter(h => h.isFavorite);

  return (
    <div className={`sidebar-container ${!isOpen ? 'collapsed' : ''}`}>
      <div className="sidebar-header">
        <button className="new-chat-btn" onClick={onNewChat}>
          <Plus size={18} /> New Chat
        </button>
      </div>
      
      <div className="sidebar-tabs">
        <button className={`sidebar-tab ${tab === 'all' ? 'active' : ''}`} onClick={() => setTab('all')}>History</button>
        <button className={`sidebar-tab ${tab === 'fav' ? 'active' : ''}`} onClick={() => setTab('fav')}>Favorites</button>
      </div>

      <div className="history-list">
        {filteredHistory.map(item => (
          <div 
            key={item.id} 
            className={`history-item ${item.id === currentSessionId ? 'active' : ''}`} 
            onClick={() => onSelectSession(item)}
          >
            <MessageSquare size={16} style={{ color: 'var(--text-muted)', marginTop: '2px', flexShrink: 0 }} />
            <div className="history-content">
              <div className="history-query">{item.title}</div>
              <div className="history-time">{new Date(item.timestamp).toLocaleDateString()}</div>
            </div>
            <button 
              className={`star-btn ${item.isFavorite ? 'starred' : ''}`}
              onClick={(e) => { e.stopPropagation(); onToggleFavorite(item.id); }}
            >
              <Star size={16} fill={item.isFavorite ? "currentColor" : "none"} />
            </button>
          </div>
        ))}
      </div>

      <div className="sidebar-footer">
        <button className="clear-btn" onClick={onClearHistory}>
          <Trash2 size={14} style={{ display: 'inline', marginRight: '0.5rem' }} /> Clear History
        </button>
      </div>
    </div>
  );
};