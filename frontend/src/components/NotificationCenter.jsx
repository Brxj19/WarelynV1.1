import { Bell, CheckCheck, ChevronRight, Trash2, X } from 'lucide-react';
import { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { useAuth } from '../context/AuthContext.jsx';
import { useToast } from '../hooks/useToast.jsx';
import { emptyStateIllustrations } from '../lib/emptyStates.js';
import * as notificationService from '../services/notificationService.js';
import { formatDateTime } from '../utils/formatters.js';

const TABS = [
  { key: 'all', label: 'All' },
  { key: 'unread', label: 'Unread' },
  { key: 'cleared', label: 'Cleared' },
];

export function NotificationBell() {
  const { accessToken } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();
  const ref = useRef(null);
  const [open, setOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [activeTab, setActiveTab] = useState('all');

  const fetchData = useCallback(async () => {
    if (!accessToken) return;
    try {
      const [list, unread] = await Promise.all([
        notificationService.listNotifications(accessToken, { status: activeTab }),
        notificationService.getUnreadCount(accessToken),
      ]);
      setNotifications(list);
      setUnreadCount(unread.count);
    } catch {
      // silently fail
    }
  }, [accessToken, activeTab]);

  useEffect(() => {
    if (!accessToken) return;
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData, accessToken]);

  useEffect(() => {
    function handlePointerDown(event) {
      if (ref.current && !ref.current.contains(event.target)) setOpen(false);
    }
    document.addEventListener('pointerdown', handlePointerDown);
    return () => document.removeEventListener('pointerdown', handlePointerDown);
  }, []);

  async function handleMarkRead(id) {
    setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, is_read: true } : n)));
    setUnreadCount((prev) => Math.max(0, prev - 1));
    try {
      await notificationService.markNotificationRead(accessToken, id);
    } catch {
      toast.error('Failed to mark as read.');
      fetchData();
    }
  }

  async function handleMarkAllRead() {
    setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    setUnreadCount(0);
    try {
      await notificationService.markAllNotificationsRead(accessToken);
      toast.success('All notifications marked as read.');
    } catch {
      toast.error('Failed to mark all as read.');
      fetchData();
    }
  }

  async function handleClearOne(id) {
    const wasUnread = notifications.find((n) => n.id === id && !n.is_read);
    setNotifications((prev) => prev.filter((n) => n.id !== id));
    if (wasUnread) setUnreadCount((prev) => Math.max(0, prev - 1));
    try {
      await notificationService.clearOne(accessToken, id);
    } catch {
      toast.error('Failed to clear notification.');
      fetchData();
    }
  }

  async function handleClearAll() {
    const hadUnread = notifications.some((n) => !n.is_read);
    setNotifications([]);
    if (hadUnread) setUnreadCount(0);
    try {
      await notificationService.clearAll(accessToken);
      toast.success('All notifications cleared.');
    } catch {
      toast.error('Failed to clear notifications.');
      fetchData();
    }
  }

  function handleNotificationClick(n) {
    if (n.action_url) {
      if (!n.is_read) {
        setNotifications((prev) => prev.map((x) => (x.id === n.id ? { ...x, is_read: true } : x)));
        setUnreadCount((prev) => Math.max(0, prev - 1));
        notificationService.markNotificationRead(accessToken, n.id).catch(() => {});
      }
      setOpen(false);
      navigate(n.action_url);
    }
  }

  return (
    <div className="topbar-popover-anchor" ref={ref}>
      <button className="topbar-icon-btn topbar-icon-btn-quiet relative" onClick={() => setOpen((v) => !v)} title="Notifications" type="button">
        <Bell size={18} />
        {unreadCount > 0 ? (
          <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white">{unreadCount > 9 ? '9+' : unreadCount}</span>
        ) : null}
      </button>

      {open ? (
        <div className="topbar-popover topbar-popover-right" style={{ width: '380px' }}>
          <div className="mb-2 flex items-center justify-between">
            <h3 className="text-sm font-bold text-warelyn-text">Notifications</h3>
            <div className="flex items-center gap-2">
              {unreadCount > 0 ? (
                <button className="flex items-center gap-1 text-xs font-medium text-warelyn-primary hover:underline" onClick={handleMarkAllRead} title="Mark all as read" type="button">
                  <CheckCheck size={14} /> Mark all read
                </button>
              ) : null}
              {activeTab !== 'cleared' && notifications.length > 0 ? (
                <button className="flex items-center gap-1 text-xs font-medium text-red-500 hover:underline" onClick={handleClearAll} title="Clear all notifications" type="button">
                  <Trash2 size={14} /> Clear all
                </button>
              ) : null}
            </div>
          </div>

          {/* Tabs */}
          <div className="mb-2 flex gap-1 rounded-lg bg-gray-100 p-0.5">
            {TABS.map((tab) => (
              <button
                className={`flex-1 rounded-md px-2 py-1 text-xs font-medium transition ${activeTab === tab.key ? 'bg-white text-warelyn-text shadow-sm' : 'text-warelyn-muted hover:text-warelyn-text'}`}
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                type="button"
              >
                {tab.label}
              </button>
            ))}
          </div>

          {notifications.length === 0 ? (
            <div className="py-6 text-center">
              <img src={emptyStateIllustrations.notifications} alt="" aria-hidden="true" className="mx-auto mb-3 w-16" />
              <p className="text-sm font-medium text-warelyn-text">
                {activeTab === 'unread' ? 'No unread notifications' : 'No notifications available'}
              </p>
              <p className="mt-1 text-xs text-warelyn-muted">
                {activeTab === 'unread' ? 'You are all caught up for now.' : 'New account, template, inventory, and transaction updates will appear here.'}
              </p>
            </div>
          ) : (
            <div className="max-h-80 overflow-y-auto">
              {notifications.map((n) => (
                <div
                  className={`flex items-start gap-3 rounded-xl px-3 py-3 transition ${n.is_read ? '' : 'bg-blue-50/50'} ${n.action_url ? 'cursor-pointer hover:bg-gray-50' : ''}`}
                  key={n.id}
                  onClick={() => n.action_url && handleNotificationClick(n)}
                  role={n.action_url ? 'button' : undefined}
                  tabIndex={n.action_url ? 0 : undefined}
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-warelyn-text">{n.title}</p>
                    {n.message ? <p className="mt-0.5 text-xs text-warelyn-muted line-clamp-2">{n.message}</p> : null}
                    <p className="mt-1 text-[10px] text-warelyn-muted">{formatDateTime(n.created_at)}</p>
                  </div>
                  <div className="flex shrink-0 items-center gap-1">
                    {!n.is_read && !n.cleared_at ? (
                      <button
                        className="rounded-lg p-1 text-warelyn-muted hover:bg-white hover:text-warelyn-text"
                        onClick={(e) => { e.stopPropagation(); handleMarkRead(n.id); }}
                        title="Mark as read"
                        type="button"
                      >
                        <CheckCheck size={14} />
                      </button>
                    ) : null}
                    {!n.cleared_at ? (
                      <button
                        className="rounded-lg p-1 text-warelyn-muted hover:bg-white hover:text-red-500"
                        onClick={(e) => { e.stopPropagation(); handleClearOne(n.id); }}
                        title="Clear"
                        type="button"
                      >
                        <X size={14} />
                      </button>
                    ) : null}
                    {n.action_url ? <ChevronRight className="text-warelyn-muted" size={14} /> : null}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      ) : null}
    </div>
  );
}
