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

export function getMe(accessToken) {
  return apiRequest('/auth/me', { accessToken });
}

export function logout(refreshTokenValue) {
  return apiRequest('/auth/logout', {
    method: 'POST',
    body: JSON.stringify({ refresh_token: refreshTokenValue }),
  });
}
