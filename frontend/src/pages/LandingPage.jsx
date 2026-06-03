import { Link } from 'react-router-dom';
import {
  ArrowRight, BarChart3, Boxes, Grid2x2, PackageSearch, Radar, ScrollText, ShieldCheck, Truck, Users,
} from 'lucide-react';

import { AppLogo } from '../components/AppLogo.jsx';
import { LandingDemoPreview, landingDemoMeta } from '../components/landing/LandingProductDemos.jsx';
import { Button } from '../components/ui/Button.jsx';
import { useAuth } from '../context/AuthContext.jsx';

const features = [
  ['Spatial Clarity', Grid2x2, 'Top-down operational grid system giving instant clarity on physical storage capacity.'],
  ['Instant Tracking', Radar, 'Real-time stock statuses with clear visual indicators for seamless operations flow.'],
  ['Audit Ledger', ScrollText, 'Immutable chronological ledger of inbound, outbound, transfer, and return movements.'],
];

const socialLinks = ['LinkedIn', 'X', 'YouTube', 'Instagram'];
export function LandingPage() {
  const { isAuthenticated } = useAuth();
  const primaryTarget = isAuthenticated ? '/dashboard' : '/login';
  const primaryLabel = isAuthenticated ? 'Go to dashboard' : 'Log in';

  return (
    <div className="landing-page landing-font">
      <div className="landing-bg-canvas" aria-hidden="true">
        <span className="landing-orb landing-orb-one" />
        <span className="landing-orb landing-orb-two" />
        <span className="landing-orb landing-orb-three" />
      </div>
      <header className="landing-nav-shell">
        <div className="landing-nav">
          <Link className="landing-brand" to="/landing">
            <AppLogo size="landing-nav" variant="mark" />
          </Link>
          <nav className="landing-links">
            <a href="#features">Features</a>
            <a href="#pillars">Pillars</a>
            <a href="#screens">Screens</a>
            <a href="#about">About</a>
            <Link className="landing-login-button" to={primaryTarget}>
              {primaryLabel}
            </Link>
          </nav>
        </div>
      </header>

      <main className="landing-main">
        <section className="landing-hero">
          <div className="landing-hero-mark">
            <AppLogo size="landing-hero" variant="mark" />
          </div>
          <h1>One calm platform for inventory, purchasing, sales, and execution</h1>
          <p>
            Warelyn gives teams a sleek operational control layer with role-aware handoffs, traceable stock motion, and real-time decision clarity.
          </p>
          <p className="landing-tagline">Inventory that moves with your business.</p>
          <Link to={primaryTarget}>
            <Button className="landing-primary-cta">
              {primaryLabel}
              <ArrowRight size={16} />
            </Button>
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

        <section className="landing-preview" id="pillars">
          <div className="rounded-2xl border border-warelyn-border bg-white p-5 shadow-sm">
            <h2 className="text-xl font-bold text-slate-900">Built around operational pillars</h2>
            <p className="mt-2 text-sm leading-7 text-slate-600">Auth, overview, catalog, warehousing, purchases, sales, operations, reports, and settings are connected through one consistent workflow shell.</p>
            <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {[
                ['Overview', PackageSearch],
                ['Catalog', Boxes],
                ['Warehousing', Truck],
                ['Purchases', ScrollText],
                ['Sales', Radar],
                ['Operations', ShieldCheck],
                ['Reports', BarChart3],
                ['Settings', Users],
              ].map(([label, Icon]) => (
                <div className="rounded-xl border border-slate-200 bg-slate-50 p-3" key={label}>
                  <div className="mb-2 inline-flex h-8 w-8 items-center justify-center rounded-lg bg-white text-warelyn-primary">
                    <Icon size={15} />
                  </div>
                  <p className="text-xs font-semibold text-slate-800">{label}</p>
                </div>
              ))}
            </div>
          </div>
          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <article className="rounded-2xl border border-warelyn-border bg-white p-4">
              <div className="mb-3 inline-flex h-9 w-9 items-center justify-center rounded-xl bg-blue-50 text-warelyn-primary"><Boxes size={17} /></div>
              <h3 className="text-sm font-semibold text-slate-900">Catalog & Warehousing</h3>
              <p className="mt-2 text-xs leading-6 text-slate-600">Products, warehouses, cycle counts, and stock-safe movement tracking.</p>
            </article>
            <article className="rounded-2xl border border-warelyn-border bg-white p-4">
              <div className="mb-3 inline-flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-50 text-emerald-700"><Truck size={17} /></div>
              <h3 className="text-sm font-semibold text-slate-900">Purchases & Sales</h3>
              <p className="mt-2 text-xs leading-6 text-slate-600">Order lifecycles, receipts, pick-pack-fulfill, invoices, and billing continuity.</p>
            </article>
            <article className="rounded-2xl border border-warelyn-border bg-white p-4">
              <div className="mb-3 inline-flex h-9 w-9 items-center justify-center rounded-xl bg-slate-100 text-slate-700"><BarChart3 size={17} /></div>
              <h3 className="text-sm font-semibold text-slate-900">Reports & Insights</h3>
              <p className="mt-2 text-xs leading-6 text-slate-600">Inventory summary, valuation, movement, reconciliation, and actionable snapshots.</p>
            </article>
            <article className="rounded-2xl border border-warelyn-border bg-white p-4">
              <div className="mb-3 inline-flex h-9 w-9 items-center justify-center rounded-xl bg-blue-50 text-warelyn-primary"><ShieldCheck size={17} /></div>
              <h3 className="text-sm font-semibold text-slate-900">Role-safe execution</h3>
              <p className="mt-2 text-xs leading-6 text-slate-600">Workflow-aware UX with tenant safety, read-only boundaries, and clean operator handoffs.</p>
            </article>
          </div>
        </section>

        <section className="landing-preview" id="screens">
          <h2 className="text-2xl font-bold text-slate-900">Explore live product screens</h2>
          <p className="mt-2 text-sm leading-7 text-slate-600">Visual demos styled to mirror the actual Warelyn product experience.</p>
          <div className="mt-6 space-y-6">
            {landingDemoMeta.map((screen, index) => {
              const reverse = index % 2 === 1;
              return (
                <article className="grid gap-6 rounded-3xl border border-warelyn-border bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md lg:grid-cols-[0.92fr_1.08fr] lg:items-center" key={screen.title}>
                  <div className={`landing-screen-copy space-y-4 ${reverse ? 'lg:order-2' : ''}`}>
                    <span className="inline-flex rounded-full bg-blue-50 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider text-warelyn-primary">{screen.tag}</span>
                    <div className="space-y-2">
                      <h3 className="text-xl font-semibold text-slate-950">{screen.title}</h3>
                      <p className="text-sm leading-7 text-slate-600">{screen.description}</p>
                    </div>
                    <ul className="space-y-2 text-sm leading-6 text-slate-600">
                      {screen.points?.map((point) => (
                        <li className="flex gap-2" key={point}>
                          <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-warelyn-primary" />
                          <span>{point}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div className={`landing-screen-preview ${reverse ? 'lg:order-1' : ''}`}>
                    <div className="rounded-3xl border border-slate-200 bg-slate-50 p-4 shadow-inner sm:p-5">
                      <LandingDemoPreview tag={screen.tag} />
                    </div>
                  </div>
                </article>
              );
            })}
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
        <div className="flex flex-wrap items-center gap-5 text-sm text-slate-500">
          {socialLinks.map((name) => (
            <a className="transition hover:text-warelyn-primary" href="#" key={name}>
              {name}
            </a>
          ))}
          <a className="transition hover:text-warelyn-primary" href="#">Contact support</a>
          <a className="transition hover:text-warelyn-primary" href="#">Privacy</a>
          <a className="transition hover:text-warelyn-primary" href="#">Terms</a>
        </div>
        <span className="text-sm">© 2026 Warelyn Inventory. All rights reserved.</span>
      </footer>
    </div>
  );
}
