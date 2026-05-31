const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8001/api';

let _globalErrorHandler = null;
export function setGlobalErrorHandler(fn) { _globalErrorHandler = fn; }

export async function apiRequest(path, options = {}) {
  const { accessToken, ...fetchOptions } = options;
  const isFormData = fetchOptions.body instanceof FormData;
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      ...(fetchOptions.headers ?? {}),
    },
    ...fetchOptions,
  });

  if (response.status === 204 || response.status === 205) {
    if (!response.ok) {
      const error = new Error('API request failed.');
      error.status = response.status;
      throw error;
    }
    return null;
  }

  const contentType = response.headers.get('content-type') ?? '';
  let payload = null;
  if (contentType.includes('application/json')) {
    try {
      payload = await response.json();
    } catch {
      payload = null;
    }
  }

  if (!response.ok) {
    const errorMessage = payload?.error?.message ?? 'API request failed.';
    if (_globalErrorHandler) {
      if (response.status === 401) {
        _globalErrorHandler('Session expired. Please log in again.', 'error');
      } else if (response.status === 403) {
        _globalErrorHandler('You do not have permission for this action.', 'error');
      } else if (response.status >= 500) {
        _globalErrorHandler(errorMessage, 'error');
      }
    }
    const error = new Error(errorMessage);
    error.status = response.status;
    error.payload = payload;
    throw error;
  }

  return payload;
}

export async function downloadBlob(path, accessToken, filename) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: accessToken ? { Authorization: `Bearer ${accessToken}` } : {},
  });
  if (!response.ok) throw new Error('Download failed');
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function getHealth() {
  return apiRequest('/health');
}
