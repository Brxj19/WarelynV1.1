import { Activity, AlertTriangle, BarChart3, Boxes, Download, PackageCheck, Search, ShieldCheck, Warehouse } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';

import { Badge, StatusBadge } from '../components/ui/Badge.jsx';
import { Button } from '../components/ui/Button.jsx';
import { Card, CardBody, CardHeader } from '../components/ui/Card.jsx';
import { PageHeader } from '../components/ui/PageHeader.jsx';
import { ScreenToolbar } from '../components/ui/ScreenToolbar.jsx';
import { SortableHeader } from '../components/ui/SortableHeader.jsx';
import { TableShell } from '../components/ui/TableShell.jsx';
import { emptyStateIllustrations } from '../lib/emptyStates.js';
import { formatDate, formatDateTime, formatDecimal, formatMoney, formatNumber, titleCaseStatus } from '../utils/formatters.js';
import { getNextSort, inferSortType, sortRows } from '../utils/table.js';
import { useAuth } from '../context/AuthContext.jsx';
import { useTenantSettings } from '../context/TenantSettingsContext.jsx';
import * as reportsService from '../services/reportsService.js';

export const reportLinks = [
  ['Inventory summary', '/reports/inventory-summary', 'Top-level stock, value, low-stock, expiry, blocked, and reconciliation indicators.', Boxes],
  ['Warehouse stock', '/reports/warehouse-stock', 'Stock projection by warehouse and SKU.', Warehouse],
  ['Location stock', '/reports/location-stock', 'Stock projection by bin/location and SKU.', Warehouse],
  ['Stock movements', '/reports/stock-movements', 'Ledger-backed stock movement history.', Activity],
  ['Low stock', '/reports/low-stock', 'Products at or below reorder level.', AlertTriangle],
  ['Product valuation', '/reports/product-valuation', 'Current-cost stock valuation from backend data.', BarChart3],
  ['Batch expiry', '/reports/batch-expiry', 'Expired and expiring batch visibility.', PackageCheck],
  ['Serial status', '/reports/serial-status', 'Serial-level stock state.', PackageCheck],
  ['Blocked stock', '/reports/blocked-stock', 'Return, batch, and serial non-sellable stock.', ShieldCheck],
  ['Reconciliation', '/reports/reconciliation', 'Ledger-to-projection mismatch visibility.', ShieldCheck],
];

const reportGroups = [
  ['Inventory', ['Inventory summary', 'Warehouse stock', 'Location stock', 'Product valuation']],
  ['Stock Health', ['Low stock']],
  ['Traceability', ['Batch expiry', 'Serial status']],
  ['Operations', ['Stock movements', 'Blocked stock']],
  ['Reconciliation', ['Reconciliation']],
];

export function ReportsPage() {
  return (
    <div className="space-y-6">
      <PageHeader kicker="Reports" title="Reports overview" description="Read-only reporting from backend inventory, ledger, batch, serial, returns, purchasing, and sales data. Reports expose operational truth without frontend stock calculation." />
      <div className="space-y-6">
        {reportGroups.map(([group, names]) => (
          <section key={group}>
            <h2 className="mb-3 text-sm font-bold uppercase tracking-[0.16em] text-warelyn-muted">{group}</h2>
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {reportLinks
                .filter(([title]) => names.includes(title))
                .map(([title, to, description, Icon]) => (
                  <Link className="metric-link-card" key={to} to={to}>
                    <div className="metric-link-card-body">
                      <div className="metric-link-card-icon">
                        <Icon size={20} />
                      </div>
                      <p className="metric-link-card-label">Open report</p>
                      <h2 className="mt-3 text-xl font-semibold text-warelyn-text">{title}</h2>
                      <p className="metric-link-card-copy">{description}</p>
                      <span className="metric-link-card-status primary">Open report</span>
                    </div>
                  </Link>
                ))}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}

export function SimpleReportPage({ columns, description, filters = [], load, loadRows, normalize = (row) => row, summary, title }) {
  const { accessToken } = useAuth();
  const { currency } = useTenantSettings();
  const [data, setData] = useState(null);
  const [query, setQuery] = useState({});
  const [search, setSearch] = useState('');
  const [sortState, setSortState] = useState(() => ({
    key: columns[0]?.key ?? '',
    direction: 'asc',
  }));
  const [pageSize, setPageSize] = useState(10);
  const [currentPage, setCurrentPage] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    async function run() {
      setIsLoading(true);
      setError('');
      try {
        const cleanQuery = Object.fromEntries(Object.entries(query).filter(([, v]) => v));
        setData(await load(accessToken, cleanQuery));
      } catch (loadError) {
        setError(loadError.message);
      } finally {
        setIsLoading(false);
      }
    }
    run();
  }, [accessToken, load, JSON.stringify(query)]);
  const sourceRows =
    data === null || data === undefined
      ? []
      : loadRows
      ? loadRows(data)
      : data;
  const normalizedRows = Array.isArray(sourceRows) ? sourceRows.map(normalize) : [];
  const rows = useMemo(() => {
    const value = search.trim().toLowerCase();
    if (!value) return normalizedRows;
    return normalizedRows.filter((row) =>
      columns.some((column) => {
        const raw = row[column.key];
        return raw !== null && raw !== undefined && String(raw).toLowerCase().includes(value);
      }),
    );
  }, [columns, normalizedRows, search]);
  const sortedRows = useMemo(
    () =>
      sortRows(
        rows,
        sortState,
        Object.fromEntries(
          columns.map((column) => [
            column.key,
            {
              type: column.type ?? inferSortType(column.key),
              accessor: (row) => row[column.key],
            },
          ]),
        ),
      ),
    [columns, rows, sortState],
  );
  useEffect(() => {
    setCurrentPage(1);
  }, [search, query, sortState, pageSize, normalizedRows.length]);
  const totalPages = Math.max(1, Math.ceil(sortedRows.length / pageSize));
  const safePage = Math.min(currentPage, totalPages);
  const pagedRows = useMemo(() => {
    const start = (safePage - 1) * pageSize;
    return sortedRows.slice(start, start + pageSize);
  }, [pageSize, safePage, sortedRows]);
  const activeFilters = [
    search ? { key: 'search', label: `Search: ${search}`, onRemove: () => setSearch('') } : null,
    ...filters
      .map((filter) => {
        const value = query[filter.key];
        if (!value) return null;
        return {
          key: filter.key,
          label: `${filter.label}: ${value}`,
          onRemove: () => setQuery((current) => ({ ...current, [filter.key]: '' })),
        };
      })
      .filter(Boolean),
  ].filter(Boolean);
  const hasActiveFilters = activeFilters.length > 0;

  async function exportCsv() {
    const slug = window.location.pathname.split('/').pop();
    const cleanQuery = Object.fromEntries(Object.entries(query).filter(([, v]) => v));
    const blob = await reportsService.downloadReportCsv(accessToken, slug, cleanQuery);
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `${slug}.csv`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="space-y-6">
      <PageHeader
        backTo="/reports"
        kicker="Report"
        title={title}
        description={description}
        actions={
          <Button variant="secondary" onClick={exportCsv}>
            <Download size={16} />
            Export CSV
          </Button>
        }
      />
      {filters.length > 0 && (
        <Card>
          <CardBody>
            <div className="flex flex-wrap items-end gap-4">
              {filters.map((filter) =>
                filter.type === 'date' ? (
                  <label className="block min-w-[160px]" key={filter.key}>
                    <span className="mb-1.5 block text-xs font-bold uppercase tracking-[0.16em] text-warelyn-muted">{filter.label}</span>
                    <input
                      type="date"
                      className="block w-full rounded-xl border border-warelyn-border bg-white px-3 py-2.5 text-sm"
                      onChange={(e) => setQuery((current) => ({ ...current, [filter.key]: e.target.value }))}
                      value={query[filter.key] ?? ''}
                    />
                  </label>
                ) : filter.type === 'number' ? (
                  <label className="block min-w-[120px]" key={filter.key}>
                    <span className="mb-1.5 block text-xs font-bold uppercase tracking-[0.16em] text-warelyn-muted">{filter.label}</span>
                    <input
                      type="number"
                      min="1"
                      placeholder={filter.placeholder ?? ''}
                      className="block w-full rounded-xl border border-warelyn-border bg-white px-3 py-2.5 text-sm"
                      onChange={(e) => setQuery((current) => ({ ...current, [filter.key]: e.target.value }))}
                      value={query[filter.key] ?? ''}
                    />
                  </label>
                ) : (
                  <label className="block min-w-[160px]" key={filter.key}>
                    <span className="mb-1.5 block text-xs font-bold uppercase tracking-[0.16em] text-warelyn-muted">{filter.label}</span>
                    <select
                      className="block w-full rounded-xl border border-warelyn-border bg-white px-3 py-2.5 text-sm"
                      onChange={(e) => setQuery((current) => ({ ...current, [filter.key]: e.target.value }))}
                      value={query[filter.key] ?? ''}
                    >
                      <option value="">{filter.emptyLabel ?? `All`}</option>
                      {(filter.options ?? []).map((option) => (
                        <option key={option.value} value={option.value}>{option.label}</option>
                      ))}
                    </select>
                  </label>
                )
              )}
              {hasActiveFilters && (
                <Button variant="ghost" onClick={() => { setQuery({}); setSearch(''); }}>
                  Clear filters
                </Button>
              )}
            </div>
          </CardBody>
        </Card>
      )}
      {summary && data !== null && data !== undefined
        ? summary(data)
        : null}
      <TableShell
        description={`${sortedRows.length} backend-returned row(s)`}
        emptyDescription={hasActiveFilters ? 'Adjust your date range, module, or report filters.' : 'Reports will appear after inventory, sales, or purchase activity is recorded.'}
        emptyIllustration={hasActiveFilters ? emptyStateIllustrations.noResult : emptyStateIllustrations.reports}
        emptySecondaryActionLabel={hasActiveFilters ? 'Clear filters' : undefined}
        emptyTitle={hasActiveFilters ? 'No matching report data found' : 'No report data available'}
        error={error}
        isEmpty={sortedRows.length === 0}
        isLoading={isLoading}
        onEmptySecondaryAction={hasActiveFilters ? () => { setQuery({}); setSearch(''); } : undefined}
        rowCount={sortedRows.length}
        title="Results"
        toolbar={
          <ScreenToolbar
            activeFilters={activeFilters}
            onReset={
              hasActiveFilters
                ? () => {
                    setQuery({});
                    setSearch('');
                  }
                : undefined
            }
            onSearchChange={setSearch}
            searchPlaceholder="Search rows"
            searchValue={search}
          />
        }
      >
        <table>
          <thead>
            <tr>
              {columns.map((column) => {
                const isNumeric = column.numeric ?? inferSortType(column.key) === 'number';
                return (
                <th className={isNumeric ? 'text-right' : ''} key={column.key}>
                  <SortableHeader
                    align={isNumeric ? 'right' : 'left'}
                    label={column.label}
                    onSort={(key) => setSortState((current) => getNextSort(current, key))}
                    sortKey={column.key}
                    sortState={sortState}
                  />
                </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {pagedRows.map((row, index) => (
              <tr key={row.id ?? index}>
                {columns.map((column) => (
                  <td className={(column.numeric ?? inferSortType(column.key) === 'number') ? 'number-cell whitespace-nowrap' : 'whitespace-nowrap'} key={column.key}>
                    {column.render ? column.render(row[column.key], row, currency) : renderReportCell(row[column.key], column.key, currency)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </TableShell>
      {sortedRows.length > 0 ? (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-warelyn-border bg-white px-4 py-3">
          <p className="text-xs text-warelyn-muted">
            Showing {(safePage - 1) * pageSize + 1}-{Math.min(safePage * pageSize, sortedRows.length)} of {sortedRows.length}
          </p>
          <div className="flex items-center gap-2">
            <label className="text-xs font-medium text-warelyn-muted" htmlFor="report-page-size">Rows</label>
            <select
              id="report-page-size"
              className="rounded-lg border border-warelyn-border bg-white px-2 py-1.5 text-xs text-warelyn-text"
              onChange={(event) => setPageSize(Number(event.target.value))}
              value={pageSize}
            >
              {[10, 25, 50, 100].map((size) => (
                <option key={size} value={size}>{size}</option>
              ))}
            </select>
            <button
              className="rounded-lg border border-warelyn-border px-3 py-1.5 text-xs font-semibold text-warelyn-text disabled:cursor-not-allowed disabled:opacity-50"
              disabled={safePage <= 1}
              onClick={() => setCurrentPage((page) => Math.max(1, page - 1))}
              type="button"
            >
              Prev
            </button>
            <span className="text-xs font-medium text-warelyn-muted">Page {safePage} / {totalPages}</span>
            <button
              className="rounded-lg border border-warelyn-border px-3 py-1.5 text-xs font-semibold text-warelyn-text disabled:cursor-not-allowed disabled:opacity-50"
              disabled={safePage >= totalPages}
              onClick={() => setCurrentPage((page) => Math.min(totalPages, page + 1))}
              type="button"
            >
              Next
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}

function renderReportCell(value, key, currency) {
  if (value === null || value === undefined || value === '') return '-';
  if (key.includes('created_at')) return formatDateTime(value);
  if (key.endsWith('_date') || key === 'expiry_date' || key === 'order_date') return formatDate(value);
  if (key.includes('status') || key === 'movement_type' || key === 'reference_type') return <StatusBadge status={value}>{titleCaseStatus(value)}</StatusBadge>;
  if (['sku', 'barcode', 'ledger_id', 'reference_id', 'batch_number', 'serial_number'].includes(key)) return <span className="mono-cell">{value}</span>;
  if (key.includes('value') || key.includes('cost') || key.includes('price') || key.includes('amount') || key.includes('total')) return formatMoney(value, currency);
  if (key.includes('units') || key.includes('count')) return formatNumber(value, { maximumFractionDigits: 0 });
  if (key === 'on_hand') return formatNumber(value, { maximumFractionDigits: 0 });
  if (key.includes('quantity') || key.includes('on_hand') || key.includes('reserved') || key.includes('available') || key.includes('delta')) return formatDecimal(value);
  return value;
}
