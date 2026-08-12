import React, { useState } from 'react';
import { Database, ChevronDown, ChevronUp, Download } from 'lucide-react';
import './SqlPreview.css';

interface Props {
  sql: string;
  dbName?: string;
}

export const SqlPreview: React.FC<Props> = ({ sql, dbName }) => {
  const [expanded, setExpanded] = useState(false);
  const [isExporting, setIsExporting] = useState(false);

  const handleDownloadCsv = async (e: React.MouseEvent) => {
    e.stopPropagation(); // prevent collapsing the preview
    setIsExporting(true);
    try {
      const response = await fetch('/api/export-csv', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: sql, database: dbName })
      });
      
      if (!response.ok) throw new Error('Failed to export CSV');
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'query_results.csv';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      alert('Error exporting CSV');
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="sql-preview-container">
      <div className="sql-header" onClick={() => setExpanded(!expanded)}>
        <div className="sql-header-title">
          <Database size={16} />
          <span>SQL Preview</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          {expanded && (
            <button 
              className="chart-action-btn" 
              onClick={handleDownloadCsv} 
              title="Download Results as CSV"
              disabled={isExporting}
              style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', padding: '4px' }}
            >
              <Download size={14} />
            </button>
          )}
          {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </div>
      </div>
      {expanded && (
        <div className="sql-content">
          {sql}
        </div>
      )}
    </div>
  );
};