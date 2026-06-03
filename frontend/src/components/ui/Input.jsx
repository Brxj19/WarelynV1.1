import { forwardRef } from 'react';

export const Input = forwardRef(function Input({ className = '', error, helper, label, id, ...props }, ref) {
  return (
    <label className="block" htmlFor={id}>
      {label ? <span className="font-display mb-1.5 block text-sm font-semibold text-warelyn-text">{label}</span> : null}
      <input
        id={id}
        ref={ref}
        className={`block w-full rounded-xl border bg-white px-3 py-2.5 text-sm text-warelyn-text shadow-sm outline-none transition placeholder:text-slate-400 focus:ring-4 disabled:cursor-not-allowed disabled:border-slate-200 disabled:bg-slate-50 disabled:text-slate-500 ${error ? 'border-red-300 focus:border-warelyn-danger focus:ring-red-100' : 'border-warelyn-border focus:border-warelyn-primary focus:ring-blue-900/10'} ${className}`}
        {...props}
      />
      {error ? <p className="mt-1.5 text-xs font-medium text-warelyn-danger">{error}</p> : null}
      {!error && helper ? <p className="mt-1.5 text-xs text-warelyn-muted">{helper}</p> : null}
    </label>
  );
});
