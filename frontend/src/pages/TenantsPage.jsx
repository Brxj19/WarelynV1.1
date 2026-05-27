import { Search, SlidersHorizontal } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';

import { Badge } from '../components/ui/Badge.jsx';
import { Button } from '../components/ui/Button.jsx';
import { ConfirmationModal } from '../components/ui/ConfirmationModal.jsx';
import { TableShell } from '../components/ui/TableShell.jsx';
import { emptyStateIllustrations } from '../lib/emptyStates.js';
import { formatDate } from '../utils/formatters.js';
import { useAuth } from '../context/AuthContext.jsx';
import * as adminService from '../services/adminService.js';

export function TenantsPage() {
  const { accessToken } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const [tenants, setTenants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState(searchParams.get('search') ?? '');
  const [statusFilter, setStatusFilter] = useState(searchParams.get('status') ?? '');
  const [confirmTarget, setConfirmTarget] = useState(null);

  const fetchTenants = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const params = new URLSearchParams();
      if (search) params.set('search', search);
      if (statusFilter) params.set('status', statusFilter);
      setSearchParams(params, { replace: true });
      const data = await adminService.listTenants(accessToken, search || undefined, statusFilter || undefined);
      setTenants(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [accessToken, search, statusFilter, setSearchParams]);

  useEffect(() => { fetchTenants(); }, [fetchTenants]);

  async function handleToggle(tenant) {
    try {
      if (tenant.status === 'DISABLED') {
        await adminService.enableTenant(accessToken, tenant.id);
      } else {
        await adminService.disableTenant(accessToken, tenant.id);
      }
      setConfirmTarget(null);
      fetchTenants();
    } catch (e) {
      setError(e.message);
      setConfirmTarget(null);
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <p className="page-kicker">Super Admin</p>
          <h1>Tenants</h1>
          <p>Manage all tenant accounts across the platform.</p>
        </div>
      </div>

      <TableShell error={error} isLoading={loading} isEmpty={tenants.length === 0} title="All Tenants" rowCount={tenants.length}
        emptyIllustration={(search || statusFilter) ? emptyStateIllustrations.noResult : emptyStateIllustrations.users}
        emptyTitle={(search || statusFilter) ? 'No matching tenants found' : 'No tenants yet'}
        emptyDescription={(search || statusFilter) ? 'Adjust your search or status filter.' : 'Tenants will appear here once accounts are registered.'}
        emptySecondaryActionLabel={(search || statusFilter) ? 'Clear filters' : undefined}
        onEmptySecondaryAction={(search || statusFilter) ? () => { setSearch(''); setStatusFilter(''); } : undefined}
        toolbar={
          <div className="flex gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-warelyn-muted" size={16} />
              <input className="block w-full rounded-lg border border-warelyn-border bg-white py-2 pl-9 pr-3 text-sm shadow-sm outline-none focus:border-warelyn-primary focus:ring-4 focus:ring-blue-900/10" placeholder="Search tenants..." value={search} onChange={(e) => setSearch(e.target.value)} />
            </div>
            <select className="rounded-lg border border-warelyn-border bg-white px-3 py-2 text-sm shadow-sm outline-none focus:border-warelyn-primary focus:ring-4 focus:ring-blue-900/10" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
              <option value="">All statuses</option>
              <option value="ACTIVE">Active</option>
              <option value="DISABLED">Disabled</option>
            </select>
          </div>
        }
      >
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-warelyn-border text-left text-xs font-semibold uppercase tracking-wide text-warelyn-muted">
              <th className="py-3 pl-4 pr-2">Company</th>
              <th className="px-2 py-3">Email</th>
              <th className="px-2 py-3">Status</th>
              <th className="px-2 py-3">Users</th>
              <th className="px-2 py-3">Products</th>
              <th className="px-2 py-3">Created</th>
              <th className="px-2 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {tenants.map((tenant) => (
              <tr className="border-b border-warelyn-border last:border-0 hover:bg-slate-50" key={tenant.id}>
                <td className="py-3 pl-4 pr-2">
                  <Link className="font-medium text-warelyn-primary hover:underline" to={`/admin/tenants/${tenant.id}`}>{tenant.company_name}</Link>
                </td>
                <td className="px-2 py-3 text-warelyn-muted">{tenant.contact_email}</td>
                <td className="px-2 py-3"><Badge tone={tenant.status === 'ACTIVE' ? 'success' : 'danger'}>{tenant.status}</Badge></td>
                <td className="px-2 py-3">{tenant.users_count}</td>
                <td className="px-2 py-3">{tenant.products_count}</td>
                <td className="px-2 py-3 text-warelyn-muted">{formatDate(tenant.created_at)}</td>
                <td className="px-2 py-3 text-right">
                  <Button onClick={() => setConfirmTarget(tenant)} size="sm" variant={tenant.status === 'DISABLED' ? 'success' : 'danger'}>
                    {tenant.status === 'DISABLED' ? 'Enable' : 'Disable'}
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </TableShell>

      <ConfirmationModal
        cancelLabel="Cancel"
        confirmLabel={confirmTarget?.status === 'DISABLED' ? 'Enable Tenant' : 'Disable Tenant'}
        description={confirmTarget ? `Are you sure you want to ${confirmTarget.status === 'DISABLED' ? 'enable' : 'disable'} ${confirmTarget.company_name}?` : ''}
        impact={confirmTarget?.status !== 'DISABLED' ? 'Users of this tenant will lose access until re-enabled.' : ''}
        onCancel={() => setConfirmTarget(null)}
        onConfirm={() => handleToggle(confirmTarget)}
        open={!!confirmTarget}
        title={confirmTarget?.status === 'DISABLED' ? 'Enable Tenant' : 'Disable Tenant'}
        variant={confirmTarget?.status === 'DISABLED' ? 'primary' : 'danger'}
      />
    </div>
  );
}
