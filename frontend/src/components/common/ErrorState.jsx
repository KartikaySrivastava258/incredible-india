import React from 'react';

/**
 * Renders any ApiError as a clear, actionable panel — never a blank
 * screen, never raw error JSON. Satisfies the 502 "AI is temporarily
 * unavailable" requirement (SALONI_BATRA_TASK.md 5.1) generically for
 * every endpoint (5.2's 403 handling, and 400/404 elsewhere).
 */
export default function ErrorState({ error, onRetry, title }) {
  if (!error) return null;
  const heading = title || (error.isUpstreamUnavailable ? 'AI is temporarily unavailable' : 'Something went wrong');
  return (
    <div className={`state-panel is-error${error.isForbidden ? ' is-forbidden' : ''}`} role="alert">
      <h3>{error.isForbidden ? 'Blocked by policy' : heading}</h3>
      <p style={{ margin: 0 }}>{error.friendlyMessage ? error.friendlyMessage() : 'Please try again.'}</p>
      {error.isForbidden && error.details?.policy && (
        <p className="hint" style={{ marginTop: '.5rem' }}>Policy: <code>{error.details.policy}</code></p>
      )}
      {onRetry && (
        <button type="button" className="btn btn-ghost" style={{ marginTop: '0.9rem' }} onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  );
}

