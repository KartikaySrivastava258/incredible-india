import React, { useCallback, useEffect, useState } from 'react';
import { api, ApiError } from '../api';
import { session } from '../session';
import LedgerTable from '../components/ledger/LedgerTable';
import ErrorState from '../components/common/ErrorState';
import LoadingSpinner from '../components/common/LoadingSpinner';
import EmptyState from '../components/common/EmptyState';

export default function LedgerPage() {
  const [seller] = useState(() => session.get().seller || null);
  const [entries, setEntries] = useState(null);
  const [loading, setLoading] = useState(Boolean(seller));
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    if (!seller) return;
    setLoading(true);
    setError(null);
    try {
      const data = await api.getLedger(seller.seller_id);
      setEntries(data);
    } catch (err) {
      setError(err instanceof ApiError ? err : new ApiError({ message: String(err) }));
    } finally {
      setLoading(false);
    }
  }, [seller]);

  useEffect(() => {
    load();
  }, [load]);

  if (!seller) {
    return (
      <EmptyState title="No seller session yet">
        Complete seller onboarding first so we know whose ledger to show.
      </EmptyState>
    );
  }

  return (
    <div>
      <h1>Your ledger</h1>
      <p className="hint">Every sale and every community contribution, visible to you by default.</p>
      {loading && <LoadingSpinner label="Loading ledger…" />}
      {error && <ErrorState error={error} onRetry={load} />}
      {entries && !loading && !error && <LedgerTable entries={entries} />}
    </div>
  );
}

