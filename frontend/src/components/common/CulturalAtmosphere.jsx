// @ts-nocheck
import React from 'react';

function Chakra({ size = 88 }) {
  const spokes = Array.from({ length: 24 }, (_, i) => i);
  const c = size / 2;
  const r = size / 2 - 6;
  return (
    <svg className="cultural-chakra" width={size} height={size} viewBox={`0 0 ${size} ${size}`} aria-hidden="true">
      <circle cx={c} cy={c} r={r} fill="none" stroke="currentColor" strokeWidth="1.6" />
      <circle cx={c} cy={c} r={r * 0.16} fill="currentColor" />
      {spokes.map((i) => {
        const a = (i * Math.PI) / 12;
        const x1 = c + Math.cos(a) * r * 0.17;
        const y1 = c + Math.sin(a) * r * 0.17;
        const x2 = c + Math.cos(a) * r * 0.92;
        const y2 = c + Math.sin(a) * r * 0.92;
        return <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke="currentColor" strokeWidth="1.25" strokeLinecap="round" />;
      })}
    </svg>
  );
}

function Spark({ style }) {
  return <span className="cultural-spark" style={style} aria-hidden="true">✦</span>;
}

export function DiwaliLights() {
  const bulbs = Array.from({ length: 18 }, (_, i) => i);
  return (
    <div className="diwali-lights" aria-hidden="true">
      <div className="diwali-wire" />
      {bulbs.map((i) => <span key={i} className="diya-bulb" style={{ left: `${2 + i * 5.35}%`, animationDelay: `${-i * 0.17}s` }} />)}
    </div>
  );
}

export function CulturalAtmosphere() {
  const sparks = [
    { left: '2%', top: '14%', animationDelay: '0s' },
    { left: '7%', top: '7%', animationDelay: '.9s' },
    { left: '95%', top: '13%', animationDelay: '.35s' },
    { left: '90%', top: '5%', animationDelay: '1.1s' },
    { left: '3%', top: '88%', animationDelay: '.55s' },
    { left: '8%', top: '95%', animationDelay: '1.25s' },
    { left: '94%', top: '89%', animationDelay: '.2s' },
    { left: '88%', top: '96%', animationDelay: '.8s' }
  ];
  return (
    <>
      <div className="cultural-glow cultural-glow--one" aria-hidden="true" />
      <div className="cultural-glow cultural-glow--two" aria-hidden="true" />
      <div className="cultural-sparks" aria-hidden="true">
        {sparks.map((s, i) => <Spark key={i} style={s} />)}
      </div>
      <div className="cultural-chakra-wrap" aria-hidden="true"><Chakra /></div>
    </>
  );
}

export function PotteryLoader({ label = 'Creating something beautiful…' }) {
  return (
    <div className="pottery-loader" role="status" aria-live="polite">
      <svg width="136" height="122" viewBox="0 0 136 122" aria-hidden="true">
        <ellipse className="pottery-wheel" cx="68" cy="101" rx="42" ry="8" />
        <ellipse cx="68" cy="98" rx="31" ry="5" className="pottery-wheel pottery-wheel--inner" />
        <path className="pottery-clay" d="M49 59 C51 52 58 48 68 48 C78 48 85 52 87 59 L83 87 C78 94 58 94 53 87 Z" />
        <ellipse className="pottery-rim" cx="68" cy="59" rx="19" ry="6" />
        <g className="pottery-hand pottery-hand--left">
          <path d="M13 83 C17 72 23 64 31 60 C35 58 39 60 39 64 C39 67 35 70 32 73 L43 80 C45 82 44 86 41 88 C34 91 26 90 19 87 Z" />
          <path d="M28 66 C25 62 22 61 20 63 M31 64 C29 60 26 58 24 60" className="pottery-finger" />
          <path d="M22 84 Q31 88 40 84" className="pottery-bangle pottery-bangle--left" />
        </g>
        <g className="pottery-hand pottery-hand--right">
          <path d="M123 83 C119 72 113 64 105 60 C101 58 97 60 97 64 C97 67 101 70 104 73 L93 80 C91 82 92 86 95 88 C102 91 110 90 117 87 Z" />
          <path d="M108 66 C111 62 114 61 116 63 M105 64 C107 60 110 58 112 60" className="pottery-finger" />
          <path d="M114 84 Q105 88 96 84" className="pottery-bangle pottery-bangle--right" />
        </g>
      </svg>
      <span>{label}</span>
    </div>
  );
}

export default CulturalAtmosphere;
