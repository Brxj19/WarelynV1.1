export function Input({ className = '', error, helper, label, id, ...props }) {
  return (
    <label className="block" htmlFor={id}>
      {label ? <span className="mb-2 block text-sm font-medium text-warelyn-text">{label}</span> : null}
      <input
        id={id}
        className={`block w-full rounded-lg border bg-white px-3 py-2.5 text-sm text-warelyn-text shadow-sm outline-none transition placeholder:text-slate-400 focus:ring-4 ${error ? 'border-red-300 focus:border-warelyn-danger focus:ring-red-100' : 'border-warelyn-border focus:border-warelyn-primary focus:ring-blue-900/10'} ${className}`}
        {...props}
      />
      {error ? <p className="mt-1.5 text-xs font-medium text-warelyn-danger">{error}</p> : null}
      {!error && helper ? <p className="mt-1.5 text-xs text-warelyn-muted">{helper}</p> : null}
    </label>
  );
}
