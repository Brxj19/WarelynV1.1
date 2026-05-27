import { apiRequest } from './apiClient.js';

export function listUsers(accessToken, { search, role, status } = {}) {
  const params = new URLSearchParams();
  if (search) params.set('search', search);
  if (role) params.set('role', role);
  if (status) params.set('status', status);
  const qs = params.toString();
  return apiRequest(`/users${qs ? `?${qs}` : ''}`, { accessToken });
}

export function getUser(accessToken, userId) {
  return apiRequest(`/users/${userId}`, { accessToken });
}

export function createUser(accessToken, data) {
  return apiRequest('/users', { accessToken, method: 'POST', body: JSON.stringify(data) });
}

export function updateUser(accessToken, userId, data) {
  return apiRequest(`/users/${userId}`, { accessToken, method: 'PATCH', body: JSON.stringify(data) });
}

export function deleteUser(accessToken, userId) {
  return apiRequest(`/users/${userId}`, { accessToken, method: 'DELETE' });
}

export function enableUser(accessToken, userId) {
  return apiRequest(`/users/${userId}/enable`, { accessToken, method: 'POST' });
}

export function disableUser(accessToken, userId) {
  return apiRequest(`/users/${userId}/disable`, { accessToken, method: 'POST' });
}

export function resetPassword(accessToken, userId, newPassword) {
  return apiRequest(`/users/${userId}/reset-password`, { accessToken, method: 'POST', body: JSON.stringify({ new_password: newPassword }) });
}
