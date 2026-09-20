import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ContributionControl from '../src/components/contribution/ContributionControl';

vi.mock('../src/api', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    api: {
      setContribution: vi.fn()
    }
  };
});

import { api, ApiError } from '../src/api';

describe('Contribution opt-in control', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('is off by default and calls /contributions with opted_in:false when untouched, then true+percentage on toggle', async () => {
    const user = userEvent.setup();
    api.setContribution.mockResolvedValue({
      contribution_id: 'c-1',
      seller_id: 'seller-1',
      opted_in: true,
      percentage: 10,
      touchpoint_id: 't-001',
      updated_at: '2026-09-01T00:00:00Z'
    });

    render(<ContributionControl sellerId="seller-1" touchpointId="t-001" />);

    const toggle = screen.getByLabelText(/opt in to community contribution/i);
    expect(toggle).not.toBeChecked();
    expect(api.setContribution).not.toHaveBeenCalled();

    await user.click(toggle);

    await waitFor(() =>
      expect(api.setContribution).toHaveBeenCalledWith({
        seller_id: 'seller-1',
        opted_in: true,
        percentage: 10,
        touchpoint_id: 't-001'
      })
    );

    await waitFor(() => expect(screen.getByText(/opted in at 10%/i)).toBeInTheDocument());
  });

  it('shows a clear error, not a silent failure, when the backend returns 403', async () => {
    const user = userEvent.setup();
    api.setContribution.mockRejectedValue(new ApiError({ status: 403, code: 'CEDAR_DENIED', message: 'denied' }));

    render(<ContributionControl sellerId="seller-1" touchpointId="t-001" />);
    await user.click(screen.getByLabelText(/opt in to community contribution/i));

    await waitFor(() => expect(screen.getByRole('alert')).toBeInTheDocument());
    expect(screen.getByText(/don't have permission/i)).toBeInTheDocument();
  });
});
