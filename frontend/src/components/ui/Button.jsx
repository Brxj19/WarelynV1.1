const variants = {
  primary: 'bg-warelyn-primary text-white hover:bg-blue-900 focus:ring-warelyn-primary/30',
  secondary: 'bg-white text-warelyn-text border border-warelyn-border hover:bg-slate-50 focus:ring-slate-300',
  accent: 'bg-warelyn-accent text-white hover:bg-emerald-600 focus:ring-emerald-300',
  danger: 'bg-warelyn-danger text-white hover:bg-red-600 focus:ring-red-300',
  ghost: 'bg-transparent text-slate-600 hover:bg-slate-100 hover:text-warelyn-text focus:ring-slate-300',
};

export function Button({ children, className = '', disabled = false, isLoading = false, variant = 'primary', type = 'button', ...props }) {
  return (
    <button
      className={`inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-semibold transition focus:outline-none focus:ring-4 disabled:cursor-not-allowed disabled:opacity-60 ${variants[variant] ?? variants.primary} ${className}`}
      disabled={isLoading || disabled}
      type={type}
      {...props}
    >
      {isLoading ? <span className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" /> : null}
      {children}
    </button>
  );
}
