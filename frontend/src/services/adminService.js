import { apiRequest } from './apiClient.js';

export function getPlatformSummary(accessToken) {
  return apiRequest('/admin/platform/summary', { accessToken });
}

export function getPlatformHealth(accessToken) {
  return apiRequest('/admin/platform/health', { accessToken });
}

export function listTenants(accessToken, search, status) {
  const params = new URLSearchParams();
  if (search) params.set('search', search);
  if (status) params.set('status', status);
  const qs = params.toString();
  return apiRequest(`/admin/tenants${qs ? `?${qs}` : ''}`, { accessToken });
}

export function getTenantDetail(accessToken, tenantId) {
  return apiRequest(`/admin/tenants/${tenantId}`, { accessToken });
}

export function enableTenant(accessToken, tenantId) {
  return apiRequest(`/admin/tenants/${tenantId}/enable`, { accessToken, method: 'POST' });
}

export function disableTenant(accessToken, tenantId) {
  return apiRequest(`/admin/tenants/${tenantId}/disable`, { accessToken, method: 'POST' });
}
