import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import SellerOnboardingPage from '../src/pages/SellerOnboardingPage';

vi.mock('../src/api', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    api: {
      createSeller: vi.fn(),
      sendOnboardingMessage: vi.fn(),
      generateListing: vi.fn(),
      setContribution: vi.fn()
    }
  };
});

import { api } from '../src/api';

function renderPage() {
  return render(
    <MemoryRouter>
      <SellerOnboardingPage />
    </MemoryRouter>
  );
}

describe('Seller onboarding chat', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('registers the seller, walks through every stage, and shows the draft listing', async () => {
    const user = userEvent.setup();

    api.createSeller.mockResolvedValue({
      seller_id: 'seller-1',
      name: 'Meena Devi',
      village: 'Bhaderwah',
      state: 'J&K',
      seller_language: 'hi',
      touchpoint_id: 't-001',
      created_at: '2026-09-01T00:00:00Z'
    });

    renderPage();

    await user.type(screen.getByLabelText(/name/i), 'Meena Devi');
    await user.type(screen.getByLabelText(/village/i), 'Bhaderwah');
    await user.type(screen.getByLabelText(/state/i), 'J&K');
    await user.click(screen.getByRole('button', { name: /start onboarding/i }));

    await waitFor(() => expect(api.createSeller).toHaveBeenCalledTimes(1));

    // Stage: idea -> procedure
    api.sendOnboardingMessage.mockResolvedValueOnce({
      conversation_id: 'convo-1',
      ai_reply_text: 'Tell me about the procedure now.',
      stage: 'procedure',
      draft_state: {}
    });
    await user.type(screen.getByLabelText(/message/i), 'We make wool shawls');
    await user.click(screen.getByRole('button', { name: /send/i }));
    await waitFor(() => expect(screen.getByText('Tell me about the procedure now.')).toBeInTheDocument());
    expect(screen.getByText(/procedure/i, { selector: '.stage-rail__item.is-current' })).toBeInTheDocument();

    // Stage: procedure -> business_model
    api.sendOnboardingMessage.mockResolvedValueOnce({
      conversation_id: 'convo-1',
      ai_reply_text: 'Now let us talk business model.',
      stage: 'business_model',
      draft_state: {}
    });
    await user.type(screen.getByLabelText(/message/i), 'Understood');
    await user.click(screen.getByRole('button', { name: /send/i }));
    await waitFor(() => expect(screen.getByText('Now let us talk business model.')).toBeInTheDocument());
    expect(screen.getByText(/business model/i, { selector: '.stage-rail__item.is-current' })).toBeInTheDocument();

    // Stage: business_model -> capture
    api.sendOnboardingMessage.mockResolvedValueOnce({
      conversation_id: 'convo-1',
      ai_reply_text: 'Describe your product for capture.',
      stage: 'capture',
      draft_state: {}
    });
    await user.type(screen.getByLabelText(/message/i), 'Opt-in sounds good');
    await user.click(screen.getByRole('button', { name: /send/i }));
    await waitFor(() => expect(screen.getByText('Describe your product for capture.')).toBeInTheDocument());
    expect(screen.getByText(/capture/i, { selector: '.stage-rail__item.is-current' })).toBeInTheDocument();

    // Stage: capture -> done, triggers listings/generate automatically
    api.sendOnboardingMessage.mockResolvedValueOnce({
      conversation_id: 'convo-1',
      ai_reply_text: 'Generating your listing now.',
      stage: 'done',
      draft_state: {}
    });
    api.generateListing.mockResolvedValue({
      listing_id: 'listing-1',
      product_id: 'product-1',
      category: 'textile',
      listing_title: 'Handwoven Wool Shawl',
      description_en: 'A warm handwoven shawl.',
      description_local: null,
      price_suggestion: 2200,
      photo_guidance: ['Shoot in daylight'],
      story: null,
      compliance_flags: [],
      review_status: 'pending',
      created_at: '2026-09-01T00:00:00Z'
    });
    await user.type(screen.getByLabelText(/message/i), 'Handwoven wool shawl from Bhaderwah');
    await user.click(screen.getByRole('button', { name: /send/i }));

    await waitFor(() => expect(api.generateListing).toHaveBeenCalledWith({ seller_id: 'seller-1', conversation_id: 'convo-1' }));
    await waitFor(() => expect(screen.getByText('Handwoven Wool Shawl')).toBeInTheDocument());
    expect(screen.getByText(/₹2,200/)).toBeInTheDocument();
    expect(screen.getByText('A warm handwoven shawl.')).toBeInTheDocument();
  });

  it('shows a clear retry state, not raw error JSON, when the AI service returns a 502', async () => {
    const user = userEvent.setup();
    const { ApiError } = await import('../src/api');

    api.createSeller.mockResolvedValue({
      seller_id: 'seller-2',
      name: 'Test Seller',
      village: 'X',
      state: 'Y',
      seller_language: 'hi',
      touchpoint_id: 't-001',
      created_at: '2026-09-01T00:00:00Z'
    });

    renderPage();
    await user.type(screen.getByLabelText(/name/i), 'Test Seller');
    await user.type(screen.getByLabelText(/village/i), 'X');
    await user.type(screen.getByLabelText(/state/i), 'Y');
    await user.click(screen.getByRole('button', { name: /start onboarding/i }));
    await waitFor(() => expect(api.createSeller).toHaveBeenCalledTimes(1));

    api.sendOnboardingMessage.mockRejectedValueOnce(new ApiError({ status: 502, code: 'UPSTREAM_UNAVAILABLE', message: 'down' }));
    await user.type(screen.getByLabelText(/message/i), 'hello');
    await user.click(screen.getByRole('button', { name: /send/i }));

    await waitFor(() =>
  expect(screen.getByRole('alert')).toHaveTextContent(/AI is temporarily unavailable/i)
);
    expect(screen.queryByText(/"code":/)).not.toBeInTheDocument();
    expect(screen.queryByText(/UPSTREAM_UNAVAILABLE/)).not.toBeInTheDocument();
  });
});
