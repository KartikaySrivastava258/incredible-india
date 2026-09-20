// @ts-nocheck
import React, { useState } from 'react';

export default function SearchBox({ onSearch, disabled, initialValue = '' }) {
  const [value, setValue] = useState(initialValue);

  function handleSubmit(e) {
    e.preventDefault();
    onSearch(value.trim());
  }

  return (
    <form className="search-bar" onSubmit={handleSubmit} role="search">
      <input
        type="search"
        aria-label="Search for a product"
        placeholder="Search for handmade shawls, wooden toys, Ikat sarees…"
        value={value}
        onChange={(e) => setValue(e.target.value)}
      />
      <button type="submit" className="btn btn-primary" disabled={disabled || !value.trim()}>
        Search
      </button>
    </form>
  );
}

