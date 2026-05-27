import { X } from 'lucide-react';

export function MetadataDrawer({ data, onClose, open }) {
  if (!open) return null;
  let parsed;
  try {
    parsed = typeof data === 'string' ? JSON.parse(data) : data;
  } catch {
    parsed = { raw: data };
  }
  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-950/25 backdrop-blur-sm" onClick={onClose} role="presentation">
      <div aria-modal="true" className="w-full max-w-lg overflow-y-auto border-l border-warelyn-border bg-white p-6 shadow-2xl" onClick={(e) => e.stopPropagation()} role="dialog">
        <div className="mb-6 flex items-center justify-between">
          <h2 className="text-lg font-bold tracking-tight text-warelyn-text">Audit Metadata</h2>
          <button className="rounded-lg p-1.5 text-warelyn-muted hover:bg-slate-100 hover:text-warelyn-text" onClick={onClose} type="button">
            <X size={18} />
          </button>
        </div>
        <dl className="space-y-4">
          {Object.entries(parsed ?? {}).map(([key, value]) => (
            <div key={key}>
              <dt className="text-xs font-semibold uppercase tracking-wide text-warelyn-muted">{key}</dt>
              <dd className="mt-0.5 text-sm font-medium text-warelyn-text">{value === null || value === undefined ? <span className="italic text-warelyn-muted">null</span> : String(value)}</dd>
            </div>
          ))}
        </dl>
      </div>
    </div>
  );
}
