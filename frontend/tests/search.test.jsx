import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import BuyerSearchPage from '../src/pages/BuyerSearchPage';

vi.mock('../src/api', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    api: {
      searchMatch: vi.fn()
    }
  };
});

import { api, ApiError } from '../src/api';

function renderPage() {
  return render(
    <MemoryRouter>
      <BuyerSearchPage />
    </MemoryRouter>
  );
}

describe('Buyer search', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders ranked results', async () => {
    const user = userEvent.setup();
    api.searchMatch.mockResolvedValue({
      matches: [
        { listing_id: 'l-1', score: 0.9, listing_title: 'Handwoven Wool Shawl', noble_cause_note: 'Supports a local school.' },
        { listing_id: 'l-2', score: 0.4, listing_title: 'Wooden Toy Set', noble_cause_note: null }
      ]
    });

    renderPage();
    await user.type(screen.getByRole('searchbox', { name: /search for a product/i }), 'shawl');
    await user.click(screen.getByRole('button', { name: /search/i }));

    await waitFor(() => expect(screen.getByText('Handwoven Wool Shawl')).toBeInTheDocument());
    expect(screen.getByText('Wooden Toy Set')).toBeInTheDocument();
    expect(screen.getByText('Community-supporting')).toBeInTheDocument();
  });

  it('shows a friendly empty state, not a crash, for zero results', async () => {
    const user = userEvent.setup();
    api.searchMatch.mockResolvedValue({ matches: [] });

    renderPage();
    await user.type(screen.getByRole('searchbox', { name: /search for a product/i }), 'nonexistent thing');
    await user.click(screen.getByRole('button', { name: /search/i }));

    await waitFor(() => expect(screen.getByText(/no matches yet/i)).toBeInTheDocument());
    expect(screen.getByText(/nonexistent thing/)).toBeInTheDocument();
  });

  it('handles a 502 from the matching service gracefully', async () => {
    const user = userEvent.setup();
    api.searchMatch.mockRejectedValue(new ApiError({ status: 502, code: 'UPSTREAM_UNAVAILABLE', message: 'down' }));

    renderPage();
    await user.type(screen.getByRole('searchbox', { name: /search for a product/i }), 'shawl');
    await user.click(screen.getByRole('button', { name: /search/i }));

    await waitFor(() =>
  expect(screen.getByRole('alert')).toHaveTextContent(/AI is temporarily unavailable/i)
);
    expect(screen.queryByText(/UPSTREAM_UNAVAILABLE/)).not.toBeInTheDocument();
  });
});
