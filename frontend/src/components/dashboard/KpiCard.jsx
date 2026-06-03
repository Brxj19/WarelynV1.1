import { Link } from 'react-router-dom';

function normalizeDisplayValue(value) {
  if (value === null || value === undefined) return '-';
  if (typeof value === 'number') {
    if (Number.isInteger(value)) return value.toLocaleString();
    return value.toLocaleString(undefined, { maximumFractionDigits: 2, minimumFractionDigits: 2 });
  }
  if (typeof value === 'string') {
    const parsed = Number(value);
    if (value.trim() !== '' && !Number.isNaN(parsed)) {
      if (Number.isInteger(parsed)) return parsed.toLocaleString();
      return parsed.toLocaleString(undefined, { maximumFractionDigits: 2, minimumFractionDigits: 2 });
    }
  }
  return value;
}

function deltaMeta(delta = 0, deltaInvert = false) {
  const absolute = Math.abs(delta);
  const isUp = delta >= 0;
  const isPositive = deltaInvert ? !isUp : isUp;
  return {
    arrow: isUp ? '▲' : '▼',
    className: isPositive ? 'text-emerald-600' : 'text-red-600',
    value: absolute.toFixed(1),
  };
}

export function KpiCard({
  icon: Icon,
  label,
  value,
  delta = null,
  deltaInvert = false,
  tone = 'primary',
  to,
  helper = '',
}) {
  const toneClasses = {
    primary: 'bg-[#1e3a5f]/10 text-[#1e3a5f]',
    success: 'bg-emerald-100 text-emerald-700',
    warning: 'bg-amber-100 text-amber-700',
    danger: 'bg-red-100 text-red-700',
  };
  const trend = delta === null || Number.isNaN(Number(delta)) ? null : deltaMeta(Number(delta), deltaInvert);

  return (
    <Link className="block h-full" to={to}>
      <article className="flex h-full min-h-[148px] flex-col rounded-2xl border border-warelyn-border bg-white p-4 shadow-sm transition hover:shadow-md">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <p className="text-xs font-semibold uppercase tracking-wide text-warelyn-muted">{label}</p>
            <p className="mt-1 text-2xl font-bold tracking-tight text-warelyn-text">{normalizeDisplayValue(value)}</p>
          </div>
          {Icon ? (
            <span className={`inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${toneClasses[tone] ?? toneClasses.primary}`}>
              <Icon size={18} />
            </span>
          ) : null}
        </div>
        <div className="mt-auto min-h-[2.5rem] pt-3">
          {trend ? (
            <p className={`text-xs font-semibold ${trend.className}`}>
              {trend.arrow} {trend.value}% <span className="font-medium text-warelyn-muted">vs previous period</span>
            </p>
          ) : helper ? (
            <p className="text-xs text-warelyn-muted">{helper}</p>
          ) : (
            <span className="block text-xs opacity-0" aria-hidden="true">
              —
            </span>
          )}
        </div>
      </article>
    </Link>
  );
}
