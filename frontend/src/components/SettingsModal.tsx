import React, { useState, useEffect } from 'react';
import { X, Check } from 'lucide-react';
import './SettingsModal.css';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onSaved: () => void;
}

export const SettingsModal: React.FC<Props> = ({ isOpen, onClose, onSaved }) => {
  const [provider, setProvider] = useState('openai');
  const [apiKey, setApiKey] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [hasKeyInitially, setHasKeyInitially] = useState(true);

  useEffect(() => {
    if (isOpen) {
      fetch('/api/settings')
        .then(res => res.json())
        .then(data => {
          setProvider(data.provider || 'openai');
          setHasKeyInitially(data.has_key);
        })
        .catch(console.error);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!apiKey && !hasKeyInitially) {
      alert("Please enter an API key.");
      return;
    }

    setIsSaving(true);
    try {
      const res = await fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider, api_key: apiKey })
      });
      if (res.ok) {
        onSaved();
        onClose();
        // Clear input for security
        setApiKey('');
      } else {
        alert("Failed to save settings.");
      }
    } catch (err) {
      console.error(err);
      alert("Error saving settings.");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <button className="modal-close" onClick={onClose} disabled={!hasKeyInitially}>
          <X size={20} />
        </button>
        <h2>⚙️ Configuration</h2>
        <p className="modal-desc">
          {!hasKeyInitially 
            ? "Welcome to DataChat AI! Please configure your AI provider to begin."
            : "Update your AI provider and API key here."}
        </p>

        <form onSubmit={handleSave}>
          <div className="form-group">
            <label>AI Provider</label>
            <select value={provider} onChange={(e) => setProvider(e.target.value)}>
              <option value="openai">OpenAI (ChatGPT)</option>
              <option value="anthropic">Anthropic (Claude)</option>
              <option value="groq">Groq (Llama 3)</option>
            </select>
          </div>

          <div className="form-group">
            <label>API Key</label>
            <input 
              type="password" 
              value={apiKey} 
              onChange={(e) => setApiKey(e.target.value)}
              placeholder={hasKeyInitially ? "•••••••••••••••• (Leave blank to keep current)" : "sk-..."}
            />
          </div>

          <button type="submit" className="save-btn" disabled={isSaving}>
            {isSaving ? "Saving..." : <><Check size={16} /> Save Configuration</>}
          </button>
        </form>
      </div>
    </div>
  );
};
