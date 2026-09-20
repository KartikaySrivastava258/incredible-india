import React from 'react';

const STAGES = [
  { key: 'searching', label: 'Searching' },
  { key: 'matching', label: 'Matching demand' },
  { key: 'results', label: 'Results' }
];

/**
 * A small staged sequence so a semantic-match search visibly "thinks"
 * rather than just spinning: searching -> matching -> results. Purely
 * a loading-state affordance — the matches themselves always come from
 * the real POST /search/match response.
 */
export default function SearchStageIndicator({ phase }) {
  const activeIndex = STAGES.findIndex((s) => s.key === phase);
  return (
    <div className="search-stage" role="status" aria-live="polite">
      {STAGES.map((s, i) => {
        const isDone = activeIndex > i;
        const isActive = activeIndex === i;
        const cls = ['search-stage__step', isDone ? 'is-done' : '', isActive ? 'is-active' : ''].filter(Boolean).join(' ');
        return (
          <span key={s.key} className={cls}>
            <span className="search-stage__dot" aria-hidden="true" />
            {s.label}
          </span>
        );
      })}
    </div>
  );
}
