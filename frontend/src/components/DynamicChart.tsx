import React from 'react';
import { ChartSpec } from '../types';
import { ResponsiveContainer, BarChart, Bar, LineChart, Line, PieChart, Pie, ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, Legend, Cell } from 'recharts';
import { Pin, Download } from 'lucide-react';
import { downloadElementAsImage } from '../utils/exportImage';
import './DynamicChart.css';

const COLORS = ['#8b5cf6', '#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#ec4899', '#6366f1', '#14b8a6'];

interface Props {
  spec: ChartSpec;
  onPin?: (spec: ChartSpec) => void;
}

export const DynamicChart: React.FC<Props> = ({ spec, onPin }) => {
  const chartId = React.useId();

  const handlePin = () => {
    if (onPin) onPin(spec);
  };

  const handleDownload = () => {
    downloadElementAsImage(`chart-${chartId}`, spec.title || 'chart');
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
              {spec.data.map((_, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
          </PieChart>
        );
      case 'scatter':
        return (
          <ScatterChart>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
            <XAxis dataKey={spec.xAxisKey} type="number" name={spec.xAxisKey} stroke="#888" />
            <YAxis dataKey={spec.yAxisKey || 'value'} type="number" stroke="#888" />
            <Tooltip contentStyle={{ backgroundColor: '#1a1a2e', border: '1px solid #333' }} cursor={{ strokeDasharray: '3 3' }} />
            <Legend />
            {spec.series ? spec.series.map((s, i) => (
              <Scatter key={s.dataKey} name={s.name} data={spec.data} fill={s.color || COLORS[i % COLORS.length]} />
            )) : (
              <Scatter name="Data" data={spec.data} fill={COLORS[0]} />
            )}
          </ScatterChart>
        );
      default:
        return <div>Unsupported chart type</div>;
    }
  };

  return (
    <div className="chart-container" id={`chart-${chartId}`}>
      <div className="chart-header" data-html2canvas-ignore>
        <h3 className="chart-title">{spec.title}</h3>
        <div className="chart-actions">
          {onPin && (
            <button className="chart-action-btn" onClick={handlePin} title="Pin to Dashboard">
              <Pin size={16} />
            </button>
          )}
          <button className="chart-action-btn" title="Export Image" onClick={handleDownload}>
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