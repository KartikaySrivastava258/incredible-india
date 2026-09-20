import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { api, ApiError } from '../api';
import SearchBox from '../components/buyer/SearchBox';
import SearchResults from '../components/buyer/SearchResults';
import ErrorState from '../components/common/ErrorState';
import LoadingSpinner from '../components/common/LoadingSpinner';

export default function BuyerSearchPage() {
  const [searchParams] = useSearchParams();
  const initialQuery = searchParams.get('q') || '';
  const [query, setQuery] = useState(initialQuery);
  const [matches, setMatches] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function runSearch(text) {
    if (!text) return;
    setQuery(text);
    setLoading(true);
    setError(null);
    try {
      const res = await api.searchMatch({ query_text: text });
      setMatches(res.matches);
    } catch (err) {
      setError(err instanceof ApiError ? err : new ApiError({ message: String(err) }));
      setMatches(null);
    } finally {
      setLoading(false);
    }
  }

  // A homepage search or category tile links here as /search?q=...; run it
  // automatically so the buttons that led here feel like one continuous action.
  useEffect(() => {
    if (initialQuery) runSearch(initialQuery);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialQuery]);

  return (
    <div>
      <h1>Find something handmade</h1>
      <p>Search surfaces hyperlocal products a demand-matching engine has identified as under-served.</p>
      <SearchBox onSearch={runSearch} disabled={loading} initialValue={initialQuery} />

      {loading && <LoadingSpinner label="Searching…" />}
      {error && <ErrorState error={error} onRetry={() => runSearch(query)} />}
      {matches && !loading && !error && <SearchResults matches={matches} query={query} />}
    </div>
  );
}

