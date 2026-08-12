import { useState, useEffect } from 'react';
import { ChatSessionItem, Message } from '../types';

export function useChatHistory() {
  const [history, setHistory] = useState<ChatSessionItem[]>([]);

  useEffect(() => {
    const saved = localStorage.getItem('datachat-history-sessions');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setHistory(parsed.map((item: any) => ({ ...item, timestamp: new Date(item.timestamp) })));
      } catch (e) {
        console.error('Failed to parse history', e);
      }
    }
  }, []);

  const saveHistory = (newHistory: ChatSessionItem[]) => {
    setHistory(newHistory);
    localStorage.setItem('datachat-history-sessions', JSON.stringify(newHistory));
  };

  const createSession = (id: string, title: string, messages: Message[]) => {
    const newSession: ChatSessionItem = {
      id,
      title,
      messages,
      timestamp: new Date(),
      isFavorite: false
    };
    saveHistory([newSession, ...history]);
  };

  const updateSession = (id: string, messages: Message[]) => {
    setHistory((prev) => {
      const updated = prev.map(session => 
        session.id === id ? { ...session, messages, timestamp: new Date() } : session
      );
      localStorage.setItem('datachat-history-sessions', JSON.stringify(updated));
      return updated;
    });
  };

  const toggleFavorite = (id: string) => {
    saveHistory(history.map(item => item.id === id ? { ...item, isFavorite: !item.isFavorite } : item));
  };

  const clearHistory = () => saveHistory([]);

  return { history, createSession, updateSession, toggleFavorite, clearHistory };
}
