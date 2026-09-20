import React, { useEffect } from 'react';
import { Routes, Route, NavLink, useLocation } from 'react-router-dom';
import HomePage from './pages/HomePage';
import SellerOnboardingPage from './pages/SellerOnboardingPage';
import BuyerSearchPage from './pages/BuyerSearchPage';
import ListingDetailPage from './pages/ListingDetailPage';
import LedgerPage from './pages/LedgerPage';
import ImpactPage from './pages/ImpactPage';
import AdminPage from './pages/AdminPage';
import InfiniteGallery from './components/common/InfiniteGallery';
import kalaaSetuLogo from './assets/kalaa-setu-final-logo.png';

const NAV = [
  { to: '/onboarding', label: 'Sell', glyph: '✦' },
  { to: '/search', label: 'Buy', glyph: '◇' },
  { to: '/ledger', label: 'My ledger', glyph: '▤' },
  { to: '/impact', label: 'Impact', glyph: '⌁' },
  { to: '/admin', label: 'Admin', glyph: '✺' },
];

function navClass({ isActive }) {
  return isActive ? 'active' : undefined;
}

export default function App() {
  const location = useLocation();
  const isHome = location.pathname === '/';

  useEffect(() => {
    const items = document.querySelectorAll('.reveal-on-scroll:not(.is-visible)');
    if (!items.length || !('IntersectionObserver' in window)) return undefined;
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-visible');
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: '0px 0px -40px 0px' },
    );
    items.forEach((item) => observer.observe(item));
    return () => observer.disconnect();
  }, [location.pathname]);

  return (
    <div className={`app-shell ${isHome ? 'app-shell--home' : 'app-shell--inner'}`}>
      <a href="#main-content" className="skip-link">Skip to content</a>
      <InfiniteGallery className="app-background-gallery" />
      <div className="ambient-side-scene ambient-side-scene--left" aria-hidden="true" />
      <div className="ambient-side-scene ambient-side-scene--right" aria-hidden="true" />

      <header className="app-header">
        <NavLink to="/" className="app-header__brand" aria-label="Kalaa Setu home">
          <img src={kalaaSetuLogo} alt="Kalaa Setu" />
        </NavLink>
        <nav className="app-nav" aria-label="Main">
          {NAV.map((item) => (
            <NavLink key={item.to} to={item.to} className={navClass}>
              <span className="nav-glyph" aria-hidden="true">{item.glyph}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>
      </header>

      <main className="app-main" id="main-content">
        <div key={location.pathname} className="route-view">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/onboarding" element={<SellerOnboardingPage />} />
            <Route path="/search" element={<BuyerSearchPage />} />
            <Route path="/listings/:listingId" element={<ListingDetailPage />} />
            <Route path="/ledger" element={<LedgerPage />} />
            <Route path="/impact" element={<ImpactPage />} />
            <Route path="/admin" element={<AdminPage />} />
            <Route path="*" element={<HomePage />} />
          </Routes>
        </div>
      </main>

      <footer className="app-footer">
        <span className="footer-ornament" aria-hidden="true">✦</span>
        Connecting local craft with a wider world · Kalaa Setu
        <span className="footer-ornament" aria-hidden="true">✦</span>
      </footer>
    </div>
  );
}
