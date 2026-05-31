import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

import { Badge } from '../components/ui/Badge.jsx';
import { Button } from '../components/ui/Button.jsx';
import { Card, CardBody, CardHeader, MetricCard } from '../components/ui/Card.jsx';
import { ConfirmationModal } from '../components/ui/ConfirmationModal.jsx';
import { ErrorState } from '../components/ui/ErrorState.jsx';
import { LoadingState } from '../components/ui/LoadingState.jsx';
import { PageHeader } from '../components/ui/PageHeader.jsx';
import { formatDate } from '../utils/formatters.js';
import { useAuth } from '../context/AuthContext.jsx';
import * as adminService from '../services/adminService.js';

export function TenantDetailPage() {
  const { accessToken } = useAuth();
  const { id } = useParams();
  const navigate = useNavigate();
  const [tenant, setTenant] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [confirmToggle, setConfirmToggle] = useState(false);

  useEffect(() => {
    adminService.getTenantDetail(accessToken, id).then(setTenant).catch((e) => setError(e.message)).finally(() => setLoading(false));
  }, [accessToken, id]);

  async function handleToggle() {
    try {
      if (tenant.status === 'DISABLED') {
        await adminService.enableTenant(accessToken, tenant.id);
      } else {
        await adminService.disableTenant(accessToken, tenant.id);
      }
      setConfirmToggle(false);
      const updated = await adminService.getTenantDetail(accessToken, id);
      setTenant(updated);
    } catch (e) {
      setError(e.message);
      setConfirmToggle(false);
    }
  }

  if (loading) return <LoadingState message="Loading tenant details..." />;
  if (error) return <ErrorState description={error} />;
  if (!tenant) return <ErrorState description="Tenant not found." />;

  return (
    <div>
      <PageHeader
        backLabel="All Tenants"
        backTo="/admin/tenants"
        description="View and manage this tenant account."
        kicker="Super Admin"
        title={tenant.company_name}
        status={<Badge tone={tenant.status === 'ACTIVE' ? 'success' : 'danger'}>{tenant.status}</Badge>}
        actions={
          <Button onClick={() => setConfirmToggle(true)} variant={tenant.status === 'DISABLED' ? 'success' : 'danger'}>
            {tenant.status === 'DISABLED' ? 'Enable Tenant' : 'Disable Tenant'}
          </Button>
        }
      />

      <div className="mb-6 grid gap-4 sm:grid-cols-3">
        <MetricCard label="Users" tone="primary" value={tenant.users_count} />
        <MetricCard label="Products" tone="success" value={tenant.products_count} />
        <MetricCard label="Warehouses" tone="warning" value={tenant.warehouses_count ?? 0} />
      </div>

      <Card>
        <CardHeader><h3 className="text-sm font-bold text-warelyn-text">Company Profile</h3></CardHeader>
        <CardBody>
          <dl className="grid gap-4 sm:grid-cols-2">
            <div><dt className="text-xs font-semibold uppercase tracking-wide text-warelyn-muted">Company Name</dt><dd className="mt-0.5 text-sm font-medium text-warelyn-text">{tenant.company_name}</dd></div>
            <div><dt className="text-xs font-semibold uppercase tracking-wide text-warelyn-muted">Contact Email</dt><dd className="mt-0.5 text-sm font-medium text-warelyn-text">{tenant.contact_email}</dd></div>
            <div><dt className="text-xs font-semibold uppercase tracking-wide text-warelyn-muted">Phone</dt><dd className="mt-0.5 text-sm font-medium text-warelyn-text">{tenant.phone ?? '-'}</dd></div>
            <div><dt className="text-xs font-semibold uppercase tracking-wide text-warelyn-muted">Address</dt><dd className="mt-0.5 text-sm font-medium text-warelyn-text">{tenant.address ?? '-'}</dd></div>
            <div><dt className="text-xs font-semibold uppercase tracking-wide text-warelyn-muted">GST Number</dt><dd className="mt-0.5 text-sm font-medium text-warelyn-text">{tenant.gst_number ?? '-'}</dd></div>
            <div><dt className="text-xs font-semibold uppercase tracking-wide text-warelyn-muted">Business Type</dt><dd className="mt-0.5 text-sm font-medium text-warelyn-text">{tenant.business_type ?? '-'}</dd></div>
            <div><dt className="text-xs font-semibold uppercase tracking-wide text-warelyn-muted">Created</dt><dd className="mt-0.5 text-sm font-medium text-warelyn-text">{formatDate(tenant.created_at)}</dd></div>
            <div><dt className="text-xs font-semibold uppercase tracking-wide text-warelyn-muted">Updated</dt><dd className="mt-0.5 text-sm font-medium text-warelyn-text">{formatDate(tenant.updated_at)}</dd></div>
          </dl>
        </CardBody>
      </Card>

      <ConfirmationModal
        cancelLabel="Cancel"
        confirmLabel={tenant.status === 'DISABLED' ? 'Enable Tenant' : 'Disable Tenant'}
        description={`Are you sure you want to ${tenant.status === 'DISABLED' ? 'enable' : 'disable'} ${tenant.company_name}?`}
        impact={tenant.status !== 'DISABLED' ? 'Users of this tenant will lose access until re-enabled.' : ''}
        onCancel={() => setConfirmToggle(false)}
        onConfirm={handleToggle}
        open={confirmToggle}
        title={tenant.status === 'DISABLED' ? 'Enable Tenant' : 'Disable Tenant'}
        variant={tenant.status === 'DISABLED' ? 'primary' : 'danger'}
      />
    </div>
  );
}
