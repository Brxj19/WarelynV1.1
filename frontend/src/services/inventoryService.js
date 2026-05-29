import { apiRequest } from './apiClient.js';

export function listStock(accessToken) {
  return apiRequest('/inventory/stock', { accessToken });
}

export function listReservations(accessToken) {
  return apiRequest('/inventory/reservations', { accessToken });
}

export function listInventoryBatches(accessToken) {
  return apiRequest('/inventory/batches', { accessToken });
}

export function getInventoryBatch(accessToken, id) {
  return apiRequest(`/inventory/batches/${id}`, { accessToken });
}

export function listInventorySerials(accessToken) {
  return apiRequest('/inventory/serials', { accessToken });
}

export function getInventorySerial(accessToken, id) {
  return apiRequest(`/inventory/serials/${id}`, { accessToken });
}
