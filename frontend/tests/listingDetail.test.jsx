import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import ListingDetailPage from '../src/pages/ListingDetailPage';

vi.mock('../src/api', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    api: {
      getListing: vi.fn()
    }
  };
});

import { api, ApiError } from '../src/api';

function renderAt(listingId) {
  return render(
    <MemoryRouter initialEntries={[`/listings/${listingId}`]}>
      <Routes>
        <Route path="/listings/:listingId" element={<ListingDetailPage />} />
      </Routes>
    </MemoryRouter>
  );
}

const baseListing = {
  listing_id: 'l-1',
  product_id: 'p-1',
  category: 'textile',
  listing_title: 'Handwoven Wool Shawl',
  description_en: 'A warm handwoven shawl.',
  description_local: null,
  price_suggestion: 2200,
  photo_guidance: [],
  compliance_flags: [],
  review_status: 'approved',
  created_at: '2026-09-01T00:00:00Z'
};

describe('Listing detail page — noble cause conditional rendering', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('does not render the noble-cause section when story is null', async () => {
    api.getListing.mockResolvedValue({ ...baseListing, story: null });
    renderAt('l-1');

    await waitFor(() => expect(screen.getByText('Handwoven Wool Shawl')).toBeInTheDocument());
    expect(screen.queryByText(/community-supporting purchase/i)).not.toBeInTheDocument();
  });

  it('renders the noble-cause section, visually distinct, when story is present', async () => {
    api.getListing.mockResolvedValue({
      ...baseListing,
      story: 'A portion of proceeds supports the local school.'
    });
    renderAt('l-1');

    await waitFor(() => expect(screen.getByText(/community-supporting purchase/i)).toBeInTheDocument());
    expect(screen.getByText('A portion of proceeds supports the local school.')).toBeInTheDocument();
  });

  it('handles a 404 for an unknown listing id without a raw error dump', async () => {
    api.getListing.mockRejectedValue(new ApiError({ status: 404, code: 'LISTING_NOT_FOUND', message: 'nope' }));
    renderAt('unknown-id');

    await waitFor(() => expect(screen.getByRole('alert')).toBeInTheDocument());
    expect(screen.getByText(/couldn't find/i)).toBeInTheDocument();
    expect(screen.queryByText(/LISTING_NOT_FOUND/)).not.toBeInTheDocument();
  });
});
