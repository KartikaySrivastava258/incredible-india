import React from 'react';
import Badge from '../common/Badge';

/**
 * SALONI_BATRA_TASK.md 5.3: "only when the backend returns a non-null
 * noble_cause_note, the noble-cause note, visually distinct". Parent is
 * responsible for the null check (this component simply never renders
 * a placeholder), but we guard here too as a safety net so no caller can
 * accidentally imply every seller contributes.
 */
export default function NobleCauseBadge({ note }) {
  if (!note) return null;
  return (
    <div className="noble-cause-callout">
      <Badge variant="noble">Community-supporting purchase</Badge>
      <p style={{ margin: 0 }}>{note}</p>
    </div>
  );
}

