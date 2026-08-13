import React, { useState, useRef } from 'react';
import { Plus, MessageSquare, Star, Trash2, Download, Upload, Settings } from 'lucide-react';
import { ChatSessionItem } from '../types';
import './Sidebar.css';

interface Props {
  history: ChatSessionItem[];
  currentSessionId: string | null;
  onNewChat: () => void;
  onSelectSession: (session: ChatSessionItem) => void;
  onToggleFavorite: (id: string) => void;
  onClearHistory: () => void;
  onOpenSettings: () => void;
  isOpen: boolean;
}

export const Sidebar: React.FC<Props> = ({ history, currentSessionId, onNewChat, onSelectSession, onToggleFavorite, onClearHistory, onOpenSettings, isOpen }) => {
  const [tab, setTab] = useState<'all' | 'fav'>('all');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const filteredHistory = tab === 'all' ? history : history.filter(h => h.isFavorite);

  const handleExport = () => {
    const backupData = {
      sessions: localStorage.getItem('datachat-sessions'),
      dashboard: localStorage.getItem('datachat-dashboard')
    };
    const blob = new Blob([JSON.stringify(backupData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `datachat-backup-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    URL.revokeObjectURL(url);
    document.body.removeChild(a);
  };

  const handleImport = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const data = JSON.parse(event.target?.result as string);
        if (data.sessions) localStorage.setItem('datachat-sessions', data.sessions);
        if (data.dashboard) localStorage.setItem('datachat-dashboard', data.dashboard);
        alert('Data imported successfully! App will now reload.');
        window.location.reload();
      } catch (err) {
        alert('Invalid backup file.');
      }
    };
    reader.readAsText(file);
  };

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

      <div className="sidebar-footer" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        <button className="clear-btn" onClick={onOpenSettings}>
          <Settings size={14} style={{ display: 'inline', marginRight: '0.5rem' }} /> Settings
        </button>
        <button className="clear-btn" onClick={handleExport}>
          <Download size={14} style={{ display: 'inline', marginRight: '0.5rem' }} /> Export Data
        </button>
        <button className="clear-btn" onClick={() => fileInputRef.current?.click()}>
          <Upload size={14} style={{ display: 'inline', marginRight: '0.5rem' }} /> Import Data
        </button>
        <input type="file" ref={fileInputRef} style={{ display: 'none' }} accept=".json" onChange={handleImport} />
        <button className="clear-btn" onClick={onClearHistory}>
          <Trash2 size={14} style={{ display: 'inline', marginRight: '0.5rem' }} /> Clear History
        </button>
      </div>
    </div>
  );
};