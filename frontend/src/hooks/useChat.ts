import { useState, useCallback } from 'react';
import { Message, ToolCall } from '../types';

export function useChat(dbName?: string) {
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
        body: JSON.stringify({
          message: content,
          history: history.map(m => ({ role: m.role, content: m.content })),
          database: dbName
        })
      });
      
      if (!response.ok) throw new Error('Network response was not ok');
      if (!response.body) throw new Error('No readable stream');
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.replace('data: ', '').trim();
            if (!dataStr) continue;
            
            try {
              const data = JSON.parse(dataStr);
              
              if (data.type === 'error') {
                // Server-side error — surface it to the chat
                setMessages(prev => {
                  const newMsgs = [...prev];
                  const lastMsg = newMsgs[newMsgs.length - 1];
                  if (lastMsg.role === 'assistant') {
                    newMsgs[newMsgs.length - 1] = {
                      ...lastMsg,
                      isStreaming: false,
                      content: lastMsg.content + '\n\n**Error:** ' + (data.message || 'Unknown server error')
                    };
                  }
                  return newMsgs;
                });
                continue;
              }

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
          newMsgs[newMsgs.length - 1] = { ...lastMsg, isStreaming: false, content: lastMsg.content + '\n\n**Error:** ' + err.message };
        }
        return newMsgs;
      });
    } finally {
      setIsLoading(false);
    }
  }, []);

  return { messages, sendMessage, isLoading, error, clearMessages, setMessages };
}