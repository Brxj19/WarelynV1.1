import { apiRequest } from './apiClient.js';

export function listWarehouses(accessToken) {
  return apiRequest('/warehouses', { accessToken });
}

export function createWarehouse(accessToken, payload) {
  return apiRequest('/warehouses', { accessToken, method: 'POST', body: JSON.stringify(payload) });
}

export function listWarehouseLocations(accessToken, warehouseId) {
  return apiRequest(`/warehouses/${warehouseId}/locations`, { accessToken });
}

export function createWarehouseLocation(accessToken, warehouseId, payload) {
  return apiRequest(`/warehouses/${warehouseId}/locations`, { accessToken, method: 'POST', body: JSON.stringify(payload) });
}
