import { apiRequest } from './apiClient.js';

export function listPurchaseOrders(accessToken) {
  return apiRequest('/purchase-orders', { accessToken });
}

export function createPurchaseOrder(accessToken, payload) {
  return apiRequest('/purchase-orders', { accessToken, method: 'POST', body: JSON.stringify(payload) });
}

export function getPurchaseOrder(accessToken, id) {
  return apiRequest(`/purchase-orders/${id}`, { accessToken });
}

export function updatePurchaseOrder(accessToken, id, payload) {
  return apiRequest(`/purchase-orders/${id}`, { accessToken, method: 'PATCH', body: JSON.stringify(payload) });
}

export function submitPurchaseOrder(accessToken, id) {
  return apiRequest(`/purchase-orders/${id}/submit`, { accessToken, method: 'POST', body: JSON.stringify({}) });
}

export function cancelPurchaseOrder(accessToken, id) {
  return apiRequest(`/purchase-orders/${id}/cancel`, { accessToken, method: 'POST', body: JSON.stringify({}) });
}

export function closePurchaseOrder(accessToken, id) {
  return apiRequest(`/purchase-orders/${id}/close`, { accessToken, method: 'POST', body: JSON.stringify({}) });
}

export function createPurchaseReceipt(accessToken, poId, payload) {
  return apiRequest(`/purchase-orders/${poId}/receipts`, { accessToken, method: 'POST', body: JSON.stringify(payload) });
}

export function listPurchaseReceipts(accessToken, poId) {
  return apiRequest(`/purchase-orders/${poId}/receipts`, { accessToken });
}

export function getPurchaseReceipt(accessToken, receiptId) {
  return apiRequest(`/purchase-receipts/${receiptId}`, { accessToken });
}

export function updatePurchaseReceipt(accessToken, receiptId, payload) {
  return apiRequest(`/purchase-receipts/${receiptId}`, { accessToken, method: 'PATCH', body: JSON.stringify(payload) });
}

export function commitPurchaseReceipt(accessToken, receiptId, payload) {
  return apiRequest(`/purchase-receipts/${receiptId}/commit`, { accessToken, method: 'POST', body: JSON.stringify(payload) });
}

export function cancelPurchaseReceipt(accessToken, receiptId) {
  return apiRequest(`/purchase-receipts/${receiptId}/cancel`, { accessToken, method: 'POST', body: JSON.stringify({}) });
}
