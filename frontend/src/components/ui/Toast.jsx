import { AlertCircle, CheckCircle2, Info, X, XCircle } from 'lucide-react';

const typeStyles = {
  success: 'border-emerald-200 bg-emerald-50 text-emerald-800',
  error: 'border-red-200 bg-red-50 text-red-800',
  warning: 'border-amber-200 bg-amber-50 text-amber-800',
  info: 'border-blue-200 bg-blue-50 text-blue-800',
};

const typeIcons = {
  success: CheckCircle2,
  error: XCircle,
  warning: AlertCircle,
  info: Info,
};

export function ToastContainer({ toasts, onDismiss }) {
  if (!toasts?.length) return null;

  return (
    <div className="fixed right-4 top-4 z-[100] flex flex-col gap-2">
      {toasts.map((toast) => {
        const Icon = typeIcons[toast.type] ?? Info;
        const style = typeStyles[toast.type] ?? typeStyles.info;
        return (
          <div key={toast.id} className={`flex items-start gap-3 rounded-2xl border p-4 shadow-lg backdrop-blur-sm transition-all duration-300 animate-in slide-in-from-right-2 ${style}`} role="alert">
            <Icon className="mt-0.5 shrink-0" size={18} />
            <p className="flex-1 text-sm font-medium">{toast.message}</p>
            {toast.action && (
              <button
                className="shrink-0 rounded-lg px-2 py-0.5 text-xs font-semibold opacity-80 hover:opacity-100 underline"
                onClick={toast.action.onClick}
                type="button"
              >
                {toast.action.label}
              </button>
            )}
            <button className="shrink-0 rounded-lg p-0.5 opacity-60 hover:opacity-100" onClick={() => onDismiss(toast.id)} type="button">
              <X size={16} />
            </button>
          </div>
        );
      })}
    </div>
  );
}
