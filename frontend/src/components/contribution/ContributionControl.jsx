import React, { useState } from 'react';
import { api, ApiError } from '../../api';
import ErrorState from '../common/ErrorState';
import LoadingSpinner from '../common/LoadingSpinner';

/**
 * SALONI_BATRA_TASK.md 5.2: "a clear opt-in toggle + percentage slider
 * that calls POST /contributions. Make it obvious this is optional and
 * off by default." Edge case: backend 403s -> show a clear error, don't
 * fail silently.
 */
export default function ContributionControl({ sellerId, touchpointId, onSaved }) {
  const [optedIn, setOptedIn] = useState(false);
  const [percentage, setPercentage] = useState(10);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [saved, setSaved] = useState(null);

  async function save(nextOptedIn, nextPercentage) {
    setSaving(true);
    setError(null);
    try {
      const record = await api.setContribution({
        seller_id: sellerId,
        opted_in: nextOptedIn,
        percentage: nextPercentage,
        touchpoint_id: touchpointId
      });
      setSaved(record);
      if (onSaved) onSaved(record);
    } catch (err) {
      setError(err instanceof ApiError ? err : new ApiError({ message: String(err) }));
    } finally {
      setSaving(false);
    }
  }

  function handleToggle(e) {
    const next = e.target.checked;
    setOptedIn(next);
    save(next, percentage);
  }

  function handleSliderCommit(e) {
    const next = Number(e.target.value);
    setPercentage(next);
    if (optedIn) save(true, next);
  }

  return (
    <div className="card contribution-control">
      <h3 style={{ marginBottom: 0 }}>Community contribution</h3>
      <p className="hint" style={{ margin: 0 }}>
        Entirely optional, entirely your choice. Off by default. If you opt in, a percentage of{' '}
        <strong>your own net proceeds</strong> goes to your school/CSC's development fund — never platform-imposed,
        and always visible to you on your ledger.
      </p>

      <div className="toggle-row">
        <label htmlFor="contribution-toggle" style={{ fontWeight: 600 }}>
          Route a share of my proceeds
        </label>
        <span className="toggle">
          <input
            id="contribution-toggle"
            type="checkbox"
            checked={optedIn}
            disabled={saving}
            onChange={handleToggle}
            aria-label="Opt in to community contribution"
          />
          <span className="track" aria-hidden="true" />
          <span className="knob" aria-hidden="true" />
        </span>
      </div>

      {optedIn && (
        <div className="slider-row">
          <label htmlFor="contribution-percentage">Percentage of net proceeds: {percentage}%</label>
          <input
            id="contribution-percentage"
            type="range"
            min={0}
            max={100}
            step={1}
            value={percentage}
            disabled={saving}
            onChange={(e) => setPercentage(Number(e.target.value))}
            onMouseUp={handleSliderCommit}
            onTouchEnd={handleSliderCommit}
            onKeyUp={handleSliderCommit}
          />
        </div>
      )}

      {saving && <LoadingSpinner label="Saving your choice…" />}
      {error && <ErrorState error={error} onRetry={() => save(optedIn, percentage)} />}
      {saved && !saving && !error && (
        <p className="hint" style={{ margin: 0 }}>
          Saved: {saved.opted_in ? `opted in at ${saved.percentage}%` : 'not opted in'}.
        </p>
      )}
    </div>
  );
}

