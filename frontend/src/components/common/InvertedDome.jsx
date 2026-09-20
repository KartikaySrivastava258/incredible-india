import React, { useEffect, useMemo, useRef, useState } from 'react';
import img0 from '../../assets/dome-00-artistsoninstagram-craftsman-handcraftedinind.webp';
import img1 from '../../assets/dome-01-achar-masala-recipe-indian-pickle-spice.webp';
import img2 from '../../assets/dome-02-allahabad-102.webp';
import img3 from '../../assets/dome-03-beautiful.webp';
import img4 from '../../assets/dome-04-colorful-paranda-or-parandi.webp';
import img5 from '../../assets/dome-05-culture.webp';
import img6 from '../../assets/dome-06-old-school-television-show.webp';
import img7 from '../../assets/dome-07-pottery-making-in-india.webp';
import img8 from '../../assets/dome-08-traditional-indian-art_-discover-the-beauty-o.webp';
import img9 from '../../assets/dome-09-traditional-pottery-of-india.webp';
import img10 from '../../assets/dome-10-anchaar.webp';
import img11 from '../../assets/dome-11-colorful.webp';
import img12 from '../../assets/dome-12-download-1.webp';
import img13 from '../../assets/dome-13-download-10.webp';
import img14 from '../../assets/dome-14-download-11.webp';
import img15 from '../../assets/dome-15-download-12.webp';
import img16 from '../../assets/dome-16-download-13.webp';
import img17 from '../../assets/dome-17-download-14.webp';
import img18 from '../../assets/dome-18-download-15.webp';
import img19 from '../../assets/dome-19-download-16.webp';
import img20 from '../../assets/dome-20-download-2.webp';
import img21 from '../../assets/dome-21-download-3.webp';
import img22 from '../../assets/dome-22-download-4.webp';
import img23 from '../../assets/dome-23-download-5.webp';
import img24 from '../../assets/dome-24-download-6.webp';
import img25 from '../../assets/dome-25-download-7.webp';
import img26 from '../../assets/dome-26-download-8.webp';
import img27 from '../../assets/dome-27-download-9.webp';
import img28 from '../../assets/dome-28-download.webp';
import img29 from '../../assets/dome-29-making-ladoo-in-pushkar.webp';
import img30 from '../../assets/dome-30-night-market-hoi-an.webp';
import img31 from '../../assets/dome-31-sweet-foods.webp';
import img32 from '../../assets/dome-32-_.webp';

const DOME_IMAGES = [img0, img1, img2, img3, img4, img5, img6, img7, img8, img9, img10, img11, img12, img13, img14, img15, img16, img17, img18, img19, img20, img21, img22, img23, img24, img25, img26, img27, img28, img29, img30, img31, img32];

function mod(n, m) {
  return ((n % m) + m) % m;
}

export default function InvertedDome({ className = '' }) {
  const stageRef = useRef(null);
  const dragRef = useRef({ active: false, x: 0, y: 0, startX: 0, startY: 0 });
  const [drag, setDrag] = useState({ x: 0, y: 0 });
  const [tilt, setTilt] = useState({ x: 0, y: 0 });
  const [reduced, setReduced] = useState(false);

  useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
    const update = () => setReduced(mq.matches);
    update();
    mq.addEventListener?.('change', update);
    return () => mq.removeEventListener?.('change', update);
  }, []);

  useEffect(() => {
    if (reduced) return undefined;
    let raf = 0;
    let t = 0;
    const tick = () => {
      t += 0.0022;
      setDrag((current) => dragRef.current.active ? current : {
        x: Math.sin(t) * 18,
        y: Math.cos(t * 0.7) * 5
      });
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [reduced]);

  const onPointerMove = (event) => {
    const el = stageRef.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const nx = (event.clientX - rect.left) / rect.width - 0.5;
    const ny = (event.clientY - rect.top) / rect.height - 0.5;
    setTilt({ x: nx * 4, y: ny * 3 });
    if (!dragRef.current.active) return;
    const nextX = dragRef.current.startX + event.clientX - dragRef.current.x;
    const nextY = dragRef.current.startY + event.clientY - dragRef.current.y;
    setDrag({ x: nextX, y: nextY });
  };

  const onPointerDown = (event) => {
    dragRef.current = {
      active: true,
      x: event.clientX,
      y: event.clientY,
      startX: drag.x,
      startY: drag.y
    };
    event.currentTarget.setPointerCapture?.(event.pointerId);
  };

  const onPointerUp = () => {
    dragRef.current.active = false;
  };

  const tiles = useMemo(() => {
    const cols = 11;
    const rows = 7;
    return Array.from({ length: cols * rows }, (_, index) => {
      const col = index % cols;
      const row = Math.floor(index / cols);
      const image = DOME_IMAGES[index % DOME_IMAGES.length];
      const x = col / (cols - 1) - 0.5;
      const y = row / (rows - 1) - 0.5;
      const edge = Math.min(1, Math.sqrt(x * x + y * y) * 1.45);
      const z = -Math.pow(edge, 1.7) * 180;
      const rotateY = x * -16;
      const rotateX = y * 13;
      const scale = 1 + edge * 0.12;
      return { index, image, col, row, z, rotateY, rotateX, scale };
    });
  }, []);

  return (
    <div
      ref={stageRef}
      className={`inverted-dome ${className}`}
      onPointerMove={onPointerMove}
      onPointerDown={onPointerDown}
      onPointerUp={onPointerUp}
      onPointerCancel={onPointerUp}
      onPointerLeave={() => { if (!dragRef.current.active) setTilt({ x: 0, y: 0 }); }}
      role="img"
      aria-label="Interactive panorama of Indian arts and crafts"
    >
      <div className="inverted-dome__wash" />
      <div
        className="inverted-dome__lens"
        style={{
          '--dome-drag-x': `${drag.x}px`,
          '--dome-drag-y': `${drag.y}px`,
          '--dome-tilt-x': `${tilt.x}deg`,
          '--dome-tilt-y': `${tilt.y}deg`
        }}
      >
        <div className="inverted-dome__grid">
          {tiles.map((tile) => (
            <div
              key={tile.index}
              className="inverted-dome__tile"
              style={{
                '--tile-x': tile.col,
                '--tile-y': tile.row,
                '--tile-z': `${tile.z}px`,
                '--tile-ry': `${tile.rotateY}deg`,
                '--tile-rx': `${tile.rotateX}deg`,
                '--tile-scale': tile.scale,
                '--tile-delay': `${(tile.index % 9) * 0.08}s`
              }}
            >
              <img src={tile.image} alt="" draggable="false" />
            </div>
          ))}
        </div>
      </div>
      <div className="inverted-dome__vignette" />
      <div className="inverted-dome__hint">Drag the craft wall · explore India</div>
    </div>
  );
}
