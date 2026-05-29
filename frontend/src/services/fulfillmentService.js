import { apiRequest } from './apiClient.js';

export function createPickTask(accessToken, orderId, payload) {
  return apiRequest(`/sales-orders/${orderId}/pick-tasks`, { accessToken, method: 'POST', body: JSON.stringify(payload) });
}

export function listPickTasks(accessToken) {
  return apiRequest('/pick-tasks', { accessToken });
}

export function listPickTasksForOrder(accessToken, orderId) {
  return apiRequest(`/sales-orders/${orderId}/pick-tasks`, { accessToken });
}

export function getPickTask(accessToken, pickTaskId) {
  return apiRequest(`/pick-tasks/${pickTaskId}`, { accessToken });
}

export function updatePickTask(accessToken, pickTaskId, payload) {
  return apiRequest(`/pick-tasks/${pickTaskId}`, { accessToken, method: 'PATCH', body: JSON.stringify(payload) });
}

export function startPickTask(accessToken, pickTaskId) {
  return apiRequest(`/pick-tasks/${pickTaskId}/start`, { accessToken, method: 'POST', body: JSON.stringify({}) });
}

export function pickPickTask(accessToken, pickTaskId, payload) {
  return apiRequest(`/pick-tasks/${pickTaskId}/pick`, { accessToken, method: 'POST', body: JSON.stringify(payload) });
}

export function cancelPickTask(accessToken, pickTaskId) {
  return apiRequest(`/pick-tasks/${pickTaskId}/cancel`, { accessToken, method: 'POST', body: JSON.stringify({}) });
}

export function createPackage(accessToken, orderId, payload) {
  return apiRequest(`/sales-orders/${orderId}/packages`, { accessToken, method: 'POST', body: JSON.stringify(payload) });
}

export function listPackagesForOrder(accessToken, orderId) {
  return apiRequest(`/sales-orders/${orderId}/packages`, { accessToken });
}

export function listAllPackages(accessToken) {
  return apiRequest('/packages', { accessToken });
}

export function getPackage(accessToken, packageId) {
  return apiRequest(`/packages/${packageId}`, { accessToken });
}

export function updatePackage(accessToken, packageId, payload) {
  return apiRequest(`/packages/${packageId}`, { accessToken, method: 'PATCH', body: JSON.stringify(payload) });
}

export function packPackage(accessToken, packageId, payload = {}) {
  return apiRequest(`/packages/${packageId}/pack`, { accessToken, method: 'POST', body: JSON.stringify(payload) });
}

export function cancelPackage(accessToken, packageId) {
  return apiRequest(`/packages/${packageId}/cancel`, { accessToken, method: 'POST', body: JSON.stringify({}) });
}
