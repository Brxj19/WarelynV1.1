import { apiRequest } from './apiClient.js';

export function getFaqSuggestions(accessToken) {
  return apiRequest('/faq/suggestions', { accessToken });
}

export function askFaq(accessToken, question) {
  return apiRequest('/faq/ask', {
    accessToken,
    method: 'POST',
    body: JSON.stringify({ question }),
  });
}
