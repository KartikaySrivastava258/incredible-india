import React from 'react';

export default function EmptyState({ title, children }) {
  return (
    <div className="state-panel is-empty">
      <h3>{title}</h3>
      {children && <div>{children}</div>}
    </div>
  );
}

