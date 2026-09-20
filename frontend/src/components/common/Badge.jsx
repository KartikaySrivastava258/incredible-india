// @ts-nocheck
import React from 'react';

const VARIANT_CLASS = {
  noble: 'badge-noble',
  neutral: 'badge-neutral',
  ok: 'badge-ok'
};

export default function Badge({ variant = 'neutral', children }) {
  return <span className={`badge ${VARIANT_CLASS[variant] || VARIANT_CLASS.neutral}`}>{children}</span>;
}

