import { apiRequest } from './apiClient.js';

export function listAuditLogs(accessToken, { tenantId, action, entityType, dateFrom, dateTo, limit, offset } = {}) {
  const params = new URLSearchParams();
  if (tenantId) params.set('tenant_id', tenantId);
  if (action) params.set('action', action);
  if (entityType) params.set('entity_type', entityType);
  if (dateFrom) params.set('date_from', dateFrom);
  if (dateTo) params.set('date_to', dateTo);
  if (limit) params.set('limit', limit);
  if (offset) params.set('offset', offset);
  const qs = params.toString();
  return apiRequest(`/audit-logs${qs ? `?${qs}` : ''}`, { accessToken });
}
