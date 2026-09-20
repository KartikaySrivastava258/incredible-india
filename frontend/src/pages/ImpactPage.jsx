import React, { useCallback, useEffect, useState } from 'react';
import { api, ApiError } from '../api';
import ImpactStats from '../components/ledger/ImpactStats';
import ErrorState from '../components/common/ErrorState';
import LoadingSpinner from '../components/common/LoadingSpinner';

const POLL_INTERVAL_MS = 5000;

export default function ImpactPage() {
  const [impact, setImpact] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    if (document.hidden) return;
    setError(null);
    try {
      const data = await api.getImpact();
      setImpact(data);
    } catch (err) {
      setError(err instanceof ApiError ? err : new ApiError({ message: String(err) }));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    // SALONI_BATRA_TASK.md 5.5: "must reflect real backend data, updating
    // live as sales are simulated." A short poll keeps this true without
    // needing a websocket the backend doesn't offer.
    const id = setInterval(load, POLL_INTERVAL_MS);
    // Pause when tab is hidden; resume on visibility restore.
    const onVisibility = () => { if (!document.hidden) load(); };
    document.addEventListener('visibilitychange', onVisibility);
    return () => {
      clearInterval(id);
      document.removeEventListener('visibilitychange', onVisibility);
    };
  }, [load]);

  return (
    <div>
      <h1>Community impact</h1>
      <p>What Kalaa Setu has made possible so far, across every village.</p>
      {loading && <LoadingSpinner label="Loading impact data…" />}
      {error && <ErrorState error={error} onRetry={load} />}
      {impact && !loading && <ImpactStats impact={impact} />}
    </div>
  );
}

