import { apiRequest } from './apiClient.js';

function query(params = {}) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') search.set(key, value);
  });
  const value = search.toString();
  return value ? `?${value}` : '';
}

export function getSalesDashboard(accessToken, params) {
  return apiRequest(`/dashboard/sales${query(params)}`, { accessToken });
}

export function getPurchaseDashboard(accessToken, params) {
  return apiRequest(`/dashboard/purchasing${query(params)}`, { accessToken });
}

export function getInventoryDashboard(accessToken, params) {
  return apiRequest(`/dashboard/inventory${query(params)}`, { accessToken });
}

export function getAdminDashboard(accessToken, params) {
  return apiRequest(`/dashboard/admin${query(params)}`, { accessToken });
}
