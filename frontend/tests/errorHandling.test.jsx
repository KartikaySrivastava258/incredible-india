import React from 'react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import LedgerPage from '../src/pages/LedgerPage';
import ImpactPage from '../src/pages/ImpactPage';
import { session } from '../src/session';

vi.mock('../src/api', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    api: {
      getLedger: vi.fn(),
      getImpact: vi.fn()
    }
  };
});

import { api, ApiError } from '../src/api';

describe('Error handling across other endpoints', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('LedgerPage shows a clear message, not raw JSON, on a 403', async () => {
    session.set({ seller: { seller_id: 'seller-1', name: 'Meena', touchpoint_id: 't-001' } });
    api.getLedger.mockRejectedValue(new ApiError({ status: 403, code: 'CEDAR_DENIED', message: 'denied' }));

    render(
      <MemoryRouter>
        <LedgerPage />
      </MemoryRouter>
    );

    await waitFor(() => expect(screen.getByRole('alert')).toBeInTheDocument());
    expect(screen.getByText(/don't have permission/i)).toBeInTheDocument();
    expect(screen.queryByText(/CEDAR_DENIED/)).not.toBeInTheDocument();
  });

  it('ImpactPage shows a clear message, not raw JSON, on a 502', async () => {
    api.getImpact.mockRejectedValue(new ApiError({ status: 502, code: 'UPSTREAM_UNAVAILABLE', message: 'down' }));

    render(
      <MemoryRouter>
        <ImpactPage />
      </MemoryRouter>
    );

    await waitFor(() => expect(screen.getByRole('alert')).toBeInTheDocument());
    expect(screen.getByRole('alert')).toHaveTextContent(/AI is temporarily unavailable/i);
    expect(screen.queryByText(/UPSTREAM_UNAVAILABLE/)).not.toBeInTheDocument();
  });
});
