import os

base_dir = r"C:\Users\Dhiraj J S\.gemini\antigravity\scratch\datachat-ai\frontend"

files = {
    "src/index.css": """
:root {
  --bg-primary: #0a0a0f;
  --bg-secondary: #12121a;
  --bg-tertiary: #1a1a2e;
  --bg-glass: rgba(255, 255, 255, 0.03);
  --bg-glass-hover: rgba(255, 255, 255, 0.06);
  --border-subtle: rgba(255, 255, 255, 0.06);
  --border-accent: rgba(139, 92, 246, 0.3);
  --text-primary: #f0f0f5;
  --text-secondary: #a0a0b5;
  --text-muted: #6b6b80;
  --accent-gradient: linear-gradient(135deg, #8b5cf6, #06b6d4);
  --accent-purple: #8b5cf6;
  --accent-cyan: #06b6d4;
  --accent-green: #10b981;
  --shadow-lg: 0 8px 32px rgba(0, 0, 0, 0.4);
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-xl: 24px;
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: 'Inter', sans-serif;
  background-color: var(--bg-primary);
  color: var(--text-primary);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* Custom Scrollbar */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: var(--bg-tertiary);
  border-radius: var(--radius-sm);
}
::-webkit-scrollbar-thumb:hover {
  background: var(--border-accent);
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes pulse {
  0% { opacity: 0.5; }
  50% { opacity: 1; }
  100% { opacity: 0.5; }
}
""",
    
    "src/hooks/useChat.ts": """
import { useState, useCallback } from 'react';
import { Message, ToolCall } from '../types';

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const clearMessages = () => setMessages([]);

  const sendMessage = useCallback(async (content: string, history: Message[] = []) => {
    setIsLoading(true);
    setError(null);
    
    const newUserMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date()
    };
    
    const newAssistantMsg: Message = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isStreaming: true
    };
    
    setMessages(prev => [...prev, newUserMsg, newAssistantMsg]);
    
    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: content, history, database: 'default' })
      });
      
      if (!response.ok) throw new Error('Network response was not ok');
      if (!response.body) throw new Error('No readable stream');
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.replace('data: ', '').trim();
            if (!dataStr) continue;
            
            try {
              const data = JSON.parse(dataStr);
              
              setMessages(prev => {
                const newMsgs = [...prev];
                const lastMsgIndex = newMsgs.length - 1;
                const lastMsg = newMsgs[lastMsgIndex];
                
                if (lastMsg.role === 'assistant' && lastMsg.isStreaming) {
                  const updatedMsg = { ...lastMsg };
                  
                  if (data.type === 'text_delta') {
                    updatedMsg.content += data.content;
                  } else if (data.type === 'tool_start') {
                    updatedMsg.toolCalls = updatedMsg.toolCalls || [];
                    updatedMsg.toolCalls.push({ tool: data.tool, args: data.args, status: 'running' });
                  } else if (data.type === 'tool_result') {
                    if (updatedMsg.toolCalls) {
                      const toolCall = updatedMsg.toolCalls.find(t => t.tool === data.tool && t.status === 'running');
                      if (toolCall) {
                        toolCall.result = data.result;
                        toolCall.status = 'completed';
                      }
                    }
                  } else if (data.type === 'sql_preview') {
                    updatedMsg.sqlPreview = data.sql;
                  } else if (data.type === 'error') {
                     throw new Error(data.message);
                  }
                  
                  newMsgs[lastMsgIndex] = updatedMsg;
                }
                return newMsgs;
              });
              
            } catch (e) {
              console.error('Error parsing SSE:', e);
            }
          }
        }
      }
      
      setMessages(prev => {
        const newMsgs = [...prev];
        const lastMsg = newMsgs[newMsgs.length - 1];
        if (lastMsg.role === 'assistant') {
          newMsgs[newMsgs.length - 1] = { ...lastMsg, isStreaming: false };
        }
        return newMsgs;
      });
      
    } catch (err: any) {
      console.error(err);
      setError(err.message || 'An error occurred');
      setMessages(prev => {
        const newMsgs = [...prev];
        const lastMsg = newMsgs[newMsgs.length - 1];
        if (lastMsg.role === 'assistant') {
          newMsgs[newMsgs.length - 1] = { ...lastMsg, isStreaming: false, content: lastMsg.content + '\\n\\n**Error:** ' + err.message };
        }
        return newMsgs;
      });
    } finally {
      setIsLoading(false);
    }
  }, []);

  return { messages, sendMessage, isLoading, error, clearMessages };
}
""",

    "src/hooks/useQueryHistory.ts": """
import { useState, useEffect } from 'react';
import { QueryHistoryItem } from '../types';

export function useQueryHistory() {
  const [history, setHistory] = useState<QueryHistoryItem[]>([]);

  useEffect(() => {
    const saved = localStorage.getItem('datachat-history');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setHistory(parsed.map((item: any) => ({ ...item, timestamp: new Date(item.timestamp) })));
      } catch (e) {
        console.error('Failed to parse history', e);
      }
    }
  }, []);

  const saveHistory = (newHistory: QueryHistoryItem[]) => {
    setHistory(newHistory);
    localStorage.setItem('datachat-history', JSON.stringify(newHistory));
  };

  const addQuery = (query: string) => {
    const newItem: QueryHistoryItem = {
      id: Date.now().toString(),
      query,
      timestamp: new Date(),
      isFavorite: false
    };
    saveHistory([newItem, ...history]);
  };

  const toggleFavorite = (id: string) => {
    saveHistory(history.map(item => item.id === id ? { ...item, isFavorite: !item.isFavorite } : item));
  };

  const clearHistory = () => saveHistory([]);

  return { history, addQuery, toggleFavorite, clearHistory };
}
""",

    "src/components/WelcomeScreen.css": """
.welcome-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 2rem;
  animation: fadeIn 0.5s ease-out;
}

.welcome-logo {
  font-size: 3rem;
  font-weight: 800;
  background: var(--accent-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 1rem;
}

.welcome-subtitle {
  color: var(--text-secondary);
  font-size: 1.1rem;
  margin-bottom: 3rem;
}

.suggestions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
  width: 100%;
  max-width: 800px;
}

.suggestion-card {
  background: var(--bg-glass);
  border: 1px solid var(--border-subtle);
  padding: 1.5rem;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s ease;
  backdrop-filter: blur(16px);
}

.suggestion-card:hover {
  background: var(--bg-glass-hover);
  border-color: var(--border-accent);
  transform: translateY(-2px);
}

.suggestion-card p {
  color: var(--text-primary);
  font-size: 0.95rem;
  line-height: 1.4;
}
""",

    "src/components/WelcomeScreen.tsx": """
import React from 'react';
import './WelcomeScreen.css';

interface Props {
  onSelectQuery: (query: string) => void;
}

export const WelcomeScreen: React.FC<Props> = ({ onSelectQuery }) => {
  const suggestions = [
    "Show me the top 5 products by revenue",
    "Draw the ER diagram for this database",
    "What's the monthly sales trend?",
    "Create a flowchart of the order process",
    "Which category generates the most revenue?",
    "Show inventory levels vs sales"
  ];

  return (
    <div className="welcome-container">
      <h1 className="welcome-logo">DataChat AI</h1>
      <p className="welcome-subtitle">Ask questions about your data in plain English</p>
      
      <div className="suggestions-grid">
        {suggestions.map((q, i) => (
          <div key={i} className="suggestion-card" onClick={() => onSelectQuery(q)}>
            <p>{q}</p>
          </div>
        ))}
      </div>
    </div>
  );
};
""",

    "src/components/ThinkingIndicator.css": """
.thinking-container {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: var(--bg-glass);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-subtle);
  width: fit-content;
  color: var(--text-secondary);
  font-size: 0.9rem;
  animation: fadeIn 0.3s ease;
}

.thinking-dots {
  display: flex;
  gap: 0.25rem;
}

.thinking-dots span {
  width: 4px;
  height: 4px;
  background-color: var(--accent-purple);
  border-radius: 50%;
  animation: pulse 1s infinite;
}

.thinking-dots span:nth-child(2) { animation-delay: 0.2s; }
.thinking-dots span:nth-child(3) { animation-delay: 0.4s; }
""",

    "src/components/ThinkingIndicator.tsx": """
import React from 'react';
import './ThinkingIndicator.css';
import { Brain } from 'lucide-react';

export const ThinkingIndicator: React.FC = () => {
  return (
    <div className="thinking-container">
      <Brain size={16} className="text-accent-purple" />
      <span>Agent is thinking</span>
      <div className="thinking-dots">
        <span></span><span></span><span></span>
      </div>
    </div>
  );
};
""",

    "src/components/SqlPreview.css": """
.sql-preview-container {
  margin: 1rem 0;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  background: var(--bg-tertiary);
  overflow: hidden;
}

.sql-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 1rem;
  background: rgba(0,0,0,0.2);
  cursor: pointer;
  user-select: none;
}

.sql-header-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--accent-cyan);
  font-size: 0.85rem;
  font-weight: 600;
}

.sql-content {
  padding: 1rem;
  background: #000;
  color: #e5e5e5;
  font-family: monospace;
  font-size: 0.9rem;
  overflow-x: auto;
  white-space: pre-wrap;
}
""",

    "src/components/SqlPreview.tsx": """
import React, { useState } from 'react';
import { Database, ChevronDown, ChevronUp } from 'lucide-react';
import './SqlPreview.css';

export const SqlPreview: React.FC<{ sql: string }> = ({ sql }) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="sql-preview-container">
      <div className="sql-header" onClick={() => setExpanded(!expanded)}>
        <div className="sql-header-title">
          <Database size={16} />
          <span>SQL Preview</span>
        </div>
        {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
      </div>
      {expanded && (
        <div className="sql-content">
          {sql}
        </div>
      )}
    </div>
  );
};
""",

    "src/components/DynamicChart.css": """
.chart-container {
  background: var(--bg-glass);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: 1rem;
  margin: 1rem 0;
  backdrop-filter: blur(16px);
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.chart-title {
  color: var(--text-primary);
  font-weight: 600;
  font-size: 1.1rem;
}

.chart-actions {
  display: flex;
  gap: 0.5rem;
}

.chart-action-btn {
  background: transparent;
  border: 1px solid var(--border-subtle);
  color: var(--text-secondary);
  border-radius: var(--radius-sm);
  padding: 0.25rem;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chart-action-btn:hover {
  background: var(--bg-glass-hover);
  color: var(--text-primary);
  border-color: var(--border-accent);
}

.chart-wrapper {
  width: 100%;
  height: 300px;
}
""",

    "src/components/DynamicChart.tsx": """
import React from 'react';
import { ChartSpec } from '../types';
import { ResponsiveContainer, BarChart, Bar, LineChart, Line, PieChart, Pie, ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, Legend, Cell } from 'recharts';
import { Pin, Download } from 'lucide-react';
import './DynamicChart.css';

const COLORS = ['#8b5cf6', '#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#ec4899', '#6366f1', '#14b8a6'];

interface Props {
  spec: ChartSpec;
  onPin?: (spec: ChartSpec) => void;
}

export const DynamicChart: React.FC<Props> = ({ spec, onPin }) => {
  const handlePin = () => {
    if (onPin) onPin(spec);
  };

  const renderChart = () => {
    switch (spec.type) {
      case 'bar':
        return (
          <BarChart data={spec.data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
            <XAxis dataKey={spec.xAxisKey} stroke="#888" />
            <YAxis stroke="#888" />
            <Tooltip contentStyle={{ backgroundColor: '#1a1a2e', border: '1px solid #333' }} />
            <Legend />
            {spec.series?.map((s, i) => (
              <Bar key={s.dataKey} dataKey={s.dataKey} name={s.name} fill={s.color || COLORS[i % COLORS.length]} radius={[4, 4, 0, 0]} />
            ))}
          </BarChart>
        );
      case 'line':
        return (
          <LineChart data={spec.data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
            <XAxis dataKey={spec.xAxisKey} stroke="#888" />
            <YAxis stroke="#888" />
            <Tooltip contentStyle={{ backgroundColor: '#1a1a2e', border: '1px solid #333' }} />
            <Legend />
            {spec.series?.map((s, i) => (
              <Line key={s.dataKey} type="monotone" dataKey={s.dataKey} name={s.name} stroke={s.color || COLORS[i % COLORS.length]} strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} />
            ))}
          </LineChart>
        );
      case 'pie':
        return (
          <PieChart>
            <Tooltip contentStyle={{ backgroundColor: '#1a1a2e', border: '1px solid #333' }} />
            <Legend />
            <Pie
              data={spec.data}
              dataKey={spec.dataKey || 'value'}
              nameKey={spec.nameKey || 'name'}
              cx="50%"
              cy="50%"
              outerRadius={100}
              label
            >
              {spec.data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
          </PieChart>
        );
      case 'scatter':
        return (
          <ScatterChart>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
            <XAxis dataKey={spec.xAxisKey} type="number" stroke="#888" name="X" />
            <YAxis dataKey={spec.series?.[0]?.dataKey} type="number" stroke="#888" name="Y" />
            <Tooltip cursor={{ strokeDasharray: '3 3' }} contentStyle={{ backgroundColor: '#1a1a2e', border: '1px solid #333' }} />
            <Scatter name={spec.title} data={spec.data} fill={COLORS[0]} />
          </ScatterChart>
        );
      default:
        return <div>Unsupported chart type</div>;
    }
  };

  return (
    <div className="chart-container">
      <div className="chart-header">
        <h3 className="chart-title">{spec.title}</h3>
        <div className="chart-actions">
          {onPin && (
            <button className="chart-action-btn" onClick={handlePin} title="Pin to Dashboard">
              <Pin size={16} />
            </button>
          )}
          <button className="chart-action-btn" title="Export">
            <Download size={16} />
          </button>
        </div>
      </div>
      <div className="chart-wrapper">
        <ResponsiveContainer width="100%" height="100%">
          {renderChart()}
        </ResponsiveContainer>
      </div>
    </div>
  );
};
""",

    "src/components/MermaidDiagram.css": """
.mermaid-container {
  background: var(--bg-glass);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: 1rem;
  margin: 1rem 0;
  backdrop-filter: blur(16px);
}

.mermaid-header {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 0.5rem;
}

.mermaid-content {
  display: flex;
  justify-content: center;
  overflow-x: auto;
  background: rgba(255, 255, 255, 0.05);
  border-radius: var(--radius-sm);
  padding: 1rem;
}

.mermaid-error {
  color: #ef4444;
  font-family: monospace;
  background: rgba(239, 68, 68, 0.1);
  padding: 1rem;
  border-radius: var(--radius-sm);
}
""",

    "src/components/MermaidDiagram.tsx": """
import React, { useEffect, useRef, useState, useId } from 'react';
import mermaid from 'mermaid';
import { Pin } from 'lucide-react';
import './MermaidDiagram.css';

interface Props {
  code: string;
  onPin?: (code: string) => void;
}

export const MermaidDiagram: React.FC<Props> = ({ code, onPin }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [svg, setSvg] = useState<string>('');
  const id = 'mermaid-' + useId().replace(/:/g, '');

  useEffect(() => {
    mermaid.initialize({
      startOnLoad: false,
      theme: 'dark',
      securityLevel: 'loose',
    });

    const renderDiagram = async () => {
      try {
        setError(null);
        const { svg: svgCode } = await mermaid.render(id, code);
        setSvg(svgCode);
      } catch (err: any) {
        setError(err.message || 'Failed to render diagram');
      }
    };

    renderDiagram();
  }, [code, id]);

  return (
    <div className="mermaid-container">
      {onPin && (
        <div className="mermaid-header">
          <button className="chart-action-btn" onClick={() => onPin(code)} title="Pin to Dashboard">
            <Pin size={16} />
          </button>
        </div>
      )}
      {error ? (
        <div className="mermaid-error">{error}\\n\\n{code}</div>
      ) : (
        <div className="mermaid-content" dangerouslySetInnerHTML={{ __html: svg }} />
      )}
    </div>
  );
};
""",

    "src/components/MarkdownRenderer.css": """
.markdown-body {
  color: var(--text-primary);
  line-height: 1.6;
}

.markdown-body p {
  margin-bottom: 1rem;
}

.markdown-body a {
  color: var(--accent-cyan);
  text-decoration: none;
}

.markdown-body a:hover {
  text-decoration: underline;
}

.markdown-body code {
  background: rgba(0, 0, 0, 0.3);
  padding: 0.2em 0.4em;
  border-radius: 3px;
  font-family: monospace;
  font-size: 0.9em;
}

.markdown-body pre {
  background: #000;
  padding: 1rem;
  border-radius: var(--radius-sm);
  overflow-x: auto;
  margin: 1rem 0;
}

.markdown-body pre code {
  background: transparent;
  padding: 0;
  color: #e5e5e5;
}

.code-block-wrapper {
  position: relative;
}

.copy-btn {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-subtle);
  color: var(--text-secondary);
  border-radius: 4px;
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
  cursor: pointer;
}
.copy-btn:hover {
  background: var(--bg-glass-hover);
  color: white;
}
""",

    "src/components/MarkdownRenderer.tsx": """
import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { DynamicChart } from './DynamicChart';
import { MermaidDiagram } from './MermaidDiagram';
import { SqlPreview } from './SqlPreview';
import { ChartSpec } from '../types';
import './MarkdownRenderer.css';

interface Props {
  content: string;
  onPinChart?: (spec: ChartSpec) => void;
  onPinDiagram?: (code: string) => void;
}

export const MarkdownRenderer: React.FC<Props> = ({ content, onPinChart, onPinDiagram }) => {
  return (
    <div className="markdown-body">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          code({ node, inline, className, children, ...props }: any) {
            const match = /language-(\\w+)/.exec(className || '');
            const lang = match ? match[1] : '';
            const code = String(children).replace(/\\n$/, '');

            if (!inline) {
              if (lang === 'chart' || lang === 'json-chart') {
                try {
                  const spec = JSON.parse(code) as ChartSpec;
                  return <DynamicChart spec={spec} onPin={onPinChart} />;
                } catch (e) {
                  return <div className="p-4 border border-red-500 text-red-500 rounded">Invalid chart JSON format...</div>;
                }
              }
              if (lang === 'mermaid') {
                return <MermaidDiagram code={code} onPin={onPinDiagram} />;
              }
              if (lang === 'sql') {
                return <SqlPreview sql={code} />;
              }

              return (
                <div className="code-block-wrapper">
                  <button className="copy-btn" onClick={() => navigator.clipboard.writeText(code)}>Copy</button>
                  <pre><code className={className} {...props}>{children}</code></pre>
                </div>
              );
            }
            return <code className={className} {...props}>{children}</code>;
          }
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};
""",

    "src/components/ChatInput.css": """
.chat-input-container {
  padding: 1rem;
  background: var(--bg-primary);
  border-top: 1px solid var(--border-subtle);
  position: relative;
}

.chat-input-wrapper {
  max-width: 800px;
  margin: 0 auto;
  position: relative;
  background: var(--bg-secondary);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: 0.5rem;
  display: flex;
  align-items: flex-end;
  gap: 0.5rem;
  box-shadow: var(--shadow-lg);
}

.chat-input-wrapper:focus-within {
  border-color: var(--accent-purple);
}

.chat-textarea {
  flex: 1;
  background: transparent;
  border: none;
  color: var(--text-primary);
  font-family: inherit;
  font-size: 1rem;
  padding: 0.75rem;
  resize: none;
  min-height: 44px;
  max-height: 200px;
  outline: none;
}

.chat-textarea::placeholder {
  color: var(--text-muted);
}

.send-btn {
  background: var(--accent-gradient);
  border: none;
  color: white;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: opacity 0.2s;
  flex-shrink: 0;
  margin-bottom: 2px;
}

.send-btn:hover:not(:disabled) {
  opacity: 0.9;
}

.send-btn:disabled {
  background: var(--bg-tertiary);
  color: var(--text-muted);
  cursor: not-allowed;
}

.stop-btn {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
  border: 1px solid #ef4444;
  border-radius: 4px;
  padding: 0.25rem 0.75rem;
  font-size: 0.8rem;
  cursor: pointer;
  position: absolute;
  top: -40px;
  left: 50%;
  transform: translateX(-50%);
}
""",

    "src/components/ChatInput.tsx": """
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
          <Square size={12} className="inline mr-1" /> Stop generating
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
""",

    "src/components/ChatMessage.css": """
.message-row {
  display: flex;
  margin-bottom: 1.5rem;
  animation: slideUp 0.3s ease-out;
  width: 100%;
}

.message-row.user {
  justify-content: flex-end;
}

.message-bubble {
  max-width: 80%;
  padding: 1rem 1.25rem;
  border-radius: var(--radius-lg);
  position: relative;
}

.message-row.user .message-bubble {
  background: var(--accent-gradient);
  color: white;
  border-bottom-right-radius: 4px;
}

.message-row.assistant .message-bubble {
  background: var(--bg-glass);
  border: 1px solid var(--border-subtle);
  border-bottom-left-radius: 4px;
  width: 100%;
}

.message-tools {
  margin-bottom: 1rem;
}

.tool-call {
  background: var(--bg-tertiary);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  margin-bottom: 0.5rem;
  overflow: hidden;
}

.tool-header {
  padding: 0.5rem 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.85rem;
  color: var(--text-secondary);
  cursor: pointer;
  user-select: none;
}

.tool-header:hover {
  background: rgba(255, 255, 255, 0.05);
}

.tool-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-indicator.running { background: #f59e0b; animation: pulse 1s infinite; }
.status-indicator.completed { background: #10b981; }
.status-indicator.error { background: #ef4444; }

.tool-details {
  padding: 1rem;
  background: #000;
  font-family: monospace;
  font-size: 0.8rem;
  color: #a0a0b5;
  border-top: 1px solid var(--border-subtle);
}
""",

    "src/components/ChatMessage.tsx": """
import React, { useState } from 'react';
import { Message } from '../types';
import { MarkdownRenderer } from './MarkdownRenderer';
import { SqlPreview } from './SqlPreview';
import { ChevronDown, ChevronUp, Wrench } from 'lucide-react';
import './ChatMessage.css';

interface Props {
  message: Message;
  onPinChart?: (spec: any) => void;
  onPinDiagram?: (code: string) => void;
}

export const ChatMessage: React.FC<Props> = ({ message, onPinChart, onPinDiagram }) => {
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
                  <div className="flex items-center gap-2">
                    <span className={`status-indicator ${tool.status}`} />
                    {expandedTools[idx] ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                  </div>
                </div>
                {expandedTools[idx] && (
                  <div className="tool-details">
                    <div><strong>Args:</strong> {JSON.stringify(tool.args)}</div>
                    {tool.result && <div className="mt-2"><strong>Result:</strong> {JSON.stringify(tool.result).substring(0, 200)}...</div>}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
        
        {message.sqlPreview && <SqlPreview sql={message.sqlPreview} />}
        
        <MarkdownRenderer 
          content={message.content} 
          onPinChart={onPinChart}
          onPinDiagram={onPinDiagram}
        />
      </div>
    </div>
  );
};
""",

    "src/components/Sidebar.css": """
.sidebar-container {
  width: 280px;
  background: var(--bg-secondary);
  border-right: 1px solid var(--border-subtle);
  display: flex;
  flex-direction: column;
  height: 100vh;
  transition: transform 0.3s ease;
}

.sidebar-container.collapsed {
  transform: translateX(-100%);
  position: absolute;
}

.sidebar-header {
  padding: 1.5rem 1rem;
  border-bottom: 1px solid var(--border-subtle);
}

.new-chat-btn {
  width: 100%;
  background: var(--bg-glass);
  border: 1px solid var(--border-accent);
  color: var(--text-primary);
  padding: 0.75rem;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  cursor: pointer;
  transition: all 0.2s;
  font-weight: 500;
}

.new-chat-btn:hover {
  background: var(--accent-gradient);
  border-color: transparent;
}

.sidebar-tabs {
  display: flex;
  border-bottom: 1px solid var(--border-subtle);
}

.sidebar-tab {
  flex: 1;
  padding: 0.75rem;
  background: transparent;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 0.9rem;
}

.sidebar-tab.active {
  color: var(--accent-cyan);
  border-bottom: 2px solid var(--accent-cyan);
}

.history-list {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

.history-item {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  padding: 0.75rem;
  border-radius: var(--radius-sm);
  cursor: pointer;
  margin-bottom: 0.5rem;
  transition: background 0.2s;
}

.history-item:hover {
  background: var(--bg-glass-hover);
}

.history-content {
  flex: 1;
  overflow: hidden;
}

.history-query {
  color: var(--text-primary);
  font-size: 0.9rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.history-time {
  color: var(--text-muted);
  font-size: 0.75rem;
  margin-top: 0.25rem;
}

.star-btn {
  background: transparent;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
}

.star-btn.starred {
  color: #f59e0b;
}

.sidebar-footer {
  padding: 1rem;
  border-top: 1px solid var(--border-subtle);
}

.clear-btn {
  width: 100%;
  background: transparent;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 0.85rem;
}
.clear-btn:hover {
  color: var(--text-primary);
}
""",

    "src/components/Sidebar.tsx": """
import React, { useState } from 'react';
import { Plus, MessageSquare, Star, Trash2 } from 'lucide-react';
import { QueryHistoryItem } from '../types';
import './Sidebar.css';

interface Props {
  history: QueryHistoryItem[];
  onNewChat: () => void;
  onSelectQuery: (query: string) => void;
  onToggleFavorite: (id: string) => void;
  onClearHistory: () => void;
  isOpen: boolean;
}

export const Sidebar: React.FC<Props> = ({ history, onNewChat, onSelectQuery, onToggleFavorite, onClearHistory, isOpen }) => {
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
          <div key={item.id} className="history-item" onClick={() => onSelectQuery(item.query)}>
            <MessageSquare size={16} className="text-text-muted mt-1 shrink-0" />
            <div className="history-content">
              <div className="history-query">{item.query}</div>
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
          <Trash2 size={14} className="inline mr-2" /> Clear History
        </button>
      </div>
    </div>
  );
};
""",

    "src/components/Dashboard.css": """
.dashboard-container {
  padding: 2rem;
  overflow-y: auto;
  height: 100%;
}

.dashboard-header {
  margin-bottom: 2rem;
}

.dashboard-title {
  font-size: 1.8rem;
  font-weight: 700;
  color: var(--text-primary);
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 1.5rem;
}

.dashboard-item {
  position: relative;
  background: var(--bg-glass);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: 1rem;
}

.remove-pin-btn {
  position: absolute;
  top: 1rem;
  right: 1rem;
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
  border: none;
  width: 24px;
  height: 24px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 10;
}

.empty-dashboard {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 60vh;
  color: var(--text-muted);
}
""",

    "src/components/Dashboard.tsx": """
import React from 'react';
import { DashboardItem } from '../types';
import { DynamicChart } from './DynamicChart';
import { MermaidDiagram } from './MermaidDiagram';
import { LayoutDashboard, X } from 'lucide-react';
import './Dashboard.css';

interface Props {
  items: DashboardItem[];
  onRemove: (id: string) => void;
}

export const Dashboard: React.FC<Props> = ({ items, onRemove }) => {
  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <h2 className="dashboard-title"><LayoutDashboard className="inline mr-2" /> Dashboard</h2>
      </div>

      {items.length === 0 ? (
        <div className="empty-dashboard">
          <LayoutDashboard size={48} className="mb-4 opacity-50" />
          <p>Your dashboard is empty.</p>
          <p>Pin charts and diagrams from the chat to see them here.</p>
        </div>
      ) : (
        <div className="dashboard-grid">
          {items.map(item => (
            <div key={item.id} className="dashboard-item">
              <button className="remove-pin-btn" onClick={() => onRemove(item.id)}>
                <X size={14} />
              </button>
              {item.type === 'chart' ? (
                <DynamicChart spec={item.spec as any} />
              ) : (
                <MermaidDiagram code={item.spec as string} />
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
""",

    "src/components/ChatInterface.css": """
.chat-interface {
  display: flex;
  flex-direction: column;
  height: 100%;
  position: relative;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 2rem;
  display: flex;
  flex-direction: column;
}

.messages-wrapper {
  max-width: 800px;
  margin: 0 auto;
  width: 100%;
}
""",

    "src/components/ChatInterface.tsx": """
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
  onSendMessage: (msg: string) => void;
  onPinChart: (spec: ChartSpec) => void;
  onPinDiagram: (code: string) => void;
}

export const ChatInterface: React.FC<Props> = ({ messages, isLoading, onSendMessage, onPinChart, onPinDiagram }) => {
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
                onPinChart={onPinChart}
                onPinDiagram={onPinDiagram}
              />
            ))}
            {isLoading && messages[messages.length - 1]?.role !== 'assistant' && (
              <div className="mb-4"><ThinkingIndicator /></div>
            )}
            <div ref={endRef} />
          </div>
        )}
      </div>
      <ChatInput onSend={onSendMessage} isLoading={isLoading} />
    </div>
  );
};
""",

    "src/App.css": """
.app-layout {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  background-color: var(--bg-primary);
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  position: relative;
}

.app-header {
  height: 60px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-subtle);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 1rem;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.menu-toggle {
  background: transparent;
  border: none;
  color: var(--text-primary);
  cursor: pointer;
  padding: 0.5rem;
  border-radius: var(--radius-sm);
}

.menu-toggle:hover {
  background: var(--bg-glass);
}

.view-tabs {
  display: flex;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  padding: 0.25rem;
}

.view-tab {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  padding: 0.5rem 1rem;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
}

.view-tab.active {
  background: var(--bg-glass-hover);
  color: var(--text-primary);
  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}
""",

    "src/App.tsx": """
import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { ChatInterface } from './components/ChatInterface';
import { Dashboard } from './components/Dashboard';
import { useChat } from './hooks/useChat';
import { useQueryHistory } from './hooks/useQueryHistory';
import { DashboardItem, ChartSpec } from './types';
import { Menu } from 'lucide-react';
import './App.css';

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [view, setView] = useState<'chat' | 'dashboard'>('chat');
  const [dashboardItems, setDashboardItems] = useState<DashboardItem[]>([]);

  const { messages, sendMessage, isLoading, clearMessages } = useChat();
  const { history, addQuery, toggleFavorite, clearHistory } = useQueryHistory();

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

  const handleSendMessage = (content: string) => {
    addQuery(content);
    sendMessage(content, messages);
    setView('chat');
  };

  const handleNewChat = () => {
    clearMessages();
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
        onNewChat={handleNewChat}
        onSelectQuery={handleSendMessage}
        onToggleFavorite={toggleFavorite}
        onClearHistory={clearHistory}
      />
      <div className="main-content">
        <header className="app-header">
          <div className="header-left">
            <button className="menu-toggle" onClick={() => setSidebarOpen(!sidebarOpen)}>
              <Menu size={20} />
            </button>
            <div className="font-bold bg-clip-text text-transparent bg-gradient-to-r from-purple-500 to-cyan-500 hidden md:block">
              DataChat AI
            </div>
          </div>
          <div className="view-tabs">
            <button className={`view-tab ${view === 'chat' ? 'active' : ''}`} onClick={() => setView('chat')}>Chat</button>
            <button className={`view-tab ${view === 'dashboard' ? 'active' : ''}`} onClick={() => setView('dashboard')}>Dashboard</button>
          </div>
          <div style={{width: 80}}></div>
        </header>

        {view === 'chat' ? (
          <ChatInterface 
            messages={messages}
            isLoading={isLoading}
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
""",

    "src/main.tsx": """
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.tsx';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
"""
}

for filepath, content in files.items():
    full_path = os.path.join(base_dir, filepath)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\\n")
        
print("All source files created successfully.")
