import { Badge } from '../ui/Badge.jsx';

const toneByStatus = {
  VALID: 'success',
  WARNING: 'warning',
  ERROR: 'danger',
  SKIPPED: 'neutral',
  CREATED: 'success',
  UPDATED: 'primary',
};

export function ImportPreviewTable({ rows }) {
  return (
    <div className="overflow-hidden rounded-xl border border-warelyn-border">
      <table className="min-w-full divide-y divide-warelyn-border text-sm">
        <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-warelyn-muted">
          <tr>
            <th className="px-4 py-3">Row</th>
            <th className="px-4 py-3">Status</th>
            <th className="px-4 py-3">SKU</th>
            <th className="px-4 py-3">Name</th>
            <th className="px-4 py-3">Barcode</th>
            <th className="px-4 py-3">Messages</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-warelyn-border bg-white">
          {rows.map((row) => (
            <tr key={row.id}>
              <td className="px-4 py-3 text-warelyn-muted">{row.row_number}</td>
              <td className="px-4 py-3"><Badge tone={toneByStatus[row.status] ?? 'neutral'}>{row.status}</Badge></td>
              <td className="px-4 py-3 font-semibold text-warelyn-text">{row.normalized_data?.sku ?? row.raw_data?.sku ?? '-'}</td>
              <td className="px-4 py-3 text-warelyn-text">{row.normalized_data?.name ?? row.raw_data?.name ?? '-'}</td>
              <td className="px-4 py-3 text-warelyn-muted">{row.normalized_data?.barcode ?? row.raw_data?.barcode ?? '-'}</td>
              <td className="px-4 py-3 text-xs text-warelyn-muted">
                {[...(row.errors ?? []), ...(row.warnings ?? [])].join('; ') || '-'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
