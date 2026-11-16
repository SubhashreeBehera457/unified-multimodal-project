import { useState, useEffect, useCallback } from 'react';
import { SystemHealthData } from '../types';
import { api } from '../services/api';

export function useSystemHealth() {
  const [health, setHealth] = useState<SystemHealthData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHealth = useCallback(async () => {
    try {
      const data = await api.getSystemHealth();
      setHealth(data);
      setError(null);
      setLoading(false);
      return data;
    } catch (err: any) {
      console.warn('Health check notice:', err.message);
      setError(err.message);
      setLoading(false);
      return null;
    }
  }, []);

  useEffect(() => {
    fetchHealth();
    // Poll every 25 seconds
    const interval = setInterval(fetchHealth, 25000);
    return () => clearInterval(interval);
  }, [fetchHealth]);

  return {
    health,
    loading,
    error,
    refreshHealth: fetchHealth,
  };
}
