import { Activity, Database, RefreshCw, ShieldCheck } from 'lucide-react';

import { Card, CardBody, CardHeader } from '../ui/Card.jsx';

function statusTone(type, value) {
  if (type === 'db') {
    if (value === 'connected') return 'bg-emerald-500';
    if (value === 'degraded') return 'bg-amber-500';
    return 'bg-red-500';
  }
  if (type === 'app') {
    if (value === 'healthy') return 'bg-emerald-500';
    if (value === 'degraded') return 'bg-amber-500';
    return 'bg-red-500';
  }
  if (type === 'ledger') {
    return value ? 'bg-emerald-500' : 'bg-red-500';
  }
  return 'bg-slate-400';
}

function relativeTimeLabel(value) {
  if (!value) return '-';
  const then = new Date(value);
  if (Number.isNaN(then.getTime())) return String(value);
  const deltaMs = Date.now() - then.getTime();
  const minute = 60_000;
  const hour = 60 * minute;
  if (deltaMs < minute) return 'just now';
  if (deltaMs < hour) return `${Math.floor(deltaMs / minute)} mins ago`;
  return `${Math.floor(deltaMs / hour)} hrs ago`;
}

export function PlatformHealthPanel({ health, onRefresh }) {
  return (
    <Card>
      <CardHeader className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-warelyn-text">Platform health</h2>
        <button
          className="inline-flex items-center gap-1 rounded-md border border-warelyn-border bg-white px-2 py-1 text-xs font-semibold text-warelyn-primary transition hover:bg-slate-50"
          onClick={onRefresh}
          type="button"
        >
          <RefreshCw size={13} />
          Check now
        </button>
      </CardHeader>
      <CardBody>
        <div className="grid gap-3 sm:grid-cols-3">
          <p className="inline-flex items-center gap-2 text-sm text-warelyn-text">
            <Database size={15} className="text-warelyn-primary" />
            <span className={`h-2.5 w-2.5 rounded-full ${statusTone('db', health?.database_status)}`} />
            Database: <strong>{health?.database_status ?? 'unknown'}</strong>
          </p>
          <p className="inline-flex items-center gap-2 text-sm text-warelyn-text">
            <Activity size={15} className="text-warelyn-primary" />
            <span className={`h-2.5 w-2.5 rounded-full ${statusTone('app', health?.app_status)}`} />
            App: <strong>{health?.app_status ?? 'unknown'}</strong>
          </p>
          <p className="inline-flex items-center gap-2 text-sm text-warelyn-text">
            <ShieldCheck size={15} className="text-warelyn-primary" />
            <span className={`h-2.5 w-2.5 rounded-full ${statusTone('ledger', health?.ledger_integrity_ok ?? true)}`} />
            Ledger: <strong>{health?.ledger_integrity_ok ? 'OK' : 'Issues'}</strong>
          </p>
        </div>
        <p className="mt-3 text-xs text-warelyn-muted">Last checked: {relativeTimeLabel(health?.timestamp)}</p>
      </CardBody>
    </Card>
  );
}

