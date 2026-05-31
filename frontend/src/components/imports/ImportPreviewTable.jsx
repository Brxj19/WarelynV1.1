import { useEffect, useMemo, useState } from 'react';

import { Badge } from '../ui/Badge.jsx';
import { PaginationControls } from '../ui/PaginationControls.jsx';

const toneByStatus = {
  VALID: 'success',
  WARNING: 'warning',
  ERROR: 'danger',
  SKIPPED: 'neutral',
  CREATED: 'success',
  UPDATED: 'primary',
};

export function ImportPreviewTable({ rows }) {
  const [query, setQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const availableStatuses = useMemo(() => {
    return Array.from(new Set(rows.map((row) => row.status).filter(Boolean)));
  }, [rows]);
  const filteredRows = useMemo(() => {
    const normalizedQuery = query.toLowerCase().trim();
    return rows.filter((row) => {
      const statusMatch = statusFilter === 'ALL' || row.status === statusFilter;
      if (!statusMatch) return false;
      if (!normalizedQuery) return true;
      const haystack = [
        row.row_number,
        row.status,
        row.normalized_data?.sku,
        row.raw_data?.sku,
        row.normalized_data?.name,
        row.raw_data?.name,
        row.normalized_data?.barcode,
        row.raw_data?.barcode,
        ...(row.errors ?? []),
        ...(row.warnings ?? []),
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase();
      return haystack.includes(normalizedQuery);
    });
  }, [query, rows, statusFilter]);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const pageCount = Math.max(1, Math.ceil(filteredRows.length / pageSize));
  const pagedRows = useMemo(() => {
    const start = (page - 1) * pageSize;
    return filteredRows.slice(start, start + pageSize);
  }, [filteredRows, page, pageSize]);

  useEffect(() => {
    if (page > pageCount) setPage(pageCount);
  }, [page, pageCount]);

  useEffect(() => {
    setPage(1);
  }, [query, statusFilter]);

  return (
    <div className="overflow-hidden rounded-xl border border-warelyn-border">
      <div className="flex flex-col gap-2 border-b border-warelyn-border bg-slate-50 px-4 py-3 sm:flex-row sm:items-center">
        <input
          className="w-full rounded-md border border-warelyn-border bg-white px-3 py-2 text-sm text-warelyn-text placeholder:text-warelyn-muted focus:border-warelyn-primary focus:outline-none"
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Filter rows..."
          value={query}
        />
        <select
          className="rounded-md border border-warelyn-border bg-white px-3 py-2 text-sm text-warelyn-text"
          onChange={(event) => setStatusFilter(event.target.value)}
          value={statusFilter}
        >
          <option value="ALL">All statuses</option>
          {availableStatuses.map((status) => (
            <option key={status} value={status}>
              {status}
            </option>
          ))}
        </select>
      </div>
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
          {pagedRows.map((row) => (
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
      <PaginationControls page={page} pageCount={pageCount} pageSize={pageSize} setPage={setPage} setPageSize={setPageSize} totalRows={filteredRows.length} />
    </div>
  );
}
