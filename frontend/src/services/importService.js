import { apiRequest } from './apiClient.js';

export function uploadProductImport(accessToken, file, options = {}) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('mode', options.mode ?? 'create_only');
  formData.append('create_missing_references', String(Boolean(options.create_missing_references)));
  if (options.column_mapping_json) {
    formData.append('column_mapping_json', options.column_mapping_json);
  }
  return apiRequest('/imports/products/upload', { accessToken, method: 'POST', body: formData });
}

export function getProductImportJob(accessToken, jobId) {
  return apiRequest(`/imports/products/${jobId}`, { accessToken });
}

export function listProductImportRows(accessToken, jobId) {
  return apiRequest(`/imports/products/${jobId}/rows`, { accessToken });
}

export function validateProductImport(accessToken, jobId) {
  return apiRequest(`/imports/products/${jobId}/validate`, { accessToken, method: 'POST', body: JSON.stringify({}) });
}

export function commitProductImport(accessToken, jobId) {
  return apiRequest(`/imports/products/${jobId}/commit`, { accessToken, method: 'POST', body: JSON.stringify({}) });
}

export function cancelProductImport(accessToken, jobId) {
  return apiRequest(`/imports/products/${jobId}/cancel`, { accessToken, method: 'POST', body: JSON.stringify({}) });
}
