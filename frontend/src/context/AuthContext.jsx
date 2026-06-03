import { createContext, useContext, useEffect, useMemo, useRef, useState } from 'react';

import * as authService from '../services/authService.js';
import * as settingsService from '../services/settingsService.js';

const ACCESS_TOKEN_KEY = 'warelyn.accessToken';
const REFRESH_TOKEN_KEY = 'warelyn.refreshToken';

const AuthContext = createContext(null);

function readStoredTokens() {
  return {
    accessToken: window.localStorage.getItem(ACCESS_TOKEN_KEY),
    refreshToken: window.localStorage.getItem(REFRESH_TOKEN_KEY),
  };
}

function storeTokens(accessToken, refreshToken) {
  window.localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  window.localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
}

function clearTokens() {
  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
  window.localStorage.removeItem(REFRESH_TOKEN_KEY);
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [tenant, setTenant] = useState(null);
  const [accessToken, setAccessToken] = useState(() => readStoredTokens().accessToken);
  const [refreshToken, setRefreshToken] = useState(() => readStoredTokens().refreshToken);
  const [isLoading, setIsLoading] = useState(Boolean(readStoredTokens().accessToken));
  const [defaultLandingPage, setDefaultLandingPage] = useState('/dashboard');
  const latestAccessTokenRef = useRef(readStoredTokens().accessToken);

  useEffect(() => {
    latestAccessTokenRef.current = accessToken;
  }, [accessToken]);

  async function applyPreferences(token) {
    try {
      const prefs = await settingsService.getUserPreferences(token);
      applyTheme(prefs.theme_preference ?? 'light');
      document.documentElement.setAttribute('data-density', prefs.table_density ?? 'comfortable');
      setDefaultLandingPage(prefs.default_landing_page ?? '/dashboard');
    } catch {
      // Preferences are optional — don't fail login if prefs fetch fails
    }
  }

  function applyTheme(preference) {
    window.localStorage.setItem('warelyn.themePref', preference);
    if (preference === 'system') {
      const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');
    } else {
      document.documentElement.setAttribute('data-theme', preference);
    }
  }

  async function loadMe(token = accessToken) {
    const requestToken = token ?? latestAccessTokenRef.current;

    if (!requestToken) {
      setIsLoading(false);
      return null;
    }

    setIsLoading(true);
    try {
      const data = await authService.getMe(requestToken, { timeoutMs: 8000 });
      if (latestAccessTokenRef.current !== requestToken) {
        return null;
      }
      setUser(data.user);
      setTenant(data.tenant);
      void applyPreferences(requestToken);
      return data;
    } catch (error) {
      if (latestAccessTokenRef.current === requestToken) {
        clearTokens();
        setAccessToken(null);
        setRefreshToken(null);
        setUser(null);
        setTenant(null);
      }
      throw error;
    } finally {
      if (latestAccessTokenRef.current === requestToken) {
        setIsLoading(false);
      }
    }
  }

  async function login(payload) {
    const data = await authService.login(payload);
    storeTokens(data.access_token, data.refresh_token);
    latestAccessTokenRef.current = data.access_token;
    setAccessToken(data.access_token);
    setRefreshToken(data.refresh_token);
    setUser(data.user);
    setTenant(data.tenant);
    setIsLoading(false);
    void applyPreferences(data.access_token);
    return data;
  }

  async function register(payload) {
    return authService.register(payload);
  }

  async function logout() {
    const tokenToRevoke = refreshToken;
    clearTokens();
    latestAccessTokenRef.current = null;
    setAccessToken(null);
    setRefreshToken(null);
    setUser(null);
    setTenant(null);
    setIsLoading(false);
    if (tokenToRevoke) {
      try {
        await authService.logout(tokenToRevoke);
      } catch {
        // Local logout should still complete if the server token is already invalid.
      }
    }
  }

  useEffect(() => {
    const initialToken = latestAccessTokenRef.current;
    if (initialToken) {
      loadMe(initialToken).catch(() => undefined);
    } else {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    function handleChange() {
      const current = document.documentElement.getAttribute('data-theme');
      if (current === 'dark' || current === 'light') {
        const storedPref = window.localStorage.getItem('warelyn.themePref');
        if (storedPref === 'system') {
          document.documentElement.setAttribute('data-theme', mq.matches ? 'dark' : 'light');
        }
      }
    }
    mq.addEventListener('change', handleChange);
    return () => mq.removeEventListener('change', handleChange);
  }, []);

  const value = useMemo(
    () => ({
      user,
      tenant,
      accessToken,
      refreshToken,
      isAuthenticated: Boolean(user && accessToken),
      isLoading,
      defaultLandingPage,
      login,
      register,
      logout,
      loadMe,
    }),
    [user, tenant, accessToken, refreshToken, isLoading, defaultLandingPage],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
