import { Activity, Building2, CheckCircle, Layers, Monitor, Shield, TrendingUp, Users, XCircle } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';

import { AuditActivityChart } from '../components/dashboard/AuditActivityChart.jsx';
import { ChartFilterBar } from '../components/dashboard/ChartFilterBar.jsx';
import { DashboardSkeleton } from '../components/dashboard/DashboardSkeleton.jsx';
import { KpiCard } from '../components/dashboard/KpiCard.jsx';
import { PlatformHealthPanel } from '../components/dashboard/PlatformHealthPanel.jsx';
import { TenantGrowthChart } from '../components/dashboard/TenantGrowthChart.jsx';
import { TenantHealthTable } from '../components/dashboard/TenantHealthTable.jsx';
import { Card, CardBody, CardHeader } from '../components/ui/Card.jsx';
import { ErrorState } from '../components/ui/ErrorState.jsx';
import { PageHeader } from '../components/ui/PageHeader.jsx';
import { useAuth } from '../context/AuthContext.jsx';
import * as adminService from '../services/adminService.js';

const growthOptions = [
  { value: '6m', label: '6 mo' },
  { value: '12m', label: '12 mo' },
  { value: 'all', label: 'All' },
];

const auditOptions = [
  { value: 7, label: '7d' },
  { value: 30, label: '30d' },
];

export function AdminDashboardPage() {
  const { accessToken } = useAuth();
  const [dashboard, setDashboard] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [growthRange, setGrowthRange] = useState('12m');
  const [auditDays, setAuditDays] = useState(30);
  const [activeSort, setActiveSort] = useState('event_count');
  const [statusFilter, setStatusFilter] = useState('ALL');

  async function loadDashboard() {
    setError('');
    const data = await adminService.getPlatformDashboard(accessToken);
    setDashboard(data);
  }

  useEffect(() => {
    let mounted = true;
    setIsLoading(true);
    loadDashboard()
      .catch((e) => {
        if (!mounted) return;
        setError(e.message);
      })
      .finally(() => {
        if (mounted) setIsLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, [accessToken]);

  useEffect(() => {
    const timer = setInterval(() => {
      adminService
        .getPlatformHealth(accessToken)
        .then((health) => {
          setDashboard((current) => (current ? { ...current, platform_health: health } : current));
        })
        .catch(() => {});
    }, 60_000);
    return () => clearInterval(timer);
  }, [accessToken]);

  const tenantGrowthFiltered = useMemo(() => {
    if (!dashboard?.tenant_growth_by_month) return [];
    const limit = growthRange === '6m' ? 6 : growthRange === '12m' ? 12 : Number.POSITIVE_INFINITY;
    return dashboard.tenant_growth_by_month.slice(-limit);
  }, [dashboard, growthRange]);

  const auditDataFiltered = useMemo(() => {
    if (!dashboard?.audit_activity_by_day) return [];
    return auditDays === 7 ? dashboard.audit_activity_by_day.slice(-7) : dashboard.audit_activity_by_day;
  }, [dashboard, auditDays]);

  const sortedActiveTenants = useMemo(() => {
    if (!dashboard?.most_active_tenants) return [];
    const filtered =
      statusFilter === 'ALL'
        ? dashboard.most_active_tenants
        : dashboard.most_active_tenants.filter((row) => row.status === statusFilter);
    return [...filtered].sort((a, b) => Number(b?.[activeSort] ?? 0) - Number(a?.[activeSort] ?? 0));
  }, [dashboard, activeSort, statusFilter]);

  const avgAuditEvents = useMemo(() => {
    if (!auditDataFiltered.length) return 0;
    return auditDataFiltered.reduce((sum, row) => sum + Number(row.event_count || 0), 0) / auditDataFiltered.length;
  }, [auditDataFiltered]);

  const mtdDelta = useMemo(() => {
    if (!dashboard) return null;
    const prev = Number(dashboard.new_tenants_prev_month || 0);
    if (prev === 0) return null;
    return ((Number(dashboard.new_tenants_mtd || 0) - prev) / Math.abs(prev)) * 100;
  }, [dashboard]);

  async function handleHealthRefresh() {
    try {
      const health = await adminService.getPlatformHealth(accessToken);
      setDashboard((current) => (current ? { ...current, platform_health: health } : current));
    } catch {}
  }

  async function handleEnable(tenantId) {
    await adminService.enableTenant(accessToken, tenantId);
    await loadDashboard();
  }

  async function handleDisable(tenantId) {
    await adminService.disableTenant(accessToken, tenantId);
    await loadDashboard();
  }

  if (isLoading) return <DashboardSkeleton />;
  if (error) return <ErrorState description={error} />;
  if (!dashboard) return <ErrorState description="Platform dashboard payload is unavailable." />;

  return (
    <div className="space-y-6">
      <PageHeader
        description="Platform-wide health, tenant growth, and activity overview."
        kicker="Super Admin"
        title="Platform Console"
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-6">
        <KpiCard icon={Building2} label="Total Tenants" to="/admin/tenants" tone="primary" value={dashboard.total_tenants} />
        <KpiCard icon={CheckCircle} label="Active Tenants" to="/admin/tenants?status=ACTIVE" tone="success" value={dashboard.active_tenants} />
        <KpiCard icon={XCircle} label="Disabled" to="/admin/tenants?status=DISABLED" tone="danger" value={dashboard.disabled_tenants} />
        <KpiCard
          delta={mtdDelta}
          icon={TrendingUp}
          label="New This Month"
          to="/admin/tenants"
          tone="primary"
          value={dashboard.new_tenants_mtd}
        />
        <KpiCard icon={Users} label="Total Users" to="/admin/tenants" tone="primary" value={dashboard.total_users} />
        <KpiCard
          icon={Activity}
          label="Audit Events (24h)"
          to="/admin/audit-logs"
          tone={dashboard.recent_audit_events > 1000 ? 'warning' : 'primary'}
          value={dashboard.recent_audit_events}
        />
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <Card>
          <CardHeader className="space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-warelyn-text">Tenant growth</h2>
            </div>
            <ChartFilterBar onChange={setGrowthRange} options={growthOptions} value={growthRange} />
          </CardHeader>
          <CardBody>
            <TenantGrowthChart data={tenantGrowthFiltered} range={growthRange} />
          </CardBody>
        </Card>

        <Card>
          <CardHeader className="space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-warelyn-text">Platform audit activity</h2>
            </div>
            <ChartFilterBar onChange={setAuditDays} options={auditOptions} value={auditDays} />
          </CardHeader>
          <CardBody>
            <AuditActivityChart avgLine={avgAuditEvents} data={auditDataFiltered} />
          </CardBody>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <TenantHealthTable
          onDisable={handleDisable}
          onEnable={handleEnable}
          onSortChange={setActiveSort}
          onStatusFilterChange={setStatusFilter}
          rows={sortedActiveTenants}
          sortValue={activeSort}
          statusFilter={statusFilter}
          title="Most active tenants (30 days)"
          type="active"
        />
        <TenantHealthTable
          onDisable={handleDisable}
          onEnable={handleEnable}
          rows={dashboard.recent_tenants}
          title="Recently created tenants"
          type="recent"
        />
      </div>

      <PlatformHealthPanel health={dashboard.platform_health} onRefresh={handleHealthRefresh} />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { label: 'All Tenants', icon: Layers, to: '/admin/tenants', desc: 'View and manage tenant accounts' },
          { label: 'Audit Logs', icon: Shield, to: '/admin/audit-logs', desc: 'Full platform activity log' },
          { label: 'Platform Health', icon: Monitor, to: '/admin/platform-health', desc: 'Database and system status' },
        ].map(({ label, icon: Icon, to, desc }) => (
          <Link key={label} to={to}>
            <Card className="cursor-pointer transition hover:shadow-md">
              <CardBody>
                <div className="mb-2 flex items-center gap-2 text-warelyn-primary">
                  <Icon size={18} />
                  <h3 className="text-sm font-bold">{label}</h3>
                </div>
                <p className="text-xs text-warelyn-muted">{desc}</p>
              </CardBody>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}

