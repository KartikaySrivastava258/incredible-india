import React, { useCallback, useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api, ApiError } from '../api';
import NobleCauseBadge from '../components/buyer/NobleCauseBadge';
import SimulatePurchase from '../components/sales/SimulatePurchase';
import ErrorState from '../components/common/ErrorState';
import LoadingSpinner from '../components/common/LoadingSpinner';

export default function ListingDetailPage() {
  const { listingId } = useParams();
  const [listing, setListing] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getListing(listingId);
      setListing(data);
    } catch (err) {
      setError(err instanceof ApiError ? err : new ApiError({ message: String(err) }));
    } finally {
      setLoading(false);
    }
  }, [listingId]);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) return <LoadingSpinner label="Loading listing…" />;
  if (error) return <ErrorState error={error} onRetry={load} />;
  if (!listing) return null;

  return (
    <div>
      <Link to="/search" className="hint">
        ← Back to search
      </Link>

      <div className="listing-hero" style={{ marginTop: '1rem' }}>
        <div className="listing-photo-guidance">
          {listing.photo_guidance && listing.photo_guidance.length > 0 && (
            <ul>
              {listing.photo_guidance.map((tip, i) => (
                <li key={i}>{tip}</li>
              ))}
            </ul>
          )}
        </div>
        <div>
          <h1>{listing.listing_title}</h1>
          <p className="price-tag">₹{listing.price_suggestion?.toLocaleString('en-IN')}</p>
          <p>{listing.description_en}</p>
          {listing.description_local && (
            <p className="hint">{listing.description_local}</p>
          )}

          {/* SALONI_BATRA_TASK.md 5.3: only render when non-null — never
              a placeholder implying every seller contributes. */}
          <NobleCauseBadge note={listing.story} />
        </div>
      </div>

      <SimulatePurchase listingId={listing.listing_id} priceSuggestion={listing.price_suggestion} />
    </div>
  );
}

