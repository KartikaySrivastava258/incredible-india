import React from 'react';
import { describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import DraftListingReview from '../src/components/onboarding/DraftListingReview';

vi.mock('qrcode', () => ({
  default: {
    toString: vi.fn(async (text) => `<svg data-qr="true"><title>${text}</title></svg>`),
  },
}));

describe('DraftListingReview QR code', () => {
  it('renders an inline QR code for the listing URL', async () => {
    window.history.pushState({}, '', '/onboarding');
    render(<DraftListingReview listing={{ listing_id: 'abc-123', listing_title: 'Handmade Basket', price_suggestion: 500, review_status: 'pending', description_en: 'Basket' }} />);

    await waitFor(() => expect(screen.getByRole('img', { name: /scan to open handmade basket/i })).toBeInTheDocument());
    expect(screen.getByText('Scan to open this listing')).toBeInTheDocument();
  });

  it('renders no QR code when listing_id is missing', () => {
    render(<DraftListingReview listing={{ listing_title: 'No ID', price_suggestion: 100, review_status: 'pending', description_en: 'Draft' }} />);
    expect(screen.queryByText('Scan to open this listing')).not.toBeInTheDocument();
  });
});
