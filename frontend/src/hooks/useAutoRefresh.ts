import { useCallback, useEffect, useRef, useState } from "react";

export function useAutoRefresh<T>(
    fetcher: () => Promise<T>,
    intervalMs: number = 15000,
    enabled: boolean = true,
) {
    const [data, setData] = useState<T | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
    const fetcherRef = useRef(fetcher);
    fetcherRef.current = fetcher;

    const refresh = useCallback(async () => {
        try {
            const result = await fetcherRef.current();
            setData(result);
            setError(null);
            setLastRefresh(new Date());
        } catch (e) {
            setError(e instanceof Error ? e.message : "Failed to load");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        if (!enabled) return;
        refresh();
        const id = setInterval(refresh, intervalMs);
        return () => clearInterval(id);
    }, [refresh, intervalMs, enabled]);

    return { data, loading, error, lastRefresh, refresh };
}
