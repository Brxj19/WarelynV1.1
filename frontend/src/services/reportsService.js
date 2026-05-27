import { apiRequest } from './apiClient.js';

function query(params = {}) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') search.set(key, value);
  });
  const value = search.toString();
  return value ? `?${value}` : '';
}

export function getInventorySummary(accessToken, params) { return apiRequest(`/reports/inventory-summary${query(params)}`, { accessToken }); }
export function getWarehouseStock(accessToken, params) { return apiRequest(`/reports/warehouse-stock${query(params)}`, { accessToken }); }
export function getLocationStock(accessToken, params) { return apiRequest(`/reports/location-stock${query(params)}`, { accessToken }); }
export function getStockMovements(accessToken, params) { return apiRequest(`/reports/stock-movements${query(params)}`, { accessToken }); }
export function getLowStock(accessToken, params) { return apiRequest(`/reports/low-stock${query(params)}`, { accessToken }); }
export function getReorderSuggestions(accessToken, params) { return apiRequest(`/reports/reorder-suggestions${query(params)}`, { accessToken }); }
export function getProductValuation(accessToken, params) { return apiRequest(`/reports/product-valuation${query(params)}`, { accessToken }); }
export function getBatchExpiry(accessToken, params) { return apiRequest(`/reports/batch-expiry${query(params)}`, { accessToken }); }
export function getSerialStatus(accessToken, params) { return apiRequest(`/reports/serial-status${query(params)}`, { accessToken }); }
export function getBlockedStock(accessToken, params) { return apiRequest(`/reports/blocked-stock${query(params)}`, { accessToken }); }
export function getReconciliation(accessToken, params) { return apiRequest(`/reports/reconciliation${query(params)}`, { accessToken }); }
export function getOperationalDashboard(accessToken, params) { return apiRequest(`/dashboard/operations${query(params)}`, { accessToken }); }

export async function downloadReportCsv(accessToken, reportKey, params = {}) {
  const response = await fetch(`${import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8001/api'}/reports/${reportKey}/export.csv${query(params)}`, {
    headers: accessToken ? { Authorization: `Bearer ${accessToken}` } : {},
  });
  if (!response.ok) {
    let message = 'Export failed.';
    try {
      const payload = await response.json();
      message = payload?.error?.message ?? message;
    } catch {}
    throw new Error(message);
  }
  return response.blob();
}
