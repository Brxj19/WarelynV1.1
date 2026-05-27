import { createContext, useCallback, useContext, useEffect, useState } from 'react';

import { getCurrencyInfo } from '../lib/currencies.js';
import { useAuth } from './AuthContext.jsx';
import * as settingsService from '../services/settingsService.js';

const TenantSettingsContext = createContext(null);

export function TenantSettingsProvider({ children }) {
  const { accessToken, user } = useAuth();
  const [tenantSettings, setTenantSettings] = useState(null);
  const isTenantUser = user && user.role !== 'SUPER_ADMIN';

  const fetchSettings = useCallback(async () => {
    if (!accessToken || !isTenantUser) return;
    try {
      const data = await settingsService.getTenantSettings(accessToken);
      setTenantSettings(data);
    } catch {
      // Non-admin users may not have access; silently ignore
    }
  }, [accessToken, isTenantUser]);

  useEffect(() => {
    fetchSettings();
  }, [fetchSettings]);

  const currency = tenantSettings?.currency || 'USD';
  const currencyInfo = getCurrencyInfo(currency) || { code: 'USD', name: 'US Dollar', symbol: '$', decimalPlaces: 2 };

  const value = {
    tenantSettings,
    currency,
    currencyInfo,
    refreshSettings: fetchSettings,
  };

  return (
    <TenantSettingsContext.Provider value={value}>
      {children}
    </TenantSettingsContext.Provider>
  );
}

export function useTenantSettings() {
  const ctx = useContext(TenantSettingsContext);
  if (ctx === null) {
    return { tenantSettings: null, currency: 'USD', currencyInfo: { code: 'USD', name: 'US Dollar', symbol: '$', decimalPlaces: 2 }, refreshSettings: () => {} };
  }
  return ctx;
}
