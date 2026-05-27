import { useRef, useState, useEffect } from 'react';
import { ChevronDown, ChevronRight, LayoutDashboard, LogOut, Monitor, Shield, UserCircle, Users } from 'lucide-react';
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';

import { AppLogo } from '../components/AppLogo.jsx';
import { Button } from '../components/ui/Button.jsx';
import { useAuth } from '../context/AuthContext.jsx';

const ADMIN_NAV = [
  { label: 'Platform Console', to: '/admin', icon: LayoutDashboard },
  { label: 'Tenants', to: '/admin/tenants', icon: Users },
  { label: 'Audit Logs', to: '/admin/audit-logs', icon: Shield },
  { label: 'Platform Health', to: '/admin/platform-health', icon: Monitor },
];

export function AdminLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const { logout, user } = useAuth();
  const accountRef = useRef(null);
  const [isAccountOpen, setIsAccountOpen] = useState(false);

  useEffect(() => {
    function handlePointerDown(event) {
      if (accountRef.current && !accountRef.current.contains(event.target)) setIsAccountOpen(false);
    }
    document.addEventListener('pointerdown', handlePointerDown);
    return () => document.removeEventListener('pointerdown', handlePointerDown);
  }, []);

  const currentLabel = ADMIN_NAV.find((item) => location.pathname === item.to)?.label ?? 'Admin';

  return (
    <div className="flex min-h-screen">
      <aside className="hidden lg:flex flex-col w-64 bg-[#0F2460] text-white">
        <div className="p-5">
          <Link to="/admin">
            <AppLogo size="topbar" variant="full" />
          </Link>
          <span className="mt-2 inline-block rounded bg-amber-500/20 px-2 py-0.5 text-xs font-semibold uppercase tracking-wider text-amber-300">
            Platform Admin
          </span>
        </div>
        <nav className="flex-1 px-3 py-4 space-y-1">
          {ADMIN_NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/admin'}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition ${
                  isActive ? 'bg-white/10 text-white' : 'text-white/70 hover:bg-white/5 hover:text-white'
                }`
              }
            >
              <item.icon size={18} />
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="border-t border-white/10 p-4">
          <div className="flex items-center gap-2 text-sm text-white/80">
            <UserCircle size={18} />
            <span className="truncate">{user?.name ?? 'Admin'}</span>
          </div>
          <button
            className="mt-2 flex w-full items-center gap-2 rounded px-2 py-1 text-xs text-white/60 hover:bg-white/5 hover:text-white transition"
            onClick={logout}
            type="button"
          >
            <LogOut size={14} />
            Sign out
          </button>
        </div>
      </aside>

      <div className="flex flex-1 flex-col">
        <header className="flex h-14 items-center justify-between border-b border-slate-200 bg-[#0F2460] px-4 lg:px-6">
          <div className="flex items-center gap-3">
            <span className="text-sm font-semibold text-white">Warelyn Platform Console</span>
          </div>
          <div className="topbar-popover-anchor" ref={accountRef}>
            <button
              className="flex items-center gap-2 rounded-full bg-white/10 px-3 py-1.5 text-sm text-white hover:bg-white/20 transition"
              onClick={() => setIsAccountOpen((v) => !v)}
              type="button"
            >
              <UserCircle size={18} />
              <span>{user?.name ?? 'Admin'}</span>
              <ChevronDown size={14} />
            </button>
            {isAccountOpen ? (
              <div className="topbar-popover topbar-popover-right">
                <h3>Platform Admin</h3>
                <p>{user?.email ?? ''}</p>
                <div className="topbar-popover-list">
                  <button
                    className="popover-row"
                    onClick={() => { navigate('/admin'); setIsAccountOpen(false); }}
                    type="button"
                  >
                    <LayoutDashboard size={16} />
                    <span><strong>Platform home</strong><small>Return to console</small></span>
                  </button>
                  <button
                    className="popover-row"
                    onClick={async () => { setIsAccountOpen(false); await logout(); }}
                    type="button"
                  >
                    <LogOut size={16} />
                    <span><strong>Sign out</strong><small>End this session</small></span>
                  </button>
                </div>
              </div>
            ) : null}
          </div>
        </header>

        <main className="flex-1 overflow-auto bg-warelyn-bg p-6">
          <div className="mx-auto max-w-7xl">
            <div className="breadcrumbs mb-4">
              <Link to="/admin">Home</Link>
              <ChevronRight size={14} />
              <strong>{currentLabel}</strong>
            </div>
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
