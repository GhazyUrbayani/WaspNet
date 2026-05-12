/**
 * ChainRadar — SSE Alert Stream Hook
 * Connects to the backend SSE endpoint for real-time alert notifications.
 */

'use client';

import { useEffect, useRef, useState, useCallback } from 'react';

export interface StreamEvent {
  type: 'alert' | 'notification' | 'connected' | 'error';
  data: Record<string, unknown>;
  timestamp: Date;
}

interface UseAlertStreamOptions {
  enabled?: boolean;
  onEvent?: (event: StreamEvent) => void;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

export function useAlertStream(options: UseAlertStreamOptions = {}) {
  const {
    enabled = true,
    onEvent,
    reconnectInterval = 3000,
    maxReconnectAttempts = 10,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [error, setError] = useState<string | null>(null);

  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectAttempts = useRef(0);
  const reconnectTimer = useRef<NodeJS.Timeout | null>(null);

  const connect = useCallback(() => {
    if (typeof window === 'undefined') return;

    const token = localStorage.getItem('chainradar_access_token');
    if (!token) return;

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

    // EventSource doesn't support custom headers, so we pass token as query param
    // In production, use a proper SSE library or proxy
    const url = `${apiUrl}/api/v1/stream/events?token=${encodeURIComponent(token)}`;

    try {
      const es = new EventSource(url);
      eventSourceRef.current = es;

      es.onopen = () => {
        setIsConnected(true);
        setError(null);
        reconnectAttempts.current = 0;
      };

      es.addEventListener('connected', (e) => {
        const data = JSON.parse(e.data);
        const event: StreamEvent = { type: 'connected', data, timestamp: new Date() };
        onEvent?.(event);
      });

      es.addEventListener('alert', (e) => {
        const data = JSON.parse(e.data);
        const event: StreamEvent = { type: 'alert', data, timestamp: new Date() };
        setEvents((prev) => [event, ...prev].slice(0, 100)); // Keep last 100
        onEvent?.(event);
      });

      es.addEventListener('notification', (e) => {
        const data = JSON.parse(e.data);
        const event: StreamEvent = { type: 'notification', data, timestamp: new Date() };
        setEvents((prev) => [event, ...prev].slice(0, 100));
        onEvent?.(event);
      });

      es.addEventListener('error', (e) => {
        const data = e instanceof MessageEvent ? JSON.parse(e.data) : {};
        const event: StreamEvent = { type: 'error', data, timestamp: new Date() };
        onEvent?.(event);
      });

      es.onerror = () => {
        setIsConnected(false);
        es.close();

        if (reconnectAttempts.current < maxReconnectAttempts) {
          reconnectAttempts.current += 1;
          const delay = reconnectInterval * Math.pow(1.5, reconnectAttempts.current - 1);
          reconnectTimer.current = setTimeout(connect, delay);
        } else {
          setError('Connection lost. Please refresh the page.');
        }
      };
    } catch (err) {
      setError('Failed to connect to event stream');
    }
  }, [enabled, onEvent, reconnectInterval, maxReconnectAttempts]);

  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current);
    }
    setIsConnected(false);
  }, []);

  useEffect(() => {
    if (enabled) {
      connect();
    }
    return () => disconnect();
  }, [enabled, connect, disconnect]);

  return {
    isConnected,
    events,
    error,
    reconnect: connect,
    disconnect,
  };
}
