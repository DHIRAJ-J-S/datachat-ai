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
        <h2 className="dashboard-title"><LayoutDashboard style={{ display: 'inline', marginRight: '0.5rem' }} /> Dashboard</h2>
      </div>

      {items.length === 0 ? (
        <div className="empty-dashboard">
          <LayoutDashboard size={48} style={{ marginBottom: '1rem', opacity: 0.5 }} />
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