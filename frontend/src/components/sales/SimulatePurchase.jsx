import React, { useState } from 'react';
import { api, ApiError } from '../../api';
import ErrorState from '../common/ErrorState';
import LoadingSpinner from '../common/LoadingSpinner';

/**
 * SALONI_BATRA_TASK.md 5.4: a "simulate purchase" action that calls
 * POST /sales with a sale amount, then shows a confirmation with the
 * computed split (seller_net, contribution_amount if any).
 */
export default function SimulatePurchase({ listingId, priceSuggestion, onSaleComplete }) {
  const [amount, setAmount] = useState(priceSuggestion || 0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [entry, setEntry] = useState(null);

  async function handleSimulate(e) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const created = await api.simulateSale({ listing_id: listingId, sale_amount: Number(amount) });
      setEntry(created);
      if (onSaleComplete) onSaleComplete(created);
    } catch (err) {
      setError(err instanceof ApiError ? err : new ApiError({ message: String(err) }));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card">
      <h3>Simulate a purchase</h3>
      <form onSubmit={handleSimulate}>
        <div className="field">
          <label htmlFor="sale-amount">Sale amount (INR)</label>
          <input
            id="sale-amount"
            type="number"
            min="1"
            step="1"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            required
          />
        </div>
        <button type="submit" className="btn btn-accent" disabled={loading || !amount || Number(amount) <= 0}>
          Simulate purchase
        </button>
      </form>

      {loading && <LoadingSpinner label="Processing sale…" />}
      {error && <ErrorState error={error} onRetry={handleSimulate} />}

      {entry && !loading && !error && (
        <div className="card" style={{ marginTop: '1rem', background: 'var(--indigo-tint)' }} role="status">
          <h3 style={{ marginBottom: '0.5rem' }}>Sale confirmed</h3>
          <p style={{ margin: '0 0 0.3rem' }}>Sale amount: ₹{entry.sale_amount.toLocaleString('en-IN')}</p>
          <p style={{ margin: '0 0 0.3rem' }}>Platform fee: ₹{entry.platform_fee.toLocaleString('en-IN')}</p>
          <p style={{ margin: '0 0 0.3rem' }}>
            <strong>Seller net: ₹{entry.seller_net.toLocaleString('en-IN')}</strong>
          </p>
          <p style={{ margin: 0 }}>
            Community contribution:{' '}
            {entry.contribution_amount > 0
              ? `₹${entry.contribution_amount.toLocaleString('en-IN')}`
              : '₹0 (seller has not opted in)'}
          </p>
        </div>
      )}
    </div>
  );
}

