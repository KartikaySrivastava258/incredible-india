import React, { useState } from 'react';
import { api, ApiError } from '../../api';
import ErrorState from '../common/ErrorState';
import LoadingSpinner from '../common/LoadingSpinner';

const LANGUAGES = [
  { code: 'hi', label: 'हिन्दी (Hindi)' },
  { code: 'en', label: 'English' }
];

/**
 * SALONI_BATRA_TASK.md 5.1: "Seller picks a language (start with
 * Hindi)". A seller_id is required before the first POST
 * /onboarding/message call, so this form calls POST /sellers first —
 * BRAIN.md Section G lists it as a backend endpoint and Section 8 of
 * the task file lists it as one the frontend consumes.
 */
export default function SellerSetupForm({ onRegistered }) {
  const [form, setForm] = useState({
    name: '',
    village: '',
    state: '',
    seller_language: 'hi',
    phone: '',
    touchpoint_id: '11111111-1111-4111-8111-111111111111'
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showAdvanced, setShowAdvanced] = useState(false);

  function update(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const seller = await api.createSeller({
        name: form.name.trim(),
        village: form.village.trim(),
        state: form.state.trim(),
        seller_language: form.seller_language,
        phone: form.phone.trim() || undefined,
        touchpoint_id: form.touchpoint_id.trim()
      });
      onRegistered(seller);
    } catch (err) {
      setError(err instanceof ApiError ? err : new ApiError({ message: String(err) }));
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className="card seller-setup-form" onSubmit={handleSubmit}>
      <h2>Before we start</h2>
      <p className="hint">A few details so your listing and pickup can be arranged.</p>

      <div className="field">
        <label htmlFor="seller-language">Language</label>
        <select id="seller-language" value={form.seller_language} onChange={(e) => update('seller_language', e.target.value)}>
          {LANGUAGES.map((l) => (
            <option key={l.code} value={l.code}>
              {l.label}
            </option>
          ))}
        </select>
      </div>

      <div className="field">
        <label htmlFor="seller-name">Name</label>
        <input
          id="seller-name"
          type="text"
          required
          autoComplete="name"
          value={form.name}
          onChange={(e) => update('name', e.target.value)}
        />
      </div>

      <div className="field">
        <label htmlFor="seller-village">Village</label>
        <input
          id="seller-village"
          type="text"
          required
          autoComplete="address-level2"
          value={form.village}
          onChange={(e) => update('village', e.target.value)}
        />
      </div>

      <div className="field">
        <label htmlFor="seller-state">State</label>
        <input
          id="seller-state"
          type="text"
          required
          autoComplete="address-level1"
          value={form.state}
          onChange={(e) => update('state', e.target.value)}
        />
      </div>

      <div className="field">
        <label htmlFor="seller-phone">Phone (optional)</label>
        <input
          id="seller-phone"
          type="tel"
          inputMode="tel"
          autoComplete="tel"
          value={form.phone}
          onChange={(e) => update('phone', e.target.value)}
        />
      </div>

      <details className="advanced-section" onToggle={(e) => setShowAdvanced(e.target.open)}>
        <summary className="advanced-section__toggle">Advanced</summary>
        <div className="field">
          <label htmlFor="seller-touchpoint">Touchpoint ID (your school/CSC)</label>
          <input
            id="seller-touchpoint"
            type="text"
            required
            value={form.touchpoint_id}
            onChange={(e) => update('touchpoint_id', e.target.value)}
          />
          <span className="hint">Pre-filled with the demo touchpoint. A real kiosk would already know this.</span>
        </div>
      </details>

      <button type="submit" className="btn btn-primary" disabled={loading}>
        Start onboarding
      </button>

      {loading && <LoadingSpinner label="Registering…" />}
      {error && <ErrorState error={error} onRetry={handleSubmit} />}
    </form>
  );
}

