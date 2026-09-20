import React from 'react';

export const STAGES = [
  { key: 'idea', label: 'Idea' },
  { key: 'procedure', label: 'Procedure' },
  { key: 'business_model', label: 'Business model' },
  { key: 'capture', label: 'Capture' },
  { key: 'done', label: 'Draft ready' }
];

/**
 * SALONI_BATRA_TASK.md 5.1: "show the current stage subtly (e.g. a small
 * progress indicator: idea -> procedure -> business model -> capture)".
 * This is a genuine sequence (the conversation really does move through
 * these stages in order), so a stepped rail is the right structural
 * device here — not decoration.
 */
export default function StageProgress({ stage }) {
  const currentIndex = STAGES.findIndex((s) => s.key === stage);
  return (
    <nav className="stage-rail" aria-label="Onboarding progress">
      {STAGES.map((s, i) => {
        const isComplete = currentIndex > i || stage === 'done';
        const isCurrent = s.key === stage;
        const cls = ['stage-rail__item', isComplete ? 'is-complete' : '', isCurrent ? 'is-current' : '']
          .filter(Boolean)
          .join(' ');
        return (
          <div key={s.key} className={cls} aria-current={isCurrent ? 'step' : undefined}>
            <span className="stage-rail__node" aria-hidden="true" />
            {s.label}
          </div>
        );
      })}
    </nav>
  );
}

