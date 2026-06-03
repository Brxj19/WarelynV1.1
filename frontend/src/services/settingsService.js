import { apiRequest } from './apiClient.js';

export function getTenantSettings(accessToken) {
  return apiRequest('/settings/tenant', { accessToken });
}

export function updateTenantSettings(accessToken, data) {
  return apiRequest('/settings/tenant', { accessToken, method: 'PATCH', body: JSON.stringify(data) });
}

export function getUserPreferences(accessToken) {
  return apiRequest('/settings/preferences', { accessToken });
}

export function updateUserPreferences(accessToken, data) {
  return apiRequest('/settings/preferences', { accessToken, method: 'PATCH', body: JSON.stringify(data) });
}

export function uploadTenantLogo(accessToken, file) {
  const body = new FormData();
  body.append('file', file);
  return apiRequest('/uploads/logo', { accessToken, method: 'POST', body });
}
