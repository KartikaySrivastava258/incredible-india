// A minimal client-side session so a seller/buyer can move between pages
// (and refresh the browser) during a demo without losing their place.
// This is purely a frontend convenience — the backend remains the only
// source of truth for persisted data (BRAIN.md Section C).
const KEY = 'kalaa_setu_session_v1';

function read() {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

function write(next) {
  try {
    localStorage.setItem(KEY, JSON.stringify(next));
  } catch {
    // Storage unavailable (private browsing, quota) — fail silently,
    // the app still works, it just won't survive a refresh.
  }
}

export const session = {
  get() {
    return read();
  },
  set(patch) {
    const next = { ...read(), ...patch };
    write(next);
    return next;
  },
  clear() {
    write({});
  }
};

