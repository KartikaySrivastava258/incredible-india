import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SimulatePurchase from '../src/components/sales/SimulatePurchase';

vi.mock('../src/api', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    api: {
      simulateSale: vi.fn()
    }
  };
});

import { api, ApiError } from '../src/api';

describe('Sale simulation', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the computed split from the created LedgerEntry', async () => {
    const user = userEvent.setup();
    api.simulateSale.mockResolvedValue({
      ledger_entry_id: 'le-1',
      sale_id: 'sale-1',
      seller_id: 'seller-1',
      listing_id: 'l-1',
      sale_amount: 2200,
      platform_fee: 176,
      seller_net: 1822,
      contribution_amount: 202,
      touchpoint_id: 't-001',
      buyer_visible: true,
      created_at: '2026-09-01T00:00:00Z'
    });

    render(<SimulatePurchase listingId="l-1" priceSuggestion={2200} />);
    await user.click(screen.getByRole('button', { name: /simulate purchase/i }));

    await waitFor(() => expect(api.simulateSale).toHaveBeenCalledWith({ listing_id: 'l-1', sale_amount: 2200 }));
    await waitFor(() => expect(screen.getByText(/sale confirmed/i)).toBeInTheDocument());
    expect(screen.getByText(/seller net: ₹1,822/i)).toBeInTheDocument();
    expect(screen.getByText(/₹202/)).toBeInTheDocument();
  });

  it('shows ₹0 and a clear reason when the seller has not opted in', async () => {
    const user = userEvent.setup();
    api.simulateSale.mockResolvedValue({
      ledger_entry_id: 'le-2',
      sale_id: 'sale-2',
      seller_id: 'seller-2',
      listing_id: 'l-2',
      sale_amount: 700,
      platform_fee: 56,
      seller_net: 644,
      contribution_amount: 0,
      touchpoint_id: 't-002',
      buyer_visible: false,
      created_at: '2026-09-01T00:00:00Z'
    });

    render(<SimulatePurchase listingId="l-2" priceSuggestion={700} />);
    await user.click(screen.getByRole('button', { name: /simulate purchase/i }));

    await waitFor(() => expect(screen.getByText(/not opted in/i)).toBeInTheDocument());
  });

  it('handles a failed sale gracefully', async () => {
    const user = userEvent.setup();
    api.simulateSale.mockRejectedValue(new ApiError({ status: 400, code: 'INVALID_FIELDS', message: 'bad amount' }));

    render(<SimulatePurchase listingId="l-1" priceSuggestion={2200} />);
    await user.click(screen.getByRole('button', { name: /simulate purchase/i }));

    await waitFor(() => expect(screen.getByRole('alert')).toBeInTheDocument());
    expect(screen.getByText(/bad amount/i)).toBeInTheDocument();
  });
});
