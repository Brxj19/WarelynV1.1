import { apiRequest } from './apiClient.js';

export function listSalesOrders(accessToken) {
  return apiRequest('/sales-orders', { accessToken });
}

export function createSalesOrder(accessToken, payload) {
  return apiRequest('/sales-orders', { accessToken, method: 'POST', body: JSON.stringify(payload) });
}

export function getSalesOrder(accessToken, id) {
  return apiRequest(`/sales-orders/${id}`, { accessToken });
}

export function updateSalesOrder(accessToken, id, payload) {
  return apiRequest(`/sales-orders/${id}`, { accessToken, method: 'PATCH', body: JSON.stringify(payload) });
}

export function confirmSalesOrder(accessToken, id, payload) {
  return apiRequest(`/sales-orders/${id}/confirm`, { accessToken, method: 'POST', body: JSON.stringify(payload) });
}

export function cancelSalesOrder(accessToken, id) {
  return apiRequest(`/sales-orders/${id}/cancel`, { accessToken, method: 'POST', body: JSON.stringify({}) });
}

export function closeSalesOrder(accessToken, id) {
  return apiRequest(`/sales-orders/${id}/close`, { accessToken, method: 'POST', body: JSON.stringify({}) });
}

export function createSalesFulfillment(accessToken, orderId, payload) {
  return apiRequest(`/sales-orders/${orderId}/fulfillments`, { accessToken, method: 'POST', body: JSON.stringify(payload) });
}

export function listSalesFulfillments(accessToken, orderId) {
  return apiRequest(`/sales-orders/${orderId}/fulfillments`, { accessToken });
}

export function listAllSalesFulfillments(accessToken) {
  return apiRequest('/sales-fulfillments', { accessToken });
}

export function getSalesFulfillment(accessToken, fulfillmentId) {
  return apiRequest(`/sales-fulfillments/${fulfillmentId}`, { accessToken });
}

export function updateSalesFulfillment(accessToken, fulfillmentId, payload) {
  return apiRequest(`/sales-fulfillments/${fulfillmentId}`, { accessToken, method: 'PATCH', body: JSON.stringify(payload) });
}

export function commitSalesFulfillment(accessToken, fulfillmentId, payload) {
  return apiRequest(`/sales-fulfillments/${fulfillmentId}/commit`, { accessToken, method: 'POST', body: JSON.stringify(payload) });
}

export function cancelSalesFulfillment(accessToken, fulfillmentId) {
  return apiRequest(`/sales-fulfillments/${fulfillmentId}/cancel`, { accessToken, method: 'POST', body: JSON.stringify({}) });
}
