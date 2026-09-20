import React, { useEffect, useState } from 'react';
import { api, ApiError } from '../../api';
import ErrorState from '../common/ErrorState';
import LoadingSpinner from '../common/LoadingSpinner';
import ImpactStats from '../ledger/ImpactStats';

/**
 * SALONI_BATRA_TASK.md 5.6 (STRETCH): "A simple view for a school/CSC
 * admin limited to their own village's data (backend already
 * Cedar-scopes this — you just need to pass the right principal and
 * render the filtered response)."
 *
 * BRAIN.md Section G does not define a dedicated touchpoint-scoped
 * endpoint, so this reuses GET /impact and passes the admin's
 * touchpoint as a request header (X-Principal-Touchpoint-Id) for the
 * backend's Cedar layer to scope by, rather than inventing a new
 * endpoint or field name. This assumption is called out explicitly in
 * integration-notes.md for Dipanshu to confirm/adjust.
 */
export default function TouchpointAdminView({ touchpointId }) {
  const [impact, setImpact] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getImpact({ principalTouchpointId: touchpointId });
      setImpact(data);
    } catch (err) {
      setError(err instanceof ApiError ? err : new ApiError({ message: String(err) }));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [touchpointId]);

  return (
    <div>
      <h2>Touchpoint dashboard</h2>
      <p className="hint">Impact totals are global aggregates; this endpoint is not currently Cedar-scoped. Use the seller ledger lookup below for a Cedar-enforced check.</p>
      {loading && <LoadingSpinner label="Loading touchpoint data…" />}
      {error && <ErrorState error={error} onRetry={load} />}
      {!loading && !error && <ImpactStats impact={impact} />}
    </div>
  );
}

