import { apiRequest } from './apiClient.js';

export function listNotifications(accessToken, { status = 'all', limit = 50, offset = 0 } = {}) {
  const params = new URLSearchParams();
  if (status && status !== 'all') params.set('status', status);
  if (limit !== 50) params.set('limit', String(limit));
  if (offset) params.set('offset', String(offset));
  const qs = params.toString();
  return apiRequest(`/notifications${qs ? `?${qs}` : ''}`, { accessToken });
}

export function getUnreadCount(accessToken) {
  return apiRequest('/notifications/unread-count', { accessToken });
}

export function markNotificationRead(accessToken, id) {
  return apiRequest(`/notifications/${id}/read`, { accessToken, method: 'POST' });
}

export function markAllNotificationsRead(accessToken) {
  return apiRequest('/notifications/read-all', { accessToken, method: 'POST' });
}

export function clearOne(accessToken, id) {
  return apiRequest(`/notifications/${id}/clear`, { accessToken, method: 'POST' });
}

export function clearAll(accessToken) {
  return apiRequest('/notifications/clear-all', { accessToken, method: 'POST' });
}
