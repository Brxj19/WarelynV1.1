import { apiRequest } from './apiClient.js';

export function globalSearch(accessToken, q, types) {
  const params = new URLSearchParams({ q });
  if (types) params.set('types', types);
  return apiRequest(`/search?${params.toString()}`, { accessToken });
}
