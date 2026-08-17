import { useState, useEffect, useCallback, useRef } from 'react';

export type MessageType = 'user' | 'assistant' | 'welcome' | 'error' | 'status';

export interface ChatMessageData {
  id: string;
  type: MessageType;
  content: string;
  model?: string;
  tier?: string;
  tokens?: { input: number; output: number };
  timestamp: Date;
}

export const useWebSocket = () => {
  const [messages, setMessages] = useState<ChatMessageData[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isThinking, setIsThinking] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  
  const ws = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  const connect = useCallback(() => {
    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/chat`;
      ws.current = new WebSocket(wsUrl);

      ws.current.onopen = () => {
        setIsConnected(true);
        reconnectAttempts.current = 0;
      };

      ws.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'welcome') {
          setSessionId(data.session_id);
          setMessages(prev => [...prev, {
            id: crypto.randomUUID(),
            type: 'welcome',
            content: data.content,
            timestamp: new Date()
          }]);
        } else if (data.type === 'status' && data.content === 'thinking') {
          setIsThinking(true);
        } else if (data.type === 'response') {
          setIsThinking(false);
          setMessages(prev => [...prev, {
            id: crypto.randomUUID(),
            type: 'assistant',
            content: data.content,
            model: data.model,
            tier: data.tier,
            tokens: data.tokens,
            timestamp: new Date()
          }]);
        } else if (data.type === 'error') {
          setIsThinking(false);
          setMessages(prev => [...prev, {
            id: crypto.randomUUID(),
            type: 'error',
            content: data.content,
            timestamp: new Date()
          }]);
        }
      };

      ws.current.onclose = () => {
        setIsConnected(false);
        setIsThinking(false);
        if (reconnectAttempts.current < maxReconnectAttempts) {
          const timeout = Math.pow(2, reconnectAttempts.current) * 1000;
          setTimeout(connect, timeout);
          reconnectAttempts.current += 1;
        }
      };

      ws.current.onerror = () => {
        ws.current?.close();
      };
    } catch (error) {
      console.error('WebSocket connection error', error);
    }
  }, []);

  useEffect(() => {
    connect();
    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [connect]);

  const sendMessage = useCallback((content: string) => {
    if (ws.current && isConnected) {
      setMessages(prev => [...prev, {
        id: crypto.randomUUID(),
        type: 'user',
        content,
        timestamp: new Date()
      }]);
      setIsThinking(true);
      ws.current.send(JSON.stringify({ type: 'message', content }));
    }
  }, [isConnected]);

  const clearContext = useCallback(() => {
    if (ws.current && isConnected) {
      ws.current.send(JSON.stringify({ type: 'clear' }));
      setMessages([]);
      setIsThinking(false);
    }
  }, [isConnected]);

  return { messages, isConnected, isThinking, sessionId, sendMessage, clearContext };
};
