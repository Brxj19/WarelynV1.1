import { apiRequest } from './apiClient.js';

export function listAssistantSessions(accessToken) {
  return apiRequest('/assistant/sessions', { accessToken });
}

export function createAssistantSession(accessToken, title = null) {
  return apiRequest('/assistant/sessions', {
    accessToken,
    method: 'POST',
    body: JSON.stringify({ title }),
  });
}

export function getAssistantSession(accessToken, sessionId) {
  return apiRequest(`/assistant/sessions/${sessionId}`, { accessToken });
}

export function askAssistant(accessToken, sessionId, question) {
  return apiRequest(`/assistant/sessions/${sessionId}/ask`, {
    accessToken,
    method: 'POST',
    body: JSON.stringify({ question }),
  });
}

export function submitAssistantFeedback(accessToken, messageId, value, note = null) {
  return apiRequest(`/assistant/messages/${messageId}/feedback`, {
    accessToken,
    method: 'POST',
    body: JSON.stringify({ value, note }),
  });
}

export function deleteAssistantSession(accessToken, sessionId) {
  return apiRequest(`/assistant/sessions/${sessionId}`, {
    accessToken,
    method: 'DELETE',
  });
}

export function getAssistantTelemetry(accessToken) {
  return apiRequest('/assistant/telemetry', { accessToken });
}
