import React, { useCallback, useEffect, useRef, useState } from 'react';
import { api, ApiError } from '../api';
import { session } from '../session';
import SellerSetupForm from '../components/onboarding/SellerSetupForm';
import StageProgress from '../components/onboarding/StageProgress';
import ChatWindow from '../components/onboarding/ChatWindow';
import DraftListingReview from '../components/onboarding/DraftListingReview';
import ContributionControl from '../components/contribution/ContributionControl';
import ErrorState from '../components/common/ErrorState';
import LoadingSpinner from '../components/common/LoadingSpinner';

let msgCounter = 0;
const nextId = () => `m${++msgCounter}`;

export default function SellerOnboardingPage() {
  const [seller, setSeller] = useState(() => session.get().seller || null);
  const [conversationId, setConversationId] = useState(() => session.get().conversation_id || null);
  const [stage, setStage] = useState(() => session.get().stage || 'idea');
  const [messages, setMessages] = useState(() => session.get().messages || []);
  const [sendError, setSendError] = useState(null);
  const [sending, setSending] = useState(false);

  const [listing, setListing] = useState(() => session.get().listing || null);
  const [generating, setGenerating] = useState(false);
  const [generateError, setGenerateError] = useState(null);
  const generateAttempted = useRef(Boolean(session.get().listing));

  const lastFailedMessage = useRef(null);

  useEffect(() => {
    session.set({ seller, conversation_id: conversationId, stage, messages, listing });
  }, [seller, conversationId, stage, messages, listing]);

  const generateListing = useCallback(async () => {
    if (!seller || !conversationId) return;
    setGenerating(true);
    setGenerateError(null);
    try {
      const draft = await api.generateListing({ seller_id: seller.seller_id, conversation_id: conversationId });
      setListing(draft);
    } catch (err) {
      setGenerateError(err instanceof ApiError ? err : new ApiError({ message: String(err) }));
    } finally {
      setGenerating(false);
    }
  }, [seller, conversationId]);

  useEffect(() => {
    if (stage === 'done' && !listing && !generateAttempted.current) {
      generateAttempted.current = true;
      generateListing();
    }
  }, [stage, listing, generateListing]);

  function handleRegistered(newSeller) {
    setSeller(newSeller);
    setMessages([{ id: nextId(), from: 'ai', text: `Namaste ${newSeller.name}! Bataiye, aap kya banate hain?` }]);
  }

  async function handleSend(text) {
    if (!seller) return;
    const sellerMsg = { id: nextId(), from: 'seller', text };
    setMessages((prev) => [...prev, sellerMsg]);
    setSending(true);
    setSendError(null);
    lastFailedMessage.current = null;
    try {
      const res = await api.sendOnboardingMessage({
        seller_id: seller.seller_id,
        conversation_id: conversationId,
        message_text: text
      });
      setConversationId(res.conversation_id);
      setStage(res.stage);
      setMessages((prev) => [...prev, { id: nextId(), from: 'ai', text: res.ai_reply_text }]);
    } catch (err) {
      const apiErr = err instanceof ApiError ? err : new ApiError({ message: String(err) });
      setSendError(apiErr);
      lastFailedMessage.current = text;
    } finally {
      setSending(false);
    }
  }

  function retryLastMessage() {
    if (lastFailedMessage.current) {
      handleSend(lastFailedMessage.current);
    }
  }

  function startOver() {
    session.clear();
    setSeller(null);
    setConversationId(null);
    setStage('idea');
    setMessages([]);
    setListing(null);
    generateAttempted.current = false;
  }

  if (!seller) {
    return (
      <div>
        <h1>Seller onboarding</h1>
        <p>Tell us about your product, in your own language. No English, no forms — just a conversation.</p>
        <SellerSetupForm onRegistered={handleRegistered} />
      </div>
    );
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', flexWrap: 'wrap', gap: '0.5rem' }}>
        <h1>Onboarding: {seller.name}</h1>
        <button type="button" className="btn btn-ghost" onClick={startOver}>
          Start over
        </button>
      </div>

      <div className="onboarding-layout">
        <StageProgress stage={stage} />
        <div>
          <ChatWindow messages={messages} onSend={handleSend} disabled={sending || stage === 'done'} />
          {sending && <div style={{ marginTop: '0.6rem' }}><LoadingSpinner label="AI is thinking…" /></div>}
          {sendError && (
            <div style={{ marginTop: '0.6rem' }}>
              <ErrorState error={sendError} onRetry={retryLastMessage} />
            </div>
          )}
        </div>
      </div>

      {stage === 'done' && (
        <div style={{ marginTop: '2.5rem' }}>
          <h2>Your draft listing</h2>
          {generating && <LoadingSpinner label="Generating your listing…" />}
          {generateError && <ErrorState error={generateError} onRetry={generateListing} />}
          {listing && !generating && (
            <div style={{ display: 'grid', gap: '1.5rem' }}>
              <DraftListingReview listing={listing} />
              <ContributionControl sellerId={seller.seller_id} touchpointId={seller.touchpoint_id} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}

