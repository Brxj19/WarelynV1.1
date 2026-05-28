import { apiRequest } from './apiClient.js';

export function getMyTasks(accessToken, status = 'OPEN') {
  const params = status ? `?status=${status}` : '';
  return apiRequest(`/workflow/my-tasks${params}`, { accessToken });
}

export function completeTask(accessToken, taskId, body = {}) {
  return apiRequest(`/workflow/tasks/${taskId}/complete`, { accessToken, method: 'POST', body: JSON.stringify(body) });
}

export async function getMyTaskCount(accessToken) {
  const tasks = await apiRequest('/workflow/my-tasks?status=OPEN', { accessToken });
  return tasks.length;
}
