/**
 * WebSocket hook for real-time alerts
 * Replaces polling with WebSocket connection for instant alert delivery
 */
import { useEffect, useState, useCallback, useRef } from 'react';
import { apiLogger } from '../utils/logger';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/';

export interface WebSocketAlert {
  id?: number;
  message: string;
  alert_message: string;
  severity: string;
  alert_level: string;
  device_id?: number;
  device_hostname?: string;
  device_ip?: string;
  device_mac?: string;
  timestamp: string;
}

interface UseAlertWebSocketOptions {
  onAlert?: (alert: WebSocketAlert) => void;
  reconnectInterval?: number;
}

export function useAlertWebSocket(options: UseAlertWebSocketOptions = {}) {
  const { onAlert, reconnectInterval = 5000 } = options;
  const [isConnected, setIsConnected] = useState(false);
  const [lastAlert, setLastAlert] = useState<WebSocketAlert | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const connect = useCallback(() => {
    // Build WebSocket URL
    // For nginx proxy (VITE_API_BASE_URL = "/"), use current host's ws protocol
    // For direct backend access, use ws://localhost
    let wsProtocol = 'ws:';
    let wsHost = window.location.host;

    // If API_BASE_URL is a full URL, extract protocol and host
    if (API_BASE_URL.startsWith('http')) {
      wsProtocol = API_BASE_URL.replace(/^http/, 'ws');
      try {
        const url = new URL(API_BASE_URL);
        wsHost = url.host;
      } catch (e) {
        // Use default
      }
    }

    const wsUrl = `${wsProtocol}//${wsHost}/ws/alerts`;
    apiLogger.info('[WS] Connecting to:', wsUrl);

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        apiLogger.info('[WS] Connected to alerts WebSocket');
        setIsConnected(true);

        // Clear any reconnect timeout
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
          reconnectTimeoutRef.current = null;
        }
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          apiLogger.info('[WS] Received alert:', data);

          if (data.type === 'new_alert' && data.data) {
            const alert = data.data as WebSocketAlert;
            setLastAlert(alert);
            onAlert?.(alert);
          }
        } catch (e) {
          apiLogger.error('[WS] Failed to parse message:', e);
        }
      };

      ws.onclose = () => {
        apiLogger.info('[WS] Connection closed');
        setIsConnected(false);
        wsRef.current = null;

        // Attempt to reconnect
        reconnectTimeoutRef.current = setTimeout(() => {
          apiLogger.info('[WS] Attempting to reconnect...');
          connect();
        }, reconnectInterval);
      };

      ws.onerror = (error) => {
        apiLogger.error('[WS] Error:', error);
      };
    } catch (e) {
      apiLogger.error('[WS] Failed to create WebSocket:', e);
    }
  }, [onAlert, reconnectInterval]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
  }, []);

  // Connect on mount, disconnect on unmount
  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected,
    lastAlert,
    connect,
    disconnect,
  };
}
