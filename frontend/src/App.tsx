import React, { useState, useEffect, useRef } from 'react';
import { Sidebar } from './components/Sidebar';
import { ChatInterface } from './components/ChatInterface';
import { Dashboard } from './components/Dashboard';
import { useChat } from './hooks/useChat';
import { useChatHistory } from './hooks/useChatHistory';
import { DashboardItem, ChartSpec, ChatSessionItem } from './types';
import { Menu } from 'lucide-react';
import './App.css';

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [view, setView] = useState<'chat' | 'dashboard'>('chat');
  const [dashboardItems, setDashboardItems] = useState<DashboardItem[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [dbName, setDbName] = useState<string>('ecommerce.db');

  const { messages, sendMessage, isLoading, clearMessages, setMessages } = useChat(dbName);
  const { history, createSession, updateSession, toggleFavorite, clearHistory } = useChatHistory();

  // Sync current messages to the active session
  useEffect(() => {
    if (currentSessionId && messages.length > 0) {
      updateSession(currentSessionId, messages);
    }
  }, [messages, currentSessionId]);

  useEffect(() => {
    const saved = localStorage.getItem('datachat-dashboard');
    if (saved) {
      try { setDashboardItems(JSON.parse(saved)); } catch (e) {}
    }
  }, []);

  const saveDashboard = (items: DashboardItem[]) => {
    setDashboardItems(items);
    localStorage.setItem('datachat-dashboard', JSON.stringify(items));
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('/api/upload-database', {
        method: 'POST',
        body: formData,
      });
      if (response.ok) {
        setDbName(file.name);
        alert(`Successfully connected to ${file.name}`);
      } else {
        alert('Failed to upload database');
      }
    } catch (error) {
      alert('Error uploading database');
    }
  };

  const handleSendMessage = (content: string) => {
    if (!currentSessionId) {
      const newId = Date.now().toString();
      setCurrentSessionId(newId);
      // Give it a title based on the first query
      createSession(newId, content.slice(0, 40) + (content.length > 40 ? '...' : ''), []);
    }
    sendMessage(content, messages);
    setView('chat');
  };

  const handleNewChat = () => {
    setCurrentSessionId(null);
    clearMessages();
    setView('chat');
  };
  
  const handleSelectSession = (session: ChatSessionItem) => {
    setCurrentSessionId(session.id);
    setMessages(session.messages);
    setView('chat');
  };

  const handlePinChart = (spec: ChartSpec) => {
    const newItem: DashboardItem = {
      id: Date.now().toString(),
      type: 'chart',
      spec,
      title: spec.title || 'Chart'
    };
    saveDashboard([...dashboardItems, newItem]);
  };

  const handlePinDiagram = (code: string) => {
    const newItem: DashboardItem = {
      id: Date.now().toString(),
      type: 'diagram',
      spec: code,
      title: 'Diagram'
    };
    saveDashboard([...dashboardItems, newItem]);
  };

  const handleRemovePin = (id: string) => {
    saveDashboard(dashboardItems.filter(item => item.id !== id));
  };

  return (
    <div className="app-layout">
      <Sidebar 
        isOpen={sidebarOpen}
        history={history}
        currentSessionId={currentSessionId}
        onNewChat={handleNewChat}
        onSelectSession={handleSelectSession}
        onToggleFavorite={toggleFavorite}
        onClearHistory={clearHistory}
      />
      <div className="main-content">
        <header className="app-header">
          <div className="header-left">
            <button className="menu-toggle" onClick={() => setSidebarOpen(!sidebarOpen)}>
              <Menu size={20} />
            </button>
            <div className="app-title">
              DataChat AI
            </div>
          </div>
          <div className="view-tabs">
            <button className={`view-tab ${view === 'chat' ? 'active' : ''}`} onClick={() => setView('chat')}>💬 Chat</button>
            <button className={`view-tab ${view === 'dashboard' ? 'active' : ''}`} onClick={() => setView('dashboard')}>
              📌 Dashboard {dashboardItems.length > 0 && <span className="tab-badge">{dashboardItems.length}</span>}
            </button>
          </div>
          <div className="header-right" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <label className="upload-btn" style={{ cursor: 'pointer', fontSize: '0.85rem', background: 'var(--bg-glass)', padding: '0.25rem 0.75rem', borderRadius: '4px', border: '1px solid var(--border-light)' }}>
              + Upload DB
              <input type="file" accept=".db,.sqlite,.sqlite3" style={{ display: 'none' }} onChange={handleFileUpload} />
            </label>
            <div className="db-status-badge" title={`Connected to ${dbName}`}>
              <span className="status-dot"></span>
              <span className="db-name">{dbName}</span>
            </div>
          </div>
        </header>

        {view === 'chat' ? (
          <ChatInterface 
            messages={messages}
            isLoading={isLoading}
            dbName={dbName}
            onSendMessage={handleSendMessage}
            onPinChart={handlePinChart}
            onPinDiagram={handlePinDiagram}
          />
        ) : (
          <Dashboard items={dashboardItems} onRemove={handleRemovePin} />
        )}
      </div>
    </div>
  );
}

export default App;