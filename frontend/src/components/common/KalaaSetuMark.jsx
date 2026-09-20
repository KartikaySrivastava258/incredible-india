import React from 'react';

export default function KalaaSetuMark({ size = 58, showText = false, className = '' }) {
  return (
    <span className={`kalaa-logo ${className}`} style={{ '--logo-size': `${size}px` }}>
      <svg width={size} height={size} viewBox="0 0 100 100" role="img" aria-label="Kalaa Setu mark">
        <defs>
          <linearGradient id="ksBridge" x1="0" x2="1" y1="0" y2="1">
            <stop offset="0" stopColor="#D59A54" />
            <stop offset="1" stopColor="#A95136" />
          </linearGradient>
        </defs>
        <path d="M17 65 Q50 27 83 65" fill="none" stroke="url(#ksBridge)" strokeWidth="9" strokeLinecap="round" />
        <path d="M27 65 Q50 42 73 65" fill="none" stroke="#6B7C5E" strokeWidth="3.5" strokeLinecap="round" />
        <path d="M13 73 H87" stroke="#2C1A0E" strokeWidth="4" strokeLinecap="round" opacity=".9" />
        <path d="M23 73 V63 M38 73 V52 M62 73 V52 M77 73 V63" stroke="#2C1A0E" strokeWidth="2.5" strokeLinecap="round" />
        <g transform="rotate(-36 25 25)">
          <path d="M20 8 L26 11 L35 34 L28 37 Z" fill="#2C1A0E" />
          <path d="M19 8 L27 11 L23 3 Z" fill="#C4705A" />
          <path d="M28 37 L32 42 L35 34 Z" fill="#B8860B" />
        </g>
        <circle cx="50" cy="65" r="3" fill="#B8860B" />
      </svg>
      {showText && <span className="kalaa-logo__text">Kalaa Setu</span>}
    </span>
  );
}
