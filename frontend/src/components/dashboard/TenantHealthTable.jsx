import { Circle, Package, ShoppingCart, Users, Warehouse } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';

import { Badge } from '../ui/Badge.jsx';
import { Button } from '../ui/Button.jsx';
import { Card, CardBody, CardHeader } from '../ui/Card.jsx';
import { EmptyState } from '../ui/EmptyState.jsx';
import { PaginationControls } from '../ui/PaginationControls.jsx';
import { formatDate } from '../../utils/formatters.js';

function OnboardingFlag({ done, icon: Icon, label }) {
  return (
    <span className="inline-flex items-center gap-1 text-xs text-warelyn-muted" title={label}>
      <span className={done ? 'text-emerald-600' : 'text-slate-400'}>
        {done ? <Icon size={13} /> : <Circle size={13} />}
      </span>
      {label}
    </span>
  );
}

export function TenantHealthTable({
  title,
  rows = [],
  type = 'active',
  onEnable,
  onDisable,
  sortValue,
  onSortChange,
  statusFilter,
  onStatusFilterChange,
}) {
  const isActiveTable = type === 'active';
  const [query, setQuery] = useState('');
  const filteredRows = useMemo(() => {
    const normalizedQuery = query.toLowerCase().trim();
    if (!normalizedQuery) return rows;
    return rows.filter((row) => {
      const haystack = [
        row.company_name,
        row.contact_email,
        row.status,
        row.user_count,
        row.product_count,
        row.event_count,
      ]
        .filter((value) => value !== null && value !== undefined)
        .join(' ')
        .toLowerCase();
      return haystack.includes(normalizedQuery);
    });
  }, [query, rows]);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const pageCount = Math.max(1, Math.ceil(filteredRows.length / pageSize));
  const pagedRows = useMemo(() => {
    const start = (page - 1) * pageSize;
    return filteredRows.slice(start, start + pageSize);
  }, [filteredRows, page, pageSize]);

  useEffect(() => {
    if (page > pageCount) {
      setPage(pageCount);
    }
  }, [page, pageCount]);

  useEffect(() => {
    setPage(1);
  }, [query]);

  return (
    <Card>
      <CardHeader className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-warelyn-text">{title}</h2>
          {isActiveTable ? (
            <div className="flex items-center gap-2">
              <select
                className="rounded-md border border-warelyn-border bg-white px-2 py-1 text-xs text-warelyn-text"
                onChange={(event) => onSortChange?.(event.target.value)}
                value={sortValue ?? 'event_count'}
              >
                <option value="event_count">Sort: Events</option>
                <option value="user_count">Sort: Users</option>
                <option value="product_count">Sort: Products</option>
              </select>
              <select
                className="rounded-md border border-warelyn-border bg-white px-2 py-1 text-xs text-warelyn-text"
                onChange={(event) => onStatusFilterChange?.(event.target.value)}
                value={statusFilter ?? 'ALL'}
              >
                <option value="ALL">All</option>
                <option value="ACTIVE">Active</option>
                <option value="DISABLED">Disabled</option>
              </select>
            </div>
          ) : null}
        </div>
        <input
          className="w-full rounded-md border border-warelyn-border bg-white px-3 py-2 text-sm text-warelyn-text placeholder:text-warelyn-muted focus:border-warelyn-primary focus:outline-none"
          onChange={(event) => setQuery(event.target.value)}
          placeholder={isActiveTable ? 'Filter tenants by company, status, users...' : 'Filter tenants by company or email...'}
          value={query}
        />
      </CardHeader>
      <CardBody className="px-0 py-0">
        {filteredRows.length === 0 ? (
          <div className="p-6">
            <EmptyState description={query ? 'No tenants match your filters.' : 'No tenants to display right now.'} title="No tenant rows" />
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-warelyn-muted">
                  <tr>
                    <th className="px-4 py-3">Company</th>
                    {isActiveTable ? <th className="px-4 py-3">Users</th> : <th className="px-4 py-3">Email</th>}
                    {isActiveTable ? <th className="px-4 py-3">Products</th> : <th className="px-4 py-3">Onboarding</th>}
                    {isActiveTable ? <th className="px-4 py-3">Events (30d)</th> : <th className="px-4 py-3">Created</th>}
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {pagedRows.map((row) => (
                    <tr className="border-t border-warelyn-border" key={row.tenant_id}>
                      <td className="px-4 py-3 font-medium text-warelyn-text">
                        <Link className="hover:text-warelyn-primary hover:underline" to={`/admin/tenants/${row.tenant_id}`}>
                          {row.company_name}
                        </Link>
                      </td>
                      {isActiveTable ? <td className="px-4 py-3">{row.user_count}</td> : <td className="px-4 py-3">{row.contact_email}</td>}
                      {isActiveTable ? (
                        <td className="px-4 py-3">{row.product_count}</td>
                      ) : (
                        <td className="px-4 py-3">
                          <div className="flex flex-wrap gap-2">
                            <OnboardingFlag done={row.has_users} icon={Users} label="Users" />
                            <OnboardingFlag done={row.has_products} icon={Package} label="Products" />
                            <OnboardingFlag done={row.has_warehouse} icon={Warehouse} label="Warehouse" />
                            <OnboardingFlag done={row.has_orders} icon={ShoppingCart} label="Orders" />
                          </div>
                        </td>
                      )}
                      {isActiveTable ? <td className="px-4 py-3">{row.event_count}</td> : <td className="px-4 py-3">{formatDate(row.created_at)}</td>}
                      <td className="px-4 py-3">
                        <Badge tone={row.status === 'ACTIVE' ? 'success' : 'danger'}>{row.status}</Badge>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <Link className="text-xs font-semibold text-warelyn-primary hover:underline" to={`/admin/tenants/${row.tenant_id}`}>
                            View
                          </Link>
                          {row.status === 'ACTIVE' ? (
                            <Button className="px-2 py-1 text-xs" onClick={() => onDisable?.(row.tenant_id)} variant="danger">
                              Disable
                            </Button>
                          ) : (
                            <Button className="px-2 py-1 text-xs" onClick={() => onEnable?.(row.tenant_id)} variant="accent">
                              Enable
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <PaginationControls page={page} pageCount={pageCount} pageSize={pageSize} setPage={setPage} setPageSize={setPageSize} totalRows={filteredRows.length} />
          </>
        )}
      </CardBody>
    </Card>
  );
}
