import { useState, useEffect, useCallback, useRef } from 'react';

interface UseApiOptions {
  autoRefresh?: number; // ms interval
}

interface UseApiResult<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useApi<T>(
  fetcher: () => Promise<T>,
  _mockFetcher: () => T,
  deps: unknown[] = [],
  options: UseApiOptions = {}
): UseApiResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchData = useCallback(async () => {
    console.log('[useApi] Fetching data...');
    setLoading(true);
    setError(null);
    try {
      // Always use real API
      const result = await fetcher();
      console.log('[useApi] API success:', result);
      setData(result);
    } catch (apiError) {
      console.error('[useApi] API error:', apiError);
      // Show error to user - no mock fallback
      setError(apiError instanceof Error ? apiError.message : 'Failed to fetch data');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [...deps]);

  useEffect(() => {
    fetchData();
    if (options.autoRefresh) {
      intervalRef.current = setInterval(fetchData, options.autoRefresh);
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [fetchData, options.autoRefresh]);

  return { data, loading, error, refetch: fetchData };
}
