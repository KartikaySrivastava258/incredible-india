// @ts-nocheck
import React, { useEffect, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import kalaaSetuLogo from '../assets/kalaa-setu-final-logo.png';
import potteryHeart from '../assets/craft-pottery-heart.jpg';
import flowerSeller from '../assets/craft-flower-seller.jpg';
import laddu from '../assets/craft-laddu.jpg';
import embroideredArtisan from '../assets/craft-embroidered-artisan.jpg';
import achaar from '../assets/craft-achaar.jpg';
import grain from '../assets/craft-grain.jpg';
import embroidery from '../assets/craft-embroidery.jpg';

const VALUE_PROPS = [
  { icon: '◌', title: 'Discover Unique Crafts', text: 'Find work with a story behind it.' },
  { icon: '✦', title: 'Support Local Artisans', text: 'Put visibility where makers live.' },
  { icon: '↗', title: 'Sustainable Livelihoods', text: 'Turn craft into opportunity.' },
  { icon: '⌁', title: 'Stronger Communities', text: 'Make each purchase count.' }
];

const CATEGORIES = [
  { label: 'Textiles', query: 'textile', image: embroideredArtisan },
  { label: 'Food & Pickles', query: 'food', image: achaar },
  { label: 'Embroidery', query: 'embroidery', image: embroidery },
  { label: 'Handmade Craft', query: 'handicraft', image: potteryHeart }
];

const STORIES = [
  { eyebrow: 'CRAFT & HERITAGE', title: 'Hands that shape more than clay', body: 'A close look at the hands, tools and traditions behind handmade work.', image: potteryHeart },
  { eyebrow: 'LOCAL LIVELIHOOD', title: 'From a local skill to a visible storefront', body: 'Kalaa Setu helps sellers turn what they already make into something buyers can discover.', image: flowerSeller },
  { eyebrow: 'REGIONAL FLAVOURS', title: 'Recipes that travel beyond the village', body: 'Food made locally can find a much wider audience when its story is easy to understand.', image: laddu },
  { eyebrow: 'TEXTILE TRADITIONS', title: 'Every stitch carries a place', body: 'Traditional embroidery becomes searchable, presentable and easier to discover.', image: embroideredArtisan },
];

const PETALS = Array.from({ length: 18 }, (_, index) => ({
  id: index,
  top: `${4 + ((index * 17) % 88)}%`,
  delay: `${(index * 1.9) % 18}s`,
  duration: `${22 + (index % 6) * 5}s`,
  scale: 0.48 + (index % 5) * 0.12,
  drift: `${-22 + (index % 7) * 9}px`,
}));

const EMBERS = Array.from({ length: 9 }, (_, index) => ({
  id: index,
  left: `${8 + ((index * 13) % 84)}%`,
  delay: `${(index * 2.1) % 10}s`,
  duration: `${11 + (index % 4) * 3}s`,
}));

function AnimatedNumber({ value, suffix = '' }) {
  const [display, setDisplay] = useState(0);
  const ref = useRef(null);
  useEffect(() => {
    const node = ref.current;
    if (!node) return undefined;
    let frame;
    if (typeof window === 'undefined' || !('IntersectionObserver' in window)) return undefined;
    const observer = new IntersectionObserver(([entry]) => {
      if (!entry.isIntersecting) return;
      const start = performance.now();
      const duration = 1100;
      const tick = (now) => {
        const progress = Math.min((now - start) / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        setDisplay(Math.round(value * eased));
        if (progress < 1) frame = requestAnimationFrame(tick);
      };
      frame = requestAnimationFrame(tick);
      observer.disconnect();
    }, { threshold: 0.5 });
    observer.observe(node);
    return () => { observer.disconnect(); cancelAnimationFrame(frame); };
  }, [value]);
  return <strong ref={ref}>{display.toLocaleString('en-IN')}{suffix}</strong>;
}

export default function HomePage() {
  const [heroQuery, setHeroQuery] = useState('');
  const [activeStory, setActiveStory] = useState(0);
  const heroRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    let raf = 0;
    const move = (event) => {
      if (!heroRef.current) return;
      const rect = heroRef.current.getBoundingClientRect();
      const x = ((event.clientX - rect.left) / rect.width - 0.5);
      const y = ((event.clientY - rect.top) / rect.height - 0.5);
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => {
        heroRef.current?.style.setProperty('--parallax-x', `${x * 12}px`);
        heroRef.current?.style.setProperty('--parallax-y', `${y * 8}px`);
      });
    };
    const node = heroRef.current;
    node?.addEventListener('pointermove', move, { passive: true });
    return () => { node?.removeEventListener('pointermove', move); cancelAnimationFrame(raf); };
  }, []);

  useEffect(() => {
    const timer = window.setInterval(() => setActiveStory((current) => (current + 1) % STORIES.length), 5200);
    return () => window.clearInterval(timer);
  }, []);

  function handleHeroSearch(e) {
    e.preventDefault();
    const text = heroQuery.trim();
    navigate(text ? `/search?q=${encodeURIComponent(text)}` : '/search');
  }

  return (
    <div className="home-page">
      <div ref={heroRef} className="hero hero--photo hero--dome">
        <div className="home-petals" aria-hidden="true">
          {PETALS.map((petal) => (
            <span key={petal.id} className="home-petal" style={{ top: petal.top, animationDelay: petal.delay, animationDuration: petal.duration, '--petal-scale': petal.scale, '--petal-drift': petal.drift }} />
          ))}
          {EMBERS.map((ember) => (
            <span key={`ember-${ember.id}`} className="home-ember" style={{ left: ember.left, animationDelay: ember.delay, animationDuration: ember.duration }} />
          ))}
        </div>
        <div className="hero-orb hero-orb--one" aria-hidden="true" />
        <div className="hero-orb hero-orb--two" aria-hidden="true" />
        <div className="hero__inner hero__inner--dome">
          <img className="hero-brand-logo hero-parallax--logo" src={kalaaSetuLogo} alt="Kalaa Setu" />
          <span className="tag">From Tradition to Tomorrow</span>
          <h1>A Bridge for Every Creator</h1>
          <p>Kalaa Setu connects India&rsquo;s rural artisans and local sellers with buyers everywhere, turning a handmade product into a professional listing while making community impact visible.</p>

          <form className="hero-search" onSubmit={handleHeroSearch} role="search">
            <span className="hero-search__icon" aria-hidden="true">⌕</span>
            <input type="search" aria-label="Search handcrafted products, artisans, or regions" placeholder="Search handcrafted products, artisans, or regions…" value={heroQuery} onChange={(e) => setHeroQuery(e.target.value)} suppressHydrationWarning />
            <button type="submit" className="btn btn-accent">Search</button>
          </form>

          <ul className="value-props">
            {VALUE_PROPS.map((v) => (
              <li key={v.title} className="value-prop" tabIndex="0">
                <span className="value-props__icon" aria-hidden="true">{v.icon}</span>
                <span><b>{v.title}</b><small>{v.text}</small></span>
              </li>
            ))}
          </ul>
        </div>

        <div className="hero-stats reveal-on-scroll">
          <div className="hero-stats__numbers">
            <div><AnimatedNumber value={10000} suffix="+" /><span>Artisans Empowered</span></div>
            <div><AnimatedNumber value={500} suffix="+" /><span>Unique Art Forms</span></div>
            <div><AnimatedNumber value={28} suffix="+" /><span>States Connected</span></div>
          </div>
          <Link to="/onboarding" className="btn btn-accent hero-stats__cta">Be a Part of the Bridge →</Link>
        </div>
      </div>

      <section className="category-section reveal-on-scroll">
        <div className="section-kicker">A living catalogue of India</div>
        <div className="category-section__head"><h2>Explore by Category</h2><Link to="/search">View all →</Link></div>
        <div className="category-grid">
          {CATEGORIES.map((c, index) => (
            <Link key={c.query} to={`/search?q=${encodeURIComponent(c.query)}`} className="category-tile parallax-card" style={{ '--delay': `${index * 70}ms` }}>
              <span className="category-tile__thumb"><img src={c.image} alt="" /></span>
              <span>{c.label}</span>
              <small>Explore craft stories →</small>
            </Link>
          ))}
        </div>
      </section>

      <section className="craft-stories reveal-on-scroll">
        <div className="section-kicker">Stories behind the objects</div>
        <div className="story-heading"><div><h2>Made by hand. Found by people.</h2><p>Real craft references give the marketplace a sense of place, not just a grid of products.</p></div><div className="story-dots" aria-label="Story navigation">{STORIES.map((story, i) => <button key={story.title} className={i === activeStory ? 'is-active' : ''} onClick={() => setActiveStory(i)} aria-label={`Show story ${i + 1}`} />)}</div></div>
        <div className="story-feature">
          {STORIES.map((story, i) => (
            <article key={story.title} className={`story-feature__panel ${i === activeStory ? 'is-active' : ''}`}>
              <img src={story.image} alt="" />
              <div className="story-feature__copy"><span>{story.eyebrow}</span><h3>{story.title}</h3><p>{story.body}</p><Link to="/search" className="story-link">Discover related work →</Link></div>
            </article>
          ))}
        </div>
      </section>

      <section className="home-impact-strip reveal-on-scroll">
        <div className="impact-copy"><span className="section-kicker">From maker to marketplace</span><h2>A digital bridge should still feel human.</h2><p>Kalaa Setu combines conversational AI, demand matching and transparent impact into one journey.</p><div className="hero-ctas"><Link to="/onboarding" className="btn btn-primary">Try seller onboarding</Link><Link to="/impact" className="btn btn-ghost">See the impact layer</Link></div></div>
        <div className="impact-image-stack"><img src={grain} alt="Traditional rural work" /><img src={achaar} alt="Handmade food product" /></div>
      </section>

      <section className="home-ctas card reveal-on-scroll">
        <span className="section-kicker">Cross the bridge</span>
        <h2>Where do you want to begin?</h2>
        <p>Make something, find something, or understand the impact behind it.</p>
        <div className="hero-ctas"><Link to="/onboarding" className="btn btn-primary">Start seller onboarding</Link><Link to="/search" className="btn btn-ghost">Browse as a buyer</Link><Link to="/impact" className="btn btn-ghost">See community impact</Link></div>
      </section>
    </div>
  );
}
