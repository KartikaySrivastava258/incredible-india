import React, { useEffect, useRef, useState } from 'react';

/**
 * Counts from 0 up to `value` once it scrolls into view. Shared by the
 * home hero stats and the impact dashboard so both animate the same way.
 * Respects prefers-reduced-motion by jumping straight to the final value.
 */
export default function AnimatedNumber({ value, format }) {
  const [display, setDisplay] = useState(0);
  const ref = useRef(null);

  useEffect(() => {
    const node = ref.current;
    if (!node || typeof value !== 'number' || Number.isNaN(value)) return undefined;

    const reduceMotion = typeof window !== 'undefined' && window.matchMedia
      ? window.matchMedia('(prefers-reduced-motion: reduce)').matches
      : false;
    if (reduceMotion) {
      setDisplay(value);
      return undefined;
    }

    if (typeof window === 'undefined' || !('IntersectionObserver' in window)) {
      setDisplay(value);
      return undefined;
    }

    let frame;
    const observer = new IntersectionObserver(([entry]) => {
      if (!entry.isIntersecting) return;
      const start = performance.now();
      const duration = 1100;
      const tick = (now) => {
        const progress = Math.min((now - start) / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        setDisplay(value * eased);
        if (progress < 1) frame = requestAnimationFrame(tick);
      };
      frame = requestAnimationFrame(tick);
      observer.disconnect();
    }, { threshold: 0.4 });

    observer.observe(node);
    return () => { observer.disconnect(); cancelAnimationFrame(frame); };
  }, [value]);

  const shown = format ? format(display) : Math.round(display).toLocaleString('en-IN');
  return <strong ref={ref}>{shown}</strong>;
}
