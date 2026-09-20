import React from 'react';

const STATS = [
  { key: 'villages_onboarded', label: 'Villages onboarded' },
  { key: 'sellers_earning', label: 'Sellers earning' },
  { key: 'opt_in_rate', label: 'Opt-in rate', format: (v) => `${Math.round((v || 0) * 100)}%` },
  { key: 'total_community_funds', label: 'Community funds generated', format: (v) => `₹${(v || 0).toLocaleString('en-IN')}` }
];

export default function ImpactStats({ impact }) {
  if (!impact) return null;
  return (
    <div className="impact-grid">
      {STATS.map((s) => (
        <div className="impact-stat" key={s.key}>
          <span className="value">{s.format ? s.format(impact[s.key]) : impact[s.key] ?? '—'}</span>
          <span className="label">{s.label}</span>
        </div>
      ))}
    </div>
  );
}

