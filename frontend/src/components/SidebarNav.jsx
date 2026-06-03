import { ChevronDown, ChevronRight, PanelLeftClose, PanelLeftOpen } from 'lucide-react';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link, NavLink, useLocation } from 'react-router-dom';

import { AppLogo } from './AppLogo.jsx';
import { activeGroupFor, getVisibleNavGroups, isItemActive } from './navigation.js';
import { useAuth } from '../context/AuthContext.jsx';
import * as workflowService from '../services/workflowService.js';

function useMyTaskCount() {
  const { accessToken, user } = useAuth();
  const [count, setCount] = useState(0);
  const intervalRef = useRef(null);
  const nonViewerRoles = ['TENANT_ADMIN', 'INVENTORY_MANAGER', 'SALES_STAFF', 'PURCHASE_STAFF'];

  const fetch = useCallback(async () => {
    if (!accessToken || !nonViewerRoles.includes(user?.role)) return;
    try {
      const c = await workflowService.getMyTaskCount(accessToken);
      setCount(c);
    } catch { /* ignore */ }
  }, [accessToken, user?.role]);

  useEffect(() => {
    fetch();
    intervalRef.current = setInterval(fetch, 60000);
    return () => clearInterval(intervalRef.current);
  }, [fetch]);

  return count;
}

export function SidebarNav({ collapsed, mobile = false, onCollapse, onNavigate, openGroup, setOpenGroup, userRole }) {
  const location = useLocation();
  const visibleGroups = useMemo(() => getVisibleNavGroups(userRole), [userRole]);
  const [openParent, setOpenParent] = useState(() => activeParentFor(location.pathname, visibleGroups));
  const brandTarget = '/landing';
  const taskCount = useMyTaskCount();

  useEffect(() => {
    setOpenParent(activeParentFor(location.pathname, visibleGroups));
  }, [location.pathname, visibleGroups]);

  return (
    <aside className={`sidebar ${collapsed ? 'is-collapsed' : ''} ${mobile ? 'is-mobile' : ''}`}>
      <div className="sidebar-brand">
        <Link className="sidebar-brand-link" onClick={onNavigate} title={userRole === 'SUPER_ADMIN' ? 'Platform Console' : 'Dashboard'} to={brandTarget}>
          <AppLogo
            className={collapsed ? 'sidebar-logo-collapsed' : ''}
            imageClassName={collapsed ? 'sidebar-logo-collapsed-image' : ''}
            size={collapsed ? 'sidebar-collapsed' : 'sidebar'}
            variant={collapsed ? 'collapsed' : 'full'}
          />
        </Link>
      </div>

      <nav className="sidebar-nav">
        {visibleGroups.map((group) => {
          const isGroupOpen = collapsed || openGroup === group.label;
          return (
            <section className="sidebar-group" key={group.label}>
              {!collapsed ? (
                <button
                  aria-expanded={isGroupOpen}
                  className="sidebar-group-toggle"
                  onClick={() => setOpenGroup(isGroupOpen ? '' : group.label)}
                  type="button"
                >
                  <span>{group.label}</span>
                  {isGroupOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                </button>
              ) : null}

              {isGroupOpen ? (
                <div className="sidebar-group-items">
                  {group.items.map((item) => {
                    if (collapsed && item.children?.length) {
                      return (
                        <NavLink
                          className={({ isActive }) => `sidebar-nav-item ${isActive || isItemActive(item, location.pathname) ? 'is-active' : ''}`}
                          key={`${group.label}-${item.label}`}
                          onClick={onNavigate}
                          title={item.label}
                          to={item.children[0].to}
                        >
                          <span className="sidebar-nav-item-icon">
                            <item.icon size={18} />
                          </span>
                          <span className="sidebar-nav-item-label">{item.label}</span>
                        </NavLink>
                      );
                    }

                    if (item.children?.length) {
                      const parentKey = `${group.label}:${item.label}`;
                      const isParentOpen = openParent === parentKey || isItemActive(item, location.pathname);
                      return (
                        <div className="sidebar-nested-group" key={parentKey}>
                          <button
                            aria-expanded={isParentOpen}
                            className={`sidebar-parent-item ${isItemActive(item, location.pathname) ? 'is-active' : ''}`}
                            onClick={() => setOpenParent(isParentOpen ? '' : parentKey)}
                            title={item.label}
                            type="button"
                          >
                            <span className="sidebar-nav-item-icon">
                              <item.icon size={18} />
                            </span>
                            <span className="sidebar-nav-item-label">{item.label}</span>
                            <span className="sidebar-parent-chevron">
                              {isParentOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                            </span>
                          </button>
                          {isParentOpen ? (
                            <div className="sidebar-subnav">
                              {item.children.map((child) => (
                                <NavLink
                                  className={({ isActive }) => `sidebar-subnav-item ${isActive ? 'is-active' : ''}`}
                                  end={child.exact}
                                  key={`${parentKey}-${child.label}`}
                                  onClick={onNavigate}
                                  title={child.label}
                                  to={child.to}
                                >
                                  {child.icon ? (
                                    <span className="sidebar-subnav-icon">
                                      <child.icon size={14} />
                                    </span>
                                  ) : null}
                                  <span>{child.label}</span>
                                </NavLink>
                              ))}
                            </div>
                          ) : null}
                        </div>
                      );
                    }

                    return (
                      <NavLink
                        className={({ isActive }) => `sidebar-nav-item ${isActive ? 'is-active' : ''}`}
                        end={item.exact}
                        key={`${group.label}-${item.label}`}
                        onClick={onNavigate}
                        title={item.label}
                        to={item.to}
                      >
                        <span className="sidebar-nav-item-icon">
                          <item.icon size={18} />
                        </span>
                        <span className="sidebar-nav-item-label">{item.label}</span>
                        {item.to === '/my-tasks' && taskCount > 0 && !collapsed && (
                          <span className="ml-auto inline-flex h-5 min-w-[20px] items-center justify-center rounded-full bg-warelyn-primary px-1.5 text-[10px] font-bold text-white">
                            {taskCount > 99 ? '99+' : taskCount}
                          </span>
                        )}
                        {!collapsed && matchesPath(item.to, location.pathname, item.exact) ? <span className="sidebar-nav-item-dot" /> : null}
                      </NavLink>
                    );
                  })}
                </div>
              ) : null}
            </section>
          );
        })}
      </nav>

      <button className="sidebar-collapse" onClick={onCollapse} type="button">
        {mobile ? <PanelLeftClose size={18} /> : collapsed ? <PanelLeftOpen size={18} /> : <PanelLeftClose size={18} />}
        <span>{mobile ? 'Close menu' : collapsed ? 'Expand sidebar' : ''}</span>
      </button>
    </aside>
  );
}

function activeParentFor(pathname, groups) {
  for (const group of groups) {
    for (const item of group.items) {
      if (item.children?.length && isItemActive(item, pathname)) {
        return `${group.label}:${item.label}`;
      }
    }
  }
  return '';
}

function matchesPath(basePath, pathname, exact = false) {
  if (exact) return pathname === basePath;
  return pathname === basePath || pathname.startsWith(`${basePath}/`);
}
