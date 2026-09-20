import React, { useState } from 'react';
import TouchpointAdminView from '../components/admin/TouchpointAdminView';

/**
 * SALONI_BATRA_TASK.md 5.6 (STRETCH — only if MUST items are solid).
 * A real deployment would derive the touchpoint id from the logged-in
 * admin's session; there is no auth system in scope here, so this page
 * simply asks for it. See TouchpointAdminView for the Cedar-scoping note.
 */
export default function AdminPage() {
  const [touchpointId, setTouchpointId] = useState('11111111-1111-4111-8111-111111111111');
  const [active, setActive] = useState('11111111-1111-4111-8111-111111111111');

  return (
    <div>
      <h1>Touchpoint admin</h1>
      <p className="hint">School/CSC admin view, scoped to one touchpoint's own data.</p>

      <form
        className="card"
        style={{ maxWidth: 420, marginBottom: '1.5rem' }}
        onSubmit={(e) => {
          e.preventDefault();
          setActive(touchpointId.trim());
        }}
      >
        <div className="field">
          <label htmlFor="admin-touchpoint">Touchpoint ID</label>
          <input id="admin-touchpoint" type="text" value={touchpointId} onChange={(e) => setTouchpointId(e.target.value)} />
        </div>
        <button type="submit" className="btn btn-primary">
          View dashboard
        </button>
      </form>

      {active && <TouchpointAdminView touchpointId={active} />}
    </div>
  );
}

