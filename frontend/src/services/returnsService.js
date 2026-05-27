import { apiRequest } from './apiClient.js';

export function listSalesReturns(accessToken) {
  return apiRequest('/sales-returns', { accessToken });
}

export function createSalesReturn(accessToken, payload) {
  return apiRequest('/sales-returns', { accessToken, method: 'POST', body: JSON.stringify(payload) });
}

export function getSalesReturn(accessToken, id) {
  return apiRequest(`/sales-returns/${id}`, { accessToken });
}

export function updateSalesReturn(accessToken, id, payload) {
  return apiRequest(`/sales-returns/${id}`, { accessToken, method: 'PATCH', body: JSON.stringify(payload) });
}

export function submitSalesReturn(accessToken, id) {
  return apiRequest(`/sales-returns/${id}/submit`, { accessToken, method: 'POST', body: JSON.stringify({}) });
}

export function cancelSalesReturn(accessToken, id) {
  return apiRequest(`/sales-returns/${id}/cancel`, { accessToken, method: 'POST', body: JSON.stringify({}) });
}

export function inspectSalesReturn(accessToken, id, payload) {
  return apiRequest(`/sales-returns/${id}/inspect`, { accessToken, method: 'POST', body: JSON.stringify(payload) });
}

export function processSalesReturn(accessToken, id, payload) {
  return apiRequest(`/sales-returns/${id}/process`, { accessToken, method: 'POST', body: JSON.stringify(payload) });
}
