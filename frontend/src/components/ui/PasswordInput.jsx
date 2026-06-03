import { Eye, EyeOff } from 'lucide-react';
import { useId, useState } from 'react';

export function PasswordInput({
  className = '',
  disabled = false,
  error,
  helper,
  id,
  label,
  ...props
}) {
  const generatedId = useId();
  const inputId = id ?? `password-input-${generatedId}`;
  const helperId = helper ? `${inputId}-helper` : undefined;
  const errorId = error ? `${inputId}-error` : undefined;
  const [isVisible, setIsVisible] = useState(false);

  return (
    <label className="block" htmlFor={inputId}>
      {label ? <span className="mb-1.5 block text-sm font-semibold text-warelyn-text">{label}</span> : null}
      <div
        className={`group flex w-full items-center rounded-xl border bg-white px-3 shadow-sm transition focus-within:ring-4 ${
          error
            ? 'border-red-300 focus-within:border-warelyn-danger focus-within:ring-red-100'
            : 'border-warelyn-border focus-within:border-warelyn-primary focus-within:ring-blue-900/10'
        } ${disabled ? 'cursor-not-allowed bg-slate-50 opacity-70' : ''}`}
      >
        <input
          {...props}
          aria-describedby={error ? errorId : helperId}
          aria-invalid={Boolean(error)}
          className={`block min-h-[44px] w-full border-0 bg-transparent px-0 py-2.5 text-sm text-warelyn-text outline-none ring-0 placeholder:text-slate-400 disabled:cursor-not-allowed disabled:text-slate-500 ${className}`}
          disabled={disabled}
          id={inputId}
          type={isVisible ? 'text' : 'password'}
        />
        <button
          aria-label={isVisible ? 'Hide password' : 'Show password'}
          className="inline-flex h-8 w-8 items-center justify-center rounded-md text-slate-500 transition hover:bg-slate-100 hover:text-warelyn-text focus:outline-none focus:ring-2 focus:ring-warelyn-primary/30 disabled:cursor-not-allowed disabled:opacity-50"
          disabled={disabled}
          onClick={() => setIsVisible((current) => !current)}
          type="button"
        >
          {isVisible ? <EyeOff size={16} /> : <Eye size={16} />}
        </button>
      </div>
      {error ? (
        <p className="mt-1.5 text-xs font-medium text-warelyn-danger" id={errorId}>
          {error}
        </p>
      ) : null}
      {!error && helper ? (
        <p className="mt-1.5 text-xs text-warelyn-muted" id={helperId}>
          {helper}
        </p>
      ) : null}
    </label>
  );
}
