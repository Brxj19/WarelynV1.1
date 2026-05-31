import { apiRequest } from './apiClient.js';

export function listPutawayTasks(accessToken, status = null) {
  const params = status ? `?status=${encodeURIComponent(status)}` : '';
  return apiRequest(`/putaway-tasks${params}`, { accessToken });
}

