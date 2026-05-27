import { Link } from 'react-router-dom';
import { Grid2x2, Radar, ScrollText } from 'lucide-react';

import { AppLogo } from '../components/AppLogo.jsx';
import { Button } from '../components/ui/Button.jsx';

const features = [
  ['Spatial Clarity', Grid2x2, 'Top-down operational grid system giving instant clarity on physical storage capacity.'],
  ['Instant Tracking', Radar, 'Real-time stock statuses with clear visual indicators for seamless operations flow.'],
  ['Audit Ledger', ScrollText, 'Immutable chronological ledger of inbound, outbound, transfer, and return movements.'],
];

export function LandingPage() {
  return (
    <div className="landing-page">
      <header className="landing-nav-shell">
        <div className="landing-nav">
          <Link className="landing-brand" to="/">
            <AppLogo size="landing-nav" variant="mark" />
          </Link>
          <nav className="landing-links">
            <a href="#features">Features</a>
            <a href="#pricing">Pricing</a>
            <a href="#about">About</a>
            <Link className="landing-login-button" to="/login">
              Login
            </Link>
          </nav>
        </div>
      </header>

      <main className="landing-main">
        <section className="landing-hero">
          <div className="landing-hero-mark">
            <AppLogo size="landing-hero" variant="mark" />
          </div>
          <h1>WARELYN INVENTORY</h1>
          <p>
            Inventory that moves with your business
          </p>
          <p>
            High-precision warehouse operations. Distilling complex logistics into a clean,
            top-down operational grid system.
          </p>
          <Link to="/register">
            <Button className="landing-primary-cta">START MAPPING</Button>
          </Link>
        </section>

        <section className="landing-feature-grid" id="features">
          {features.map(([title, Icon, description]) => (
            <article className="landing-feature-card" key={title}>
              <div className="landing-feature-icon">
                <Icon size={20} />
              </div>
              <h2>{title}</h2>
              <p>{description}</p>
            </article>
          ))}
        </section>

        <section className="landing-preview" id="pricing">
          <div className="landing-preview-image-shell">
            <img alt="Warelyn system preview reference" className="landing-preview-image" src="/LandingPageScreen.png" />
            <div className="landing-preview-overlay" />
            <div className="landing-preview-center">
              <Button className="landing-preview-button" variant="secondary">
                SYSTEM INTERFACE PREVIEW
              </Button>
            </div>
          </div>
        </section>

        <section className="landing-about-copy" id="about">
          <div>
            <span>Operational grid</span>
            <p>Clear warehouse mapping, instant state visibility, and a calmer control surface for inventory teams.</p>
          </div>
          <div>
            <span>Read-only trust</span>
            <p>Frontend polish stays separate from backend stock authority, preserving ledger-first inventory correctness.</p>
          </div>
          <div>
            <span>Ready foundation</span>
            <p>Products, orders, receiving, fulfillment, returns, and reports stay accessible without adding dead-end routes.</p>
          </div>
        </section>
      </main>

      <footer className="landing-footer">
        <span className="landing-footer-brand">
          <AppLogo size="landing-footer" variant="mark" />
        </span>
        <span>© 2026 Warelyn. All rights reserved. Precise logistics.</span>
      </footer>
    </div>
  );
}
