import { AlertTriangle, CheckCircle2, Circle, Clock, XCircle } from 'lucide-react';

const tones = {
  neutral: 'bg-slate-100 text-slate-700 ring-slate-200',
  success: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
  warning: 'bg-amber-50 text-amber-700 ring-amber-200',
  danger: 'bg-red-50 text-red-700 ring-red-200',
  primary: 'bg-blue-50 text-warelyn-primary ring-blue-200',
  slate: 'bg-slate-900 text-white ring-slate-800',
};

const statusTones = {
  ACCEPTED_BLOCKED: 'warning',
  ACCEPTED_RESTOCK: 'success',
  ACTIVE: 'success',
  BLOCKED: 'warning',
  CANCELLED: 'danger',
  CLOSED: 'slate',
  COMMITTED: 'success',
  CONFIRMED: 'primary',
  DAMAGED: 'danger',
  DRAFT: 'neutral',
  FULFILLED: 'success',
  IN_PROGRESS: 'primary',
  OPEN: 'primary',
  PACKED: 'success',
  PARTIALLY_FULFILLED: 'warning',
  PARTIALLY_RECEIVED: 'warning',
  PENDING: 'warning',
  PICKED: 'success',
  PROCESSED: 'success',
  QC_HOLD: 'warning',
  RECEIVED: 'success',
  REJECTED: 'danger',
  RESERVED: 'primary',
  SCRAPPED: 'danger',
  SOLD: 'slate',
  SUBMITTED: 'primary',
};

const statusIcons = {
  danger: XCircle,
  neutral: Circle,
  primary: Clock,
  slate: Circle,
  success: CheckCircle2,
  warning: AlertTriangle,
};

export function Badge({ children, className = '', tone = 'neutral' }) {
  return <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ${tones[tone] ?? tones.neutral} ${className}`}>{children}</span>;
}

export function StatusBadge({ children, status, className = '' }) {
  const value = status ?? children;
  const tone = statusTones[value] ?? 'neutral';
  const Icon = statusIcons[tone] ?? Circle;
  return <Badge className={`gap-1.5 ${className}`} tone={tone}><Icon size={12} />{children ?? value}</Badge>;
}
