export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  toolCalls?: ToolCall[];
  sqlPreview?: string;
  isStreaming?: boolean;
}

export interface ToolCall {
  tool: string;
  args: Record<string, any>;
  result?: any;
  status: 'running' | 'completed' | 'error';
}

export interface ChartSpec {
  type: 'bar' | 'line' | 'pie' | 'scatter';
  title: string;
  data: Record<string, any>[];
  xAxisKey?: string;
  yAxisKey?: string;
  series?: { dataKey: string; name: string; color: string }[];
  dataKey?: string;
  nameKey?: string;
}

export interface ChatSessionItem {
  id: string;
  title: string;
  messages: Message[];
  timestamp: Date;
  isFavorite: boolean;
}

export interface DashboardItem {
  id: string;
  type: 'chart' | 'diagram';
  spec: ChartSpec | string;
  title: string;
}
