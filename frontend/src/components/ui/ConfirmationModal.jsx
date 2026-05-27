import { AlertTriangle, CheckCircle2 } from 'lucide-react';

import { Button } from './Button.jsx';

export function ConfirmationModal({ cancelLabel = 'Cancel', children, confirmLabel = 'Confirm', description, impact, isLoading = false, onCancel, onConfirm, open, title, variant = 'primary' }) {
  if (!open) return null;
  const isDanger = variant === 'danger';
  const Icon = isDanger ? AlertTriangle : CheckCircle2;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/45 px-4 py-6 backdrop-blur-sm" role="presentation">
      <div aria-modal="true" className="w-full max-w-lg rounded-2xl border border-warelyn-border bg-white p-6 shadow-2xl" role="dialog">
        <div className="flex gap-4">
          <div className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl ${isDanger ? 'bg-red-50 text-warelyn-danger' : 'bg-blue-50 text-warelyn-primary'}`}><Icon size={22} /></div>
          <div>
            <h2 className="text-lg font-bold tracking-tight text-warelyn-text">{title}</h2>
            {description ? <p className="mt-2 text-sm leading-6 text-warelyn-muted">{description}</p> : null}
          </div>
        </div>
        {impact ? <div className="mt-5 rounded-2xl border border-warelyn-border bg-slate-50 p-4 text-sm text-warelyn-muted">{impact}</div> : null}
        {children ? <div className="mt-5">{children}</div> : null}
        <div className="mt-6 flex justify-end gap-3">
          <Button disabled={isLoading} onClick={onCancel} variant="secondary">{cancelLabel}</Button>
          <Button isLoading={isLoading} onClick={onConfirm} variant={variant}>{confirmLabel}</Button>
        </div>
      </div>
    </div>
  );
}
