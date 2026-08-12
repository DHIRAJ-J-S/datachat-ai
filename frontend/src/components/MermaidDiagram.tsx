import React, { useEffect, useRef, useState, useId } from 'react';
import mermaid from 'mermaid';
import { Pin, Download } from 'lucide-react';
import { downloadElementAsImage } from '../utils/exportImage';
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

  const handleDownload = () => {
    downloadElementAsImage(id + '-container', 'diagram');
  };

  return (
    <div className="mermaid-container" id={id + '-container'}>
      <div className="mermaid-header" data-html2canvas-ignore>
        {onPin && (
          <button className="chart-action-btn" onClick={() => onPin(code)} title="Pin to Dashboard">
            <Pin size={16} />
          </button>
        )}
        <button className="chart-action-btn" onClick={handleDownload} title="Export Image">
          <Download size={16} />
        </button>
      </div>
      {error ? (
        <div className="mermaid-error">{error}\n\n{code}</div>
      ) : (
        <div className="mermaid-content" dangerouslySetInnerHTML={{ __html: svg }} />
      )}
    </div>
  );
};