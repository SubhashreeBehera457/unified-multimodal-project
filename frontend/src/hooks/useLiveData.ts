import { useState, useEffect, useCallback, useRef } from 'react';
import { DashboardData } from '../types';
import { api } from '../services/api';

export type ConnectionState = 'LIVE CONNECTION' | 'RECONNECTING' | 'OFFLINE';

export function useLiveData() {
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionState>('CONNECTING' as any);
  const [lastSync, setLastSync] = useState<string>('--:--:--');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<any>(null);

  const fetchDashboard = useCallback(async () => {
    try {
      const data = await api.getDashboard();
      setDashboard(data);
      setLastSync(data.last_synced || new Date().toLocaleTimeString());
      setError(null);
      setLoading(false);
      return data;
    } catch (err: any) {
      console.warn('Dashboard fetch notice:', err.message);
      setError(err.message);
      setLoading(false);
      return null;
    }
  }, []);

  // Connect WebSocket
  useEffect(() => {
    let isMounted = true;

    function connectWs() {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/live`;

      try {
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          if (!isMounted) return;
          setConnectionStatus('LIVE CONNECTION');
          // Immediately fetch fresh dashboard
          fetchDashboard();
        };

        ws.onmessage = (event) => {
          if (!isMounted) return;
          try {
            const data = JSON.parse(event.data);
            if (data.type === 'TELEMETRY_PULSE') {
              setLastSync(data.timestamp || new Date().toLocaleTimeString());
              setDashboard((prev) => {
                if (!prev) return prev;
                return {
                  ...prev,
                  kpis: data.kpis || prev.kpis,
                  timeline: data.latest_events ? [...data.latest_events, ...prev.timeline].slice(0, 15) : prev.timeline,
                  last_synced: data.timestamp,
                };
              });
            }
          } catch {
            // ignore non-json
          }
        };

        ws.onclose = () => {
          if (!isMounted) return;
          setConnectionStatus('RECONNECTING');
          reconnectTimeoutRef.current = setTimeout(connectWs, 5000);
        };

        ws.onerror = () => {
          if (!isMounted) return;
          setConnectionStatus('OFFLINE');
          ws.close();
        };
      } catch {
        setConnectionStatus('OFFLINE');
      }
    }

    // Initial load
    fetchDashboard().then(() => {
      connectWs();
    });

    // Periodic background sync fallback every 15s
    const pollInterval = setInterval(() => {
      fetchDashboard();
    }, 15000);

    return () => {
      isMounted = false;
      clearInterval(pollInterval);
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, [fetchDashboard]);

  const refreshNow = useCallback(() => {
    setLoading(true);
    fetchDashboard();
  }, [fetchDashboard]);

  return {
    dashboard,
    connectionStatus,
    lastSync,
    loading,
    error,
    refreshNow,
  };
}
