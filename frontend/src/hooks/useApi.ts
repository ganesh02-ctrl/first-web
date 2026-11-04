import { DependencyList, useCallback, useEffect, useState } from "react";
import { errorMessage } from "../services/api";

/** Loads data on mount / when deps change. Returns data, loading, error, reload. */
export function useApi<T>(loader: () => Promise<T>, deps: DependencyList = []) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const run = useCallback(loader, deps);
  const reload = useCallback(async () => {
    setLoading(true); setError(null);
    try { setData(await run()); } catch (e) { setError(errorMessage(e)); } finally { setLoading(false); }
  }, [run]);
  useEffect(() => { reload(); }, [reload]);
  return { data, loading, error, reload, setData };
}
