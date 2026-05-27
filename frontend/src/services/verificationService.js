import { apiRequest } from './apiClient.js';

export function sendEmailVerification(accessToken) {
  return apiRequest('/verification/email/send', { accessToken, method: 'POST' });
}

export function confirmEmailVerification(accessToken, code) {
  return apiRequest('/verification/email/confirm', { accessToken, method: 'POST', body: JSON.stringify({ code }) });
}

export function sendPhoneVerification(accessToken) {
  return apiRequest('/verification/phone/send', { accessToken, method: 'POST' });
}

export function confirmPhoneVerification(accessToken, code) {
  return apiRequest('/verification/phone/confirm', { accessToken, method: 'POST', body: JSON.stringify({ code }) });
}

export function getVerificationStatus(accessToken) {
  return apiRequest('/verification/status', { accessToken });
}
