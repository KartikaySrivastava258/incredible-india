import React, { useEffect, useMemo, useRef, useState } from 'react';
import { GALLERY_IMAGES } from './galleryImages';

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function wrap(value, loop) {
  if (loop <= 0) return 0;
  return ((value % loop) + loop) % loop;
}

function computeLayout(width, height) {
  const cols = width < 640 ? 5 : width < 1100 ? 8 : 11;
  const gap = width < 640 ? 10 : width < 1100 ? 12 : 14;
  const bleed = 1.0;
  const fieldWidth = Math.max(320, width) * bleed;
  const tileW = Math.round((fieldWidth - gap * (cols - 1)) / cols);
  const tileH = Math.round(tileW * 1.2);
  const visibleRows = Math.ceil(Math.max(height, 1) / (tileH + gap));
  const rows = Math.max(6, visibleRows + 2);
  const loop = rows * (tileH + gap);
  return { cols, rows, gap, tileW, tileH, loop };
}

function pickImage(col, row) {
  const len = GALLERY_IMAGES.length;
  const index = (row * 5 + col * 3 + ((row * col) % 7)) % len;
  return GALLERY_IMAGES[index] ?? GALLERY_IMAGES[0];
}

function buildColumns(layout) {
  return Array.from({ length: layout.cols }, (_, col) => {
    const tiles = Array.from({ length: layout.rows }, (_, row) => pickImage(col, row));
    const speedBase = 0.018 + (col % 4) * 0.005;
    const direction = col % 2 === 0 ? 1 : -1;
    return {
      id: col,
      speed: direction * speedBase,
      tiles,
    };
  });
}

export default function InfiniteGallery({ className = '' }) {
  const rootRef = useRef(null);
  const rigRef = useRef(null);
  const stripRefs = useRef([]);
  const [layout, setLayout] = useState(() => computeLayout(1280, 800));
  const [mounted, setMounted] = useState(false);
  const columns = useMemo(() => buildColumns(layout), [layout]);
  const columnsRef = useRef(columns);
  const layoutRef = useRef(layout);
  const offsetsRef = useRef(columns.map(() => 0));

  columnsRef.current = columns;
  layoutRef.current = layout;
  if (offsetsRef.current.length !== columns.length) {
    offsetsRef.current = columns.map((_, index) => offsetsRef.current[index] ?? 0);
  }

  const motionRef = useRef({
    reduced: false,
    targetX: 0,
    targetY: 0,
    tiltX: 0,
    tiltY: 0,
    pivotX: 50,
    pivotY: 46,
    spotX: 50,
    spotY: 46,
    scroll: 0,
    lastTime: 0,
    frame: 0,
    dragging: false,
    dragLastY: 0,
    dragLastT: 0,
    velocity: 0,
    idle: 0,
  });

  useEffect(() => {
    const root = rootRef.current;
    if (!root) return;

    const measure = () => {
      const rect = root.getBoundingClientRect();
      const next = computeLayout(rect.width || window.innerWidth, rect.height || window.innerHeight);
      root.style.setProperty('--tile-w', `${next.tileW}px`);
      root.style.setProperty('--tile-h', `${next.tileH}px`);
      root.style.setProperty('--gallery-gap', `${next.gap}px`);
      setLayout((prev) => {
        if (
          prev.cols === next.cols &&
          prev.rows === next.rows &&
          Math.abs(prev.tileW - next.tileW) < 0.5 &&
          Math.abs(prev.tileH - next.tileH) < 0.5
        ) {
          layoutRef.current = { ...prev, loop: next.loop, gap: next.gap, tileW: next.tileW, tileH: next.tileH };
          return prev;
        }
        return next;
      });
    };

    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    const setReduced = () => {
      motionRef.current.reduced = reduceMotion.matches;
    };
    setReduced();
    reduceMotion.addEventListener('change', setReduced);

    const onScroll = () => {
      motionRef.current.scroll = window.scrollY || 0;
    };

    const onPointerMove = (event) => {
      const rect = root.getBoundingClientRect();
      const nx = clamp((event.clientX - rect.left) / Math.max(rect.width, 1) - 0.5, -0.5, 0.5);
      const ny = clamp((event.clientY - rect.top) / Math.max(rect.height, 1) - 0.5, -0.5, 0.5);
      motionRef.current.targetX = nx;
      motionRef.current.targetY = ny;
      if (motionRef.current.dragging) {
        const now = performance.now();
        const dy = event.clientY - motionRef.current.dragLastY;
        const dt = Math.max(1, now - motionRef.current.dragLastT);
        motionRef.current.velocity = dy / dt;
        motionRef.current.dragLastY = event.clientY;
        motionRef.current.dragLastT = now;
        offsetsRef.current = offsetsRef.current.map((value) => value - dy * 0.85);
      }
    };

    const onPointerDown = (event) => {
      if (event.button !== 0) return;
      motionRef.current.dragging = true;
      motionRef.current.velocity = 0;
      motionRef.current.dragLastY = event.clientY;
      motionRef.current.dragLastT = performance.now();
      root.setPointerCapture?.(event.pointerId);
    };

    const onPointerUp = () => {
      motionRef.current.dragging = false;
    };

    const observer = new ResizeObserver(measure);
    observer.observe(root);
    measure();
    setMounted(true);
    onScroll();

    window.addEventListener('pointermove', onPointerMove, { passive: true });
    root.addEventListener('pointerdown', onPointerDown);
    window.addEventListener('pointerup', onPointerUp);
    window.addEventListener('pointercancel', onPointerUp);
    window.addEventListener('scroll', onScroll, { passive: true });

    const tick = (time) => {
      const m = motionRef.current;
      const currentLayout = layoutRef.current;
      const dt = Math.min(40, time - (m.lastTime || time));
      m.lastTime = time;
      m.idle += dt;
      const follow = 1 - Math.pow(0.001, dt / 16);
      const reduced = m.reduced;

      if (!reduced) {
        const idleX = Math.sin(m.idle * 0.00018) * 0.8;
        const idleY = Math.cos(m.idle * 0.00014) * 0.5;
        m.tiltY += (m.targetX * 4.2 + idleX - m.tiltY) * follow * 0.28;
        m.tiltX += (m.targetY * -2.4 + idleY - m.tiltX) * follow * 0.28;
        m.pivotX += (50 + m.targetX * 16 - m.pivotX) * follow * 0.4;
        m.pivotY += (46 + m.targetY * 10 - m.pivotY) * follow * 0.4;
        m.spotX += (50 + m.targetX * 80 - m.spotX) * follow;
        m.spotY += (46 + m.targetY * 70 - m.spotY) * follow;
        if (!m.dragging) {
          m.velocity *= Math.pow(0.92, dt / 16);
          const inertia = m.velocity * dt;
          const scrollFlow = m.scroll * 0.012;
          const cols = columnsRef.current;
          offsetsRef.current = cols.map((col, i) => {
            const current = offsetsRef.current[i] ?? 0;
            const signedInertia = inertia * (col.speed >= 0 ? 1 : -1);
            return current + col.speed * dt + signedInertia + scrollFlow * (0.35 + (i % 3) * 0.08);
          });
        }
      }

      if (rigRef.current) {
        rigRef.current.style.setProperty('--tilt-x', `${reduced ? 2 : m.tiltX}deg`);
        rigRef.current.style.setProperty('--tilt-y', `${reduced ? 0 : m.tiltY}deg`);
        rigRef.current.style.setProperty('--rig-x', `${reduced ? 0 : m.targetX * -10}px`);
        rigRef.current.style.setProperty('--rig-y', `${reduced ? 0 : m.targetY * -6}px`);
      }
      if (rootRef.current) {
        rootRef.current.style.setProperty('--pivot-x', `${m.pivotX}%`);
        rootRef.current.style.setProperty('--pivot-y', `${m.pivotY}%`);
        rootRef.current.style.setProperty('--spot-x', `${m.spotX}%`);
        rootRef.current.style.setProperty('--spot-y', `${m.spotY}%`);
      }

      const loop = currentLayout.loop;
      stripRefs.current.forEach((node, i) => {
        if (!node) return;
        const y = reduced ? 0 : wrap(offsetsRef.current[i] ?? 0, loop);
        node.style.transform = `translate3d(0, ${-y}px, 0)`;
      });

      m.frame = requestAnimationFrame(tick);
    };
    motionRef.current.frame = requestAnimationFrame(tick);

    return () => {
      cancelAnimationFrame(motionRef.current.frame);
      observer.disconnect();
      reduceMotion.removeEventListener('change', setReduced);
      window.removeEventListener('pointermove', onPointerMove);
      root.removeEventListener('pointerdown', onPointerDown);
      window.removeEventListener('pointerup', onPointerUp);
      window.removeEventListener('pointercancel', onPointerUp);
      window.removeEventListener('scroll', onScroll);
    };
  }, []);

  return (
    <div
      ref={rootRef}
      className={`infinite-gallery ${className}`}
      aria-hidden="true"
      style={{
        ['--tile-w']: `${layout.tileW}px`,
        ['--tile-h']: `${layout.tileH}px`,
        ['--gallery-gap']: `${layout.gap}px`,
      }}
    >
      <div className="infinite-gallery__stage">
        <div ref={rigRef} className="infinite-gallery__rig">
          <div className="infinite-gallery__columns">
            {mounted &&
              columns.map((col, colIndex) => (
              <div key={col.id} className="infinite-gallery__col">
                <div
                  ref={(node) => {
                    stripRefs.current[colIndex] = node;
                  }}
                  className="infinite-gallery__strip"
                >
                  {[...col.tiles, ...col.tiles].map((src, tileIndex) => (
                    <div
                      key={`${col.id}-${tileIndex}`}
                      className="infinite-gallery__tile"
                      style={{ ['--ken-delay']: `${((colIndex * 1.4 + tileIndex) % 9) * -2.4}s` }}
                    >
                      <img
                        src={src}
                        alt=""
                        draggable={false}
                        loading={tileIndex < layout.rows ? 'eager' : 'lazy'}
                        decoding="async"
                      />
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
      <div className="infinite-gallery__veil" />
      <div className="infinite-gallery__vignette" />
      <div className="infinite-gallery__sweep" />
      <div className="infinite-gallery__grain" />
    </div>
  );
}
