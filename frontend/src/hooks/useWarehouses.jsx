import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext.jsx';
import * as warehouseService from '../services/warehouseService.js';

export function useWarehouses() {
  const { accessToken } = useAuth();
  const [warehouses, setWarehouses] = useState([]);

  useEffect(() => {
    if (!accessToken) return;
    warehouseService.listWarehouses(accessToken)
      .then((data) => setWarehouses(data.map((w) => ({ value: String(w.id), label: w.name }))))
      .catch(() => {});
  }, [accessToken]);

  return warehouses;
}
