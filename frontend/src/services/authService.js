import { apiRequest } from './apiClient.js';

export function register(payload) {
  return apiRequest('/auth/register', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function login(payload) {
  return apiRequest('/auth/login', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function refreshToken(refreshTokenValue) {
  return apiRequest('/auth/refresh', {
    method: 'POST',
    body: JSON.stringify({ refresh_token: refreshTokenValue }),
  });
}

export function getMe(accessToken, options = {}) {
  return apiRequest('/auth/me', { accessToken, timeoutMs: options.timeoutMs ?? 8000 });
}

export function logout(refreshTokenValue) {
  return apiRequest('/auth/logout', {
    method: 'POST',
    body: JSON.stringify({ refresh_token: refreshTokenValue }),
  });
}

export function requestPasswordReset(email) {
  return apiRequest('/auth/forgot-password', {
    method: 'POST',
    body: JSON.stringify({ email }),
  });
}

export function verifyResetCode(email, code) {
  return apiRequest('/auth/verify-reset-code', {
    method: 'POST',
    body: JSON.stringify({ email, code }),
  });
}

export function resetPassword(resetToken, newPassword) {
  return apiRequest('/auth/reset-password', {
    method: 'POST',
    body: JSON.stringify({ reset_token: resetToken, new_password: newPassword }),
  });
}
