import { apiRequest } from './apiClient.js';

export function listSessions(accessToken) {
  return apiRequest('/cycle-counts', { accessToken });
}

export function getSession(accessToken, id) {
  return apiRequest(`/cycle-counts/${id}`, { accessToken });
}

export function createSession(accessToken, payload) {
  return apiRequest('/cycle-counts', { accessToken, method: 'POST', body: JSON.stringify(payload) });
}

export function listLines(accessToken, sessionId) {
  return apiRequest(`/cycle-counts/${sessionId}/lines`, { accessToken });
}

export function addLine(accessToken, sessionId, payload) {
  return apiRequest(`/cycle-counts/${sessionId}/lines`, { accessToken, method: 'POST', body: JSON.stringify(payload) });
}

export function updateLine(accessToken, sessionId, lineId, payload) {
  return apiRequest(`/cycle-counts/${sessionId}/lines/${lineId}`, { accessToken, method: 'PATCH', body: JSON.stringify(payload) });
}

export function submitSession(accessToken, sessionId) {
  return apiRequest(`/cycle-counts/${sessionId}/submit`, { accessToken, method: 'POST', body: JSON.stringify({}) });
}

export function reconcileSession(accessToken, sessionId) {
  return apiRequest(`/cycle-counts/${sessionId}/reconcile`, { accessToken, method: 'POST', body: JSON.stringify({}) });
}

export function cancelSession(accessToken, sessionId) {
  return apiRequest(`/cycle-counts/${sessionId}/cancel`, { accessToken, method: 'POST', body: JSON.stringify({}) });
}
