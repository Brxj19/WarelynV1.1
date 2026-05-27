export function Card({ children, className = '' }) {
  return <div className={`rounded-2xl border border-warelyn-border bg-white shadow-sm ${className}`}>{children}</div>;
}

export function CardHeader({ children, className = '' }) {
  return <div className={`border-b border-warelyn-border px-5 py-4 sm:px-6 ${className}`}>{children}</div>;
}

export function CardBody({ children, className = '' }) {
  return <div className={`px-5 py-5 sm:px-6 ${className}`}>{children}</div>;
}

export function MetricCard({ label, value, description, tone = 'primary' }) {
  const accents = {
    danger: 'bg-red-500',
    primary: 'bg-warelyn-primary',
    success: 'bg-warelyn-accent',
    warning: 'bg-warelyn-warning',
  };

  return (
    <Card className="overflow-hidden">
      <div className={`h-1 ${accents[tone] ?? accents.primary}`} />
      <CardBody>
        <p className="text-xs font-semibold uppercase tracking-wide text-warelyn-muted">{label}</p>
        <p className="mt-2 text-2xl font-bold tracking-tight text-warelyn-text">{value}</p>
        {description ? <p className="mt-1 text-xs text-warelyn-muted">{description}</p> : null}
      </CardBody>
    </Card>
  );
}
