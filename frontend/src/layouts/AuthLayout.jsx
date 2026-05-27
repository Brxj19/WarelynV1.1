import { Outlet } from 'react-router-dom';
import { ArrowRight, ShieldCheck, Truck, Warehouse } from 'lucide-react';

import { AppLogo } from '../components/AppLogo.jsx';

const authHighlights = [
  ['Warehouse clarity', Warehouse],
  ['Receipt accuracy', Truck],
  ['Ledger trust', ShieldCheck],
];

export function AuthLayout() {
  return (
    <div className="grid min-h-screen bg-white lg:grid-cols-[1.06fr_0.94fr]">
      <section className="auth-panel hidden lg:flex lg:flex-col lg:justify-between">
        <div>
          <AppLogo className="mb-10" size="auth" variant="full" />
          <p className="auth-eyebrow">Operational clarity</p>
          <h1 className="auth-heading">Inventory that moves with your business.</h1>
          <p className="auth-copy">Manage products, stock, purchasing, sales, fulfillment, returns, and reporting from one calm, structured workspace.</p>
        </div>

        <div className="space-y-5">
          <div className="auth-preview-card">
            <div className="auth-preview-head">
              <span>Foundation ready</span>
              <span className="auth-preview-badge">Live workspace</span>
            </div>
            <div className="auth-preview-grid">
              {authHighlights.map(([label, Icon]) => (
                <div className="auth-preview-item" key={label}>
                  <div className="auth-preview-icon">
                    <Icon size={18} />
                  </div>
                  <span>{label}</span>
                  <ArrowRight size={15} />
                </div>
              ))}
            </div>
          </div>

          <p className="auth-caption">Tenant-safe workflows, backend-controlled stock accuracy, and a cleaner operator shell from the first sign-in.</p>
        </div>
      </section>

      <main className="flex items-center justify-center bg-[radial-gradient(circle_at_top,_rgba(30,58,138,0.08),_transparent_44%),linear-gradient(180deg,#ffffff_0%,#f8fafc_100%)] px-6 py-12">
        <Outlet />
      </main>
    </div>
  );
}
