import { useCallback, useContext, useState } from 'react';
import { createContext } from 'react';

const ToastContext = createContext(null);

let toastId = 0;

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const addToast = useCallback((message, type = 'info', options = {}) => {
    const id = ++toastId;
    const toast = { id, message, type, duration: options.duration ?? 4500, action: options.action ?? null };
    setToasts((prev) => [...prev, toast]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, toast.duration);
    return id;
  }, []);

  const removeToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const success = useCallback((message, opts) => addToast(message, 'success', opts), [addToast]);
  const error = useCallback((message, opts) => addToast(message, 'error', opts), [addToast]);
  const warning = useCallback((message, opts) => addToast(message, 'warning', opts), [addToast]);
  const info = useCallback((message, opts) => addToast(message, 'info', opts), [addToast]);

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast, success, error, warning, info }}>
      {children}
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used within a ToastProvider');
  return ctx;
}
