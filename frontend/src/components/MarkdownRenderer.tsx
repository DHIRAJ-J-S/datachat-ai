import React, { useId } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { DynamicChart } from './DynamicChart';
import { MermaidDiagram } from './MermaidDiagram';
import { SqlPreview } from './SqlPreview';
import { ChartSpec } from '../types';
import { Download } from 'lucide-react';
import { downloadElementAsImage } from '../utils/exportImage';
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
          table({ node, ...props }: any) {
            const tableId = 'table-' + useId().replace(/:/g, '');
            return (
              <div className="table-wrapper-exportable" id={tableId} style={{ position: 'relative', marginBottom: '1rem' }}>
                <div data-html2canvas-ignore style={{ position: 'absolute', top: '-1.5rem', right: '0' }}>
                   <button 
                    onClick={() => downloadElementAsImage(tableId, 'table-export')}
                    className="chart-action-btn"
                    title="Export Image"
                    style={{ background: 'var(--bg-glass)', border: '1px solid var(--border-light)', borderRadius: '4px', padding: '4px', color: 'var(--text-secondary)', cursor: 'pointer' }}
                   >
                     <Download size={14} />
                   </button>
                </div>
                <div style={{ overflowX: 'auto', background: 'var(--bg-primary)', padding: '0.5rem', borderRadius: '4px' }}>
                  <table {...props} />
                </div>
              </div>
            );
          },
          code({ node, inline, className, children, ...props }: any) {
            const match = /language-(\w+)/.exec(className || '');
            const lang = match ? match[1] : '';
            const code = String(children).replace(/\n$/, '');

            if (!inline) {
              if (lang === 'chart' || lang === 'json-chart') {
                try {
                  const spec = JSON.parse(code) as ChartSpec;
                  return <DynamicChart spec={spec} onPin={onPinChart} />;
                } catch (e) {
                  return <div className="chart-error">Invalid chart JSON format...</div>;
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