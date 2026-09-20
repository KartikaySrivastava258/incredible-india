import React, { useState } from 'react';
import TouchpointAdminView from '../components/admin/TouchpointAdminView';
import ErrorState from '../components/common/ErrorState';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { api, ApiError } from '../api';

export default function AdminPage() {
  const [touchpointId, setTouchpointId] = useState('11111111-1111-4111-8111-111111111111');
  const [active, setActive] = useState('11111111-1111-4111-8111-111111111111');
  const [sellerId, setSellerId] = useState('');
  const [ledger, setLedger] = useState(null);
  const [ledgerError, setLedgerError] = useState(null);
  const [ledgerLoading, setLedgerLoading] = useState(false);

  async function lookupLedger(e) {
    e.preventDefault();
    if (!sellerId.trim() || !active) return;
    setLedgerLoading(true);
    setLedgerError(null);
    setLedger(null);
    try {
      setLedger(await api.getLedgerAsAdmin(sellerId.trim(), active));
    } catch (err) {
      setLedgerError(err instanceof ApiError ? err : new ApiError({ message: String(err) }));
    } finally {
      setLedgerLoading(false);
    }
  }

  return (
    <div>
      <h1>Touchpoint admin</h1>
      <p className="hint">Choose a touchpoint. Impact totals below are global aggregates because GET /impact is not currently Cedar-scoped.</p>

      <form className="card" style={{ maxWidth: 520, marginBottom: '1.5rem' }} onSubmit={(e) => { e.preventDefault(); setActive(touchpointId.trim()); }}>
        <div className="field">
          <label htmlFor="admin-touchpoint">Touchpoint ID</label>
          <input id="admin-touchpoint" type="text" value={touchpointId} onChange={(e) => setTouchpointId(e.target.value)} />
        </div>
        <button type="submit" className="btn btn-primary">View dashboard</button>
      </form>

      {active && <TouchpointAdminView touchpointId={active} />}

      <section className="card" style={{ marginTop: '1.5rem' }}>
        <h2>Look up a seller's ledger</h2>
        <p className="hint">This lookup uses the active touchpoint admin principal and is enforced by Cedar.</p>
        <form onSubmit={lookupLedger}>
          <div className="field">
            <label htmlFor="admin-seller">Seller ID</label>
            <input id="admin-seller" type="text" value={sellerId} onChange={(e) => setSellerId(e.target.value)} placeholder="Seller UUID" />
          </div>
          <button type="submit" className="btn btn-primary" disabled={!sellerId.trim() || ledgerLoading}>Look up ledger</button>
        </form>
        {ledgerLoading && <LoadingSpinner label="Checking Cedar policy…" />}
        {ledgerError && <ErrorState error={ledgerError} />}
        {ledger && (
          <div role="status" style={{ marginTop: '1rem' }}>
            <strong>Allowed by Cedar.</strong> {ledger.entries?.length || 0} ledger entr{ledger.entries?.length === 1 ? 'y' : 'ies'} found.
          </div>
        )}
      </section>
    </div>
  );
}
