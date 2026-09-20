import React, { useEffect, useState } from 'react';
import QRCode from 'qrcode';
import Badge from '../common/Badge';

/**
 * SALONI_BATRA_TASK.md 5.1: "When stage === 'done', call
 * POST /listings/generate and show the resulting draft listing for the
 * seller to review." Renders the exact Listing fields from BRAIN.md
 * Section F — no renamed keys.
 */
export default function DraftListingReview({ listing }) {
  const [qrSvg, setQrSvg] = useState('');

  useEffect(() => {
    let cancelled = false;
    if (!listing?.listing_id || typeof window === 'undefined') {
      setQrSvg('');
      return undefined;
    }
    const url = `${window.location.origin}/listings/${listing.listing_id}`;
    QRCode.toString(url, { type: 'svg', margin: 2, errorCorrectionLevel: 'M' })
      .then((svg) => {
        if (!cancelled) setQrSvg(svg);
      })
      .catch(() => {
        if (!cancelled) setQrSvg('');
      });
    return () => { cancelled = true; };
  }, [listing?.listing_id]);

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

      {listing.listing_id && qrSvg && (
        <div className="listing-qr" aria-label={`QR code for listing ${listing.listing_id}`}>
          <div dangerouslySetInnerHTML={{ __html: qrSvg }} />
          <p className="hint">Scan to open this listing</p>
        </div>
      )}

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

