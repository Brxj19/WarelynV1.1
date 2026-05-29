import { apiRequest } from './apiClient.js';

export function getMyTasks(accessToken, status = 'OPEN') {
  const params = status ? `?status=${status}` : '';
  return apiRequest(`/workflow/my-tasks${params}`, { accessToken });
}

export function startTask(accessToken, taskId) {
  return apiRequest(`/workflow/tasks/${taskId}/start`, { accessToken, method: 'POST', body: JSON.stringify({}) });
}

export function completeTask(accessToken, taskId, body = {}) {
  return apiRequest(`/workflow/tasks/${taskId}/complete`, { accessToken, method: 'POST', body: JSON.stringify(body) });
}

export async function getMyTaskCount(accessToken) {
  const data = await apiRequest('/workflow/my-tasks/count?status=OPEN', { accessToken });
  return data.count;
}
