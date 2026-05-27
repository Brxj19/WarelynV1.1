import { Activity, Boxes, Layers, Server, Users } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { Card, CardBody, MetricCard } from '../components/ui/Card.jsx';
import { ErrorState } from '../components/ui/ErrorState.jsx';
import { LoadingState } from '../components/ui/LoadingState.jsx';
import { useAuth } from '../context/AuthContext.jsx';
import * as adminService from '../services/adminService.js';

export function AdminDashboardPage() {
  const { accessToken } = useAuth();
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    adminService.getPlatformSummary(accessToken).then(setSummary).catch((e) => setError(e.message)).finally(() => setLoading(false));
  }, [accessToken]);

  if (loading) return <LoadingState message="Loading platform console..." />;
  if (error) return <ErrorState description={error} />;

  return (
    <div>
      <div className="page-header">
        <div>
          <p className="page-kicker">Super Admin</p>
          <h1>Platform Console</h1>
          <p>Overview of all tenants, users, and system health.</p>
        </div>
      </div>

      <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard description="Total tenants across platform" label="Total Tenants" tone="primary" value={summary?.total_tenants ?? 0} />
        <MetricCard description="Active tenants" label="Active Tenants" tone="success" value={summary?.active_tenants ?? 0} />
        <MetricCard description="Disabled tenants" label="Disabled Tenants" tone="danger" value={summary?.disabled_tenants ?? 0} />
        <MetricCard description="Platform-wide users" label="Total Users" tone="primary" value={summary?.total_users ?? 0} />
        <MetricCard description="All products across tenants" label="Total Products" tone="success" value={summary?.total_products ?? 0} />
        <MetricCard description="Stock ledger entries" label="Ledger Entries" tone="warning" value={summary?.stock_ledger_count ?? 0} />
        <MetricCard description="Recent audit events" label="Recent Audit Events" tone="neutral" value={summary?.recent_audit_events ?? 0} />
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Link className="block" to="/admin/tenants">
          <Card className="cursor-pointer transition hover:shadow-md">
            <CardBody>
              <div className="mb-2 flex items-center gap-2 text-warelyn-primary">
                <Layers size={20} />
                <h3 className="text-sm font-bold">Tenants</h3>
              </div>
              <p className="text-xs text-warelyn-muted">Manage all tenant accounts</p>
            </CardBody>
          </Card>
        </Link>
        <Link className="block" to="/admin/audit-logs">
          <Card className="cursor-pointer transition hover:shadow-md">
            <CardBody>
              <div className="mb-2 flex items-center gap-2 text-warelyn-primary">
                <Activity size={20} />
                <h3 className="text-sm font-bold">Audit Logs</h3>
              </div>
              <p className="text-xs text-warelyn-muted">View platform-wide activity</p>
            </CardBody>
          </Card>
        </Link>
        <Link className="block" to="/admin/platform-health">
          <Card className="cursor-pointer transition hover:shadow-md">
            <CardBody>
              <div className="mb-2 flex items-center gap-2 text-warelyn-primary">
                <Server size={20} />
                <h3 className="text-sm font-bold">Platform Health</h3>
              </div>
              <p className="text-xs text-warelyn-muted">Database and application status</p>
            </CardBody>
          </Card>
        </Link>
      </div>
    </div>
  );
}
