import { apiRequest } from './apiClient.js';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api';
const LOCAL_FALLBACK_BASE_URLS = ['http://localhost:8001/api', 'http://localhost:8000/api'];

function getCandidateBaseUrls() {
  const bases = [];
  const add = (value) => {
    if (value && !bases.includes(value)) {
      bases.push(value);
    }
  };

  add(API_BASE_URL);

  if (typeof window !== 'undefined') {
    const isLocalBase = /^https?:\/\/(?:localhost|127\.0\.0\.1|\[::1\])(?::\d+)?\/api(?:\/)?$/i.test(API_BASE_URL);
    if (isLocalBase) {
      LOCAL_FALLBACK_BASE_URLS.forEach(add);
    }
  }

  return bases;
}

async function fetchBlobFromCandidates(path, accessToken, fetchOptions = {}) {
  const baseUrls = getCandidateBaseUrls();
  let lastError = null;

  for (const baseUrl of baseUrls.length > 0 ? baseUrls : [API_BASE_URL]) {
    try {
      const response = await fetch(`${baseUrl}${path}`, {
        headers: accessToken ? { Authorization: `Bearer ${accessToken}` } : {},
        ...fetchOptions,
      });
      if (!response.ok) {
        if (response.status && response.status < 500) {
          let message = 'Download failed.';
          try {
            const payload = await response.json();
            message = payload?.error?.message ?? message;
          } catch {}
          const error = new Error(message);
          error.status = response.status;
          throw error;
        }
        throw new Error('Download failed.');
      }
      return response.blob();
    } catch (error) {
      lastError = error;
      if (error?.status && error.status < 500) {
        throw error;
      }
    }
  }

  throw lastError ?? new Error('Download failed.');
}

export function listCategories(accessToken) {
  return apiRequest('/catalog/categories', { accessToken });
}

export function createCategory(accessToken, payload) {
  return apiRequest('/catalog/categories', { accessToken, method: 'POST', body: JSON.stringify(payload) });
}

export function listBrands(accessToken) {
  return apiRequest('/catalog/brands', { accessToken });
}

export function createBrand(accessToken, payload) {
  return apiRequest('/catalog/brands', { accessToken, method: 'POST', body: JSON.stringify(payload) });
}

export function listVendors(accessToken) {
  return apiRequest('/catalog/vendors', { accessToken });
}

export function createVendor(accessToken, payload) {
  return apiRequest('/catalog/vendors', { accessToken, method: 'POST', body: JSON.stringify(payload) });
}

export function listCustomers(accessToken) {
  return apiRequest('/catalog/customers', { accessToken });
}

export function createCustomer(accessToken, payload) {
  return apiRequest('/catalog/customers', { accessToken, method: 'POST', body: JSON.stringify(payload) });
}

export function listProducts(accessToken, search = '') {
  const query = search ? `?search=${encodeURIComponent(search)}` : '';
  return apiRequest(`/catalog/products${query}`, { accessToken });
}

export function getProductDetail(accessToken, productId) {
  return apiRequest(`/catalog/products/${productId}`, { accessToken });
}

export async function downloadProductsCsv(accessToken, search = '') {
  const query = search ? `?search=${encodeURIComponent(search)}` : '';
  return fetchBlobFromCandidates(`/catalog/products/export.csv${query}`, accessToken);
}

export async function downloadProductLabelsPdf(accessToken, productIds, trackingMode = 'ALL') {
  return fetchBlobFromCandidates('/catalog/products/labels.pdf', accessToken, {
    method: 'POST',
    cache: 'no-store',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ product_ids: productIds, tracking_mode: trackingMode }),
  });
}

export async function downloadProductLabelsForProductPdf(accessToken, productId) {
  return fetchBlobFromCandidates(`/catalog/products/${productId}/labels.pdf`, accessToken, {
    method: 'POST',
    cache: 'no-store',
  });
}

export function createProduct(accessToken, payload) {
  return apiRequest('/catalog/products', { accessToken, method: 'POST', body: JSON.stringify(payload) });
}
