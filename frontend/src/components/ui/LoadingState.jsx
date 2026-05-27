export function LoadingState({ message = 'Loading Warelyn workspace...', variant = 'spinner' }) {
  if (variant === 'table') {
    return (
      <div className="rounded-2xl border border-warelyn-border bg-white p-4 shadow-sm">
        <div className="mb-4 h-5 w-48 animate-pulse rounded bg-slate-100" />
        {[0, 1, 2, 3].map((row) => <div className="mb-3 h-10 animate-pulse rounded-xl bg-slate-100" key={row} />)}
      </div>
    );
  }

  return (
    <div className="flex min-h-40 items-center justify-center rounded-2xl border border-dashed border-warelyn-border bg-white p-8 text-center shadow-sm">
      <div>
        <div className="mx-auto mb-4 h-10 w-10 animate-spin rounded-full border-4 border-blue-100 border-t-warelyn-primary" />
        <p className="text-sm font-medium text-warelyn-muted">{message}</p>
      </div>
    </div>
  );
}
