// @ts-nocheck
import React from 'react';

export default function LoadingSpinner({ label = 'Loading…' }) {
  return (
    <div className="loading-row" role="status" aria-live="polite">
      <span className="craft-loader" aria-hidden="true"><span /><i /><b /></span>
      <span>{label}</span>
    </div>
  );
}
