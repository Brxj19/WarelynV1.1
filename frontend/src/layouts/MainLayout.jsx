import { useEffect, useMemo, useRef, useState } from 'react';
import { ChevronDown, ChevronRight, HelpCircle, Menu, Settings, UserCircle } from 'lucide-react';
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom';

import { AppLogo } from '../components/AppLogo.jsx';
import { FaqChatWidget } from '../components/FaqChatWidget.jsx';
import { NotificationBell } from '../components/NotificationCenter.jsx';
import { QuickCreateMenu } from '../components/QuickCreateMenu.jsx';
import { RecentHistoryMenu } from '../components/RecentHistoryMenu.jsx';
import { SidebarNav } from '../components/SidebarNav.jsx';
import { TopbarSearch } from '../components/TopbarSearch.jsx';
import { activeGroupFor, flattenNav, resolveRouteMeta } from '../components/navigation.js';
import { Button } from '../components/ui/Button.jsx';
import { ConfirmationModal } from '../components/ui/ConfirmationModal.jsx';
import { useAuth } from '../context/AuthContext.jsx';
import { TenantSettingsProvider } from '../context/TenantSettingsContext.jsx';
import { setGlobalErrorHandler } from '../services/apiClient.js';
import { useToast } from '../hooks/useToast.jsx';

function readRecentPages() {
  try {
    const stored = JSON.parse(window.localStorage.getItem('warelyn.recentPages') || '[]');
    return Array.isArray(stored) ? stored : [];
  } catch {
    window.localStorage.removeItem('warelyn.recentPages');
    return [];
  }
}

export function MainLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const { logout, tenant, user } = useAuth();
  const toast = useToast();
  const isSuperAdmin = user?.role === 'SUPER_ADMIN';
  const accountRef = useRef(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(() => window.localStorage.getItem('warelyn.sidebarCollapsed') === 'true');
  const [isAccountOpen, setIsAccountOpen] = useState(false);
  const [isSignOutConfirmOpen, setIsSignOutConfirmOpen] = useState(false);
  const [isSigningOut, setIsSigningOut] = useState(false);
  const navItems = useMemo(() => flattenNav(user?.role), [user?.role]);
  const [openGroup, setOpenGroup] = useState(() => activeGroupFor(location.pathname, user?.role));
  const [history, setHistory] = useState(readRecentPages);
  const current = useMemo(() => resolveRouteMeta(location.pathname, user?.role), [location.pathname, user?.role]);

  useEffect(() => setOpenGroup(activeGroupFor(location.pathname, user?.role)), [location.pathname, user?.role]);
  useEffect(() => {
    window.localStorage.setItem('warelyn.sidebarCollapsed', String(isCollapsed));
  }, [isCollapsed]);
  useEffect(() => {
    const entry = { label: current.label, path: location.pathname, section: current.section };
    setHistory((items) => {
      const next = [entry, ...items.filter((item) => item.path !== entry.path)].slice(0, 8);
      window.localStorage.setItem('warelyn.recentPages', JSON.stringify(next));
      return next;
    });
  }, [current.label, current.section, location.pathname]);
  useEffect(() => {
    function handlePointerDown(event) {
      if (accountRef.current && !accountRef.current.contains(event.target)) setIsAccountOpen(false);
    }
    document.addEventListener('pointerdown', handlePointerDown);
    return () => document.removeEventListener('pointerdown', handlePointerDown);
  }, []);
  useEffect(() => {
    setGlobalErrorHandler((msg, type) => toast[type]?.(msg));
    return () => setGlobalErrorHandler(null);
  }, [toast]);

  async function confirmSignOut() {
    setIsSigningOut(true);
    try {
      await logout();
    } finally {
      setIsSigningOut(false);
      setIsSignOutConfirmOpen(false);
    }
  }

  return (
    <TenantSettingsProvider>
    <div className={`app-shell ${isCollapsed ? 'sidebar-collapsed' : ''}`}>
      <header className="topbar">
        <div className="topbar-left">
          <Button aria-label="Open navigation menu" className="topbar-icon-btn lg:hidden" onClick={() => setIsSidebarOpen(true)} title="Open menu" type="button" variant="ghost">
            <Menu size={20} />
          </Button>
          <Link className="topbar-brand" to="/landing">
            <AppLogo size="topbar" variant="full" />
          </Link>
        </div>

        <TopbarSearch navItems={navItems} recordsEnabled={!isSuperAdmin} />

        <div className="topbar-actions">
          <QuickCreateMenu role={user?.role} />
          <RecentHistoryMenu history={history} />
          {!isSuperAdmin ? <NotificationBell /> : null}
          <div className="topbar-popover-anchor" ref={accountRef}>
            <button className="workspace-chip" onClick={() => setIsAccountOpen((currentState) => !currentState)} type="button">
              <UserCircle size={20} />
              <span>
                <strong>{user?.name ?? 'Warehouse user'}</strong>
                <small>{tenant?.company_name ?? user?.role ?? 'Workspace'}</small>
              </span>
              <ChevronDown size={15} />
            </button>
            {isAccountOpen ? (
              <div className="topbar-popover topbar-popover-right">
                <h3>{tenant?.company_name ?? 'Warelyn workspace'}</h3>
                <p>{user?.role ?? 'Authenticated user'}</p>
                <div className="topbar-popover-list">
                  <button
                    className="popover-row"
                    onClick={() => {
                      navigate(isSuperAdmin ? '/admin' : '/dashboard');
                      setIsAccountOpen(false);
                    }}
                    type="button"
                  >
                    <UserCircle size={16} />
                    <span>
                      <strong>{isSuperAdmin ? 'Platform home' : 'Workspace home'}</strong>
                      <small>{isSuperAdmin ? 'Return to platform console' : 'Return to dashboard'}</small>
                    </span>
                  </button>
                  {user?.role !== 'SUPER_ADMIN' ? (
                    <button
                      className="popover-row"
                      onClick={() => {
                        navigate('/settings');
                        setIsAccountOpen(false);
                      }}
                      type="button"
                    >
                      <Settings size={16} />
                      <span>
                        <strong>Settings</strong>
                        <small>Tenant and personal preferences</small>
                      </span>
                    </button>
                  ) : null}
                  <button
                    className="popover-row"
                    onClick={() => {
                      setIsAccountOpen(false);
                      setIsSignOutConfirmOpen(true);
                    }}
                    type="button"
                  >
                    <HelpCircle size={16} />
                    <span>
                      <strong>Sign out</strong>
                      <small>End this session</small>
                    </span>
                  </button>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      </header>
      <div className="shell-body">
        <div className="hidden lg:block">
          <SidebarNav
            collapsed={isCollapsed}
            onCollapse={() => setIsCollapsed((value) => !value)}
            onNavigate={() => undefined}
            openGroup={openGroup}
            setOpenGroup={setOpenGroup}
            userRole={user?.role}
          />
        </div>

        {isSidebarOpen ? (
          <div className="mobile-sidebar-backdrop" onClick={() => setIsSidebarOpen(false)} role="presentation">
            <div className="mobile-sidebar" onClick={(event) => event.stopPropagation()} role="presentation">
              <SidebarNav
                collapsed={false}
                mobile
                onCollapse={() => setIsSidebarOpen(false)}
                onNavigate={() => setIsSidebarOpen(false)}
                openGroup={openGroup}
                setOpenGroup={setOpenGroup}
                userRole={user?.role}
              />
            </div>
          </div>
        ) : null}

        <main className="shell-main">
          <div className="shell-content">
            <div className="content-scroll">
              <div className="content-inner">
                <div className="breadcrumbs">
                  <Link to="/landing">Home</Link>
                  <ChevronRight size={14} />
                  <span>{current.section}</span>
                  <ChevronRight size={14} />
                  <strong>{current.label}</strong>
                </div>
                <Outlet />
              </div>
            </div>
          </div>
        </main>
      </div>
      <ConfirmationModal
        open={isSignOutConfirmOpen}
        title="Sign out?"
        description="Are you sure you want to end this session?"
        confirmLabel="Sign out"
        variant="danger"
        isLoading={isSigningOut}
        onCancel={() => setIsSignOutConfirmOpen(false)}
        onConfirm={confirmSignOut}
      />
      {!isSuperAdmin ? <FaqChatWidget /> : null}
    </div>
    </TenantSettingsProvider>
  );
}
