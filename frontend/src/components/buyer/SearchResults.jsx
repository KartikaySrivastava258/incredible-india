import React from 'react';
import { Link } from 'react-router-dom';
import Badge from '../common/Badge';
import EmptyState from '../common/EmptyState';

/**
 * SALONI_BATRA_TASK.md 5.3: shows ranked results (listing_title; score
 * can be omitted or shown subtly). Empty results -> friendly empty
 * state, not a crash.
 */
export default function SearchResults({ matches, query }) {
  if (matches.length === 0) {
    return (
      <EmptyState title="No matches yet">
        <p style={{ margin: 0 }}>
          Nothing matched "{query}". Try a different word, or a broader category like "textile" or "toy".
        </p>
      </EmptyState>
    );
  }

  return (
    <div className="results-grid">
      {matches.map((m) => (
        <Link key={m.listing_id} to={`/listings/${m.listing_id}`} className="result-card">
          <div className="result-card__thumb" aria-hidden="true" />
          <div className="result-card__body">
            <h3>{m.listing_title}</h3>
            {typeof m.score === 'number' && (
              <span className="hint">Match score: {Math.round(m.score * 100)}%</span>
            )}
            {m.noble_cause_note && (
              <div style={{ marginTop: '0.5rem' }}>
                <Badge variant="noble">Community-supporting</Badge>
              </div>
            )}
          </div>
        </Link>
      ))}
    </div>
  );
}

