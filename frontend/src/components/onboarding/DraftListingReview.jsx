import React from 'react';
import Badge from '../common/Badge';

/**
 * SALONI_BATRA_TASK.md 5.1: "When stage === 'done', call
 * POST /listings/generate and show the resulting draft listing for the
 * seller to review." Renders the exact Listing fields from BRAIN.md
 * Section F — no renamed keys.
 */
export default function DraftListingReview({ listing }) {
  if (!listing) return null;
  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '1rem', flexWrap: 'wrap' }}>
        <h2 style={{ marginBottom: '0.25rem' }}>{listing.listing_title}</h2>
        <Badge variant={listing.review_status === 'approved' ? 'ok' : 'neutral'}>
          {listing.review_status === 'pending' ? 'Draft — pending review' : listing.review_status}
        </Badge>
      </div>
      <p className="price-tag">₹{listing.price_suggestion?.toLocaleString('en-IN')}</p>

      <h3>Description (English)</h3>
      <p>{listing.description_en}</p>

      {listing.description_local && (
        <>
          <h3>Description (seller's language)</h3>
          <p>{listing.description_local}</p>
        </>
      )}

      {listing.photo_guidance && listing.photo_guidance.length > 0 && (
        <>
          <h3>Photo guidance</h3>
          <ul>
            {listing.photo_guidance.map((tip, i) => (
              <li key={i}>{tip}</li>
            ))}
          </ul>
        </>
      )}

      {listing.compliance_flags && listing.compliance_flags.length > 0 && (
        <>
          <h3>Compliance flags</h3>
          <ul>
            {listing.compliance_flags.map((flag, i) => (
              <li key={i}>{flag}</li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}

