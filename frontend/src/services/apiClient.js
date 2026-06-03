const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api';
const LOCAL_FALLBACK_BASE_URLS = ['http://localhost:8001/api', 'http://localhost:8000/api'];

let _globalErrorHandler = null;
export function setGlobalErrorHandler(fn) { _globalErrorHandler = fn; }

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

async function requestWithBase(baseUrl, path, { accessToken, timeoutMs, ...fetchOptions } = {}) {
  const isFormData = fetchOptions.body instanceof FormData;
  const controller = timeoutMs ? new AbortController() : null;
  const timeoutId = timeoutMs
    ? window.setTimeout(() => controller?.abort(new DOMException('Request timed out.', 'TimeoutError')), timeoutMs)
    : null;
  try {
    const response = await fetch(`${baseUrl}${path}`, {
      headers: {
        ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
        ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
        ...(fetchOptions.headers ?? {}),
      },
      signal: controller?.signal,
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
  } finally {
    if (timeoutId) {
      window.clearTimeout(timeoutId);
    }
  }
}

export async function apiRequest(path, options = {}) {
  const candidateBaseUrls = getCandidateBaseUrls();
  const attempts = candidateBaseUrls.length > 0 ? candidateBaseUrls : [API_BASE_URL];
  const timeoutMs = options.timeoutMs ?? (attempts.length > 1 ? 8000 : undefined);
  let lastError = null;

  for (const baseUrl of attempts) {
    try {
      return await requestWithBase(baseUrl, path, { ...options, timeoutMs });
    } catch (error) {
      lastError = error;
      if (error?.status && error.status !== 0 && error.status < 500) {
        throw error;
      }
    }
  }

  throw lastError ?? new Error('API request failed.');
}

export async function downloadBlob(path, accessToken, filename) {
  const baseUrls = getCandidateBaseUrls();
  let lastError = null;

  for (const baseUrl of baseUrls.length > 0 ? baseUrls : [API_BASE_URL]) {
    try {
      const response = await fetch(`${baseUrl}${path}`, {
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
      return;
    } catch (error) {
      lastError = error;
    }
  }

  throw lastError ?? new Error('Download failed');
}

export function getHealth() {
  return apiRequest('/health');
}
