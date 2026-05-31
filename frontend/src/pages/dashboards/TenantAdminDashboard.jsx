import { AlertTriangle, Boxes, PackageSearch, ShieldAlert } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import { AlertBanner } from '../../components/dashboard/AlertBanner.jsx';
import { ChartFilterBar } from '../../components/dashboard/ChartFilterBar.jsx';
import { DashboardSkeleton } from '../../components/dashboard/DashboardSkeleton.jsx';
import { KpiCard } from '../../components/dashboard/KpiCard.jsx';
import { TaskInboxWidget } from '../../components/dashboard/TaskInboxWidget.jsx';
import { Card, CardBody, CardHeader } from '../../components/ui/Card.jsx';
import { EmptyState } from '../../components/ui/EmptyState.jsx';
import { ErrorState } from '../../components/ui/ErrorState.jsx';
import { PageHeader } from '../../components/ui/PageHeader.jsx';
import { StatusBadge } from '../../components/ui/Badge.jsx';
import { useAuth } from '../../context/AuthContext.jsx';
import { emptyStateIllustrations } from '../../lib/emptyStates.js';
import * as purchasingService from '../../services/purchasingService.js';
import * as reportsService from '../../services/reportsService.js';
import * as salesService from '../../services/salesService.js';
import * as workflowService from '../../services/workflowService.js';
import { formatDateTime, formatNumber } from '../../utils/formatters.js';

const TOOLTIP_STYLE = { borderRadius: '0.5rem', border: '1px solid #e5e7eb', fontSize: '0.8rem' };
const ROLE_COLORS = ['#1e3a5f', '#10b981', '#6366f1', '#f59e0b', '#8b5cf6'];
const SALES_OPEN_STATUSES = new Set(['DRAFT', 'CONFIRMED', 'PARTIALLY_FULFILLED']);
const PURCHASE_OPEN_STATUSES = new Set(['DRAFT', 'SUBMITTED', 'PARTIALLY_RECEIVED']);

function percentageDelta(current, previous) {
  if (!previous) return null;
  return ((current - previous) / Math.abs(previous)) * 100;
}

function previousWeekDelta(rows, openStatuses) {
  const now = Date.now();
  const dayMs = 24 * 60 * 60 * 1000;
  const currentStart = now - 7 * dayMs;
  const previousStart = now - 14 * dayMs;
  const current = rows.filter((row) => {
    const createdAt = new Date(row.created_at).getTime();
    return createdAt >= currentStart && openStatuses.has(row.status);
  }).length;
  const previous = rows.filter((row) => {
    const createdAt = new Date(row.created_at).getTime();
    return createdAt >= previousStart && createdAt < currentStart && openStatuses.has(row.status);
  }).length;
  return percentageDelta(current, previous);
}

function countByStatus(rows, statuses) {
  return statuses.reduce((acc, status) => {
    acc[status] = rows.filter((row) => row.status === status).length;
    return acc;
  }, {});
}

function pendingActionUrl(label) {
  if (label.toLowerCase().includes('low stock')) return '/reports/low-stock';
  if (label.toLowerCase().includes('qc')) return '/returns/qc';
  if (label.toLowerCase().includes('reconciliation')) return '/reports/reconciliation';
  return '/dashboard';
}

export function TenantAdminDashboard() {
  const { accessToken } = useAuth();
  const navigate = useNavigate();
  const [scope, setScope] = useState('CURRENT');
  const [movementDays, setMovementDays] = useState(30);
  const [dashboard, setDashboard] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [salesOrders, setSalesOrders] = useState([]);
  const [purchaseOrders, setPurchaseOrders] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let mounted = true;
    async function load() {
      setIsLoading(true);
      setError('');
      try {
        const [dashboardRow, taskRows, salesRows, purchaseRows] = await Promise.all([
          reportsService.getOperationalDashboard(accessToken),
          workflowService.getMyTasks(accessToken, 'OPEN').catch(() => []),
          salesService.listSalesOrders(accessToken),
          purchasingService.listPurchaseOrders(accessToken),
        ]);
        if (!mounted) return;
        setDashboard(dashboardRow);
        setTasks(taskRows);
        setSalesOrders(salesRows);
        setPurchaseOrders(purchaseRows);
      } catch (loadError) {
        if (!mounted) return;
        setError(loadError.message);
      } finally {
        if (mounted) setIsLoading(false);
      }
    }
    load();
    return () => {
      mounted = false;
    };
  }, [accessToken]);

  const stockMovementRows = useMemo(() => {
    const rows = dashboard?.charts?.stock_movements_by_day || [];
    return rows.slice(-movementDays);
  }, [dashboard, movementDays]);

  const taskByRole = useMemo(() => {
    const grouped = tasks.reduce((acc, task) => {
      acc[task.assigned_role] = (acc[task.assigned_role] || 0) + 1;
      return acc;
    }, {});
    return Object.entries(grouped).map(([role, count]) => ({ role, count }));
  }, [tasks]);

  const statusRows = useMemo(() => {
    const dayMs = 24 * 60 * 60 * 1000;
    const currentCutoff = Date.now() - 30 * dayMs;
    const selectedSales = scope === 'CURRENT' ? salesOrders.filter((row) => new Date(row.created_at).getTime() >= currentCutoff) : salesOrders;
    const selectedPurchases = scope === 'CURRENT' ? purchaseOrders.filter((row) => new Date(row.created_at).getTime() >= currentCutoff) : purchaseOrders;

    const salesCounts = countByStatus(selectedSales, ['DRAFT', 'CONFIRMED', 'PARTIALLY_FULFILLED', 'FULFILLED']);
    const purchaseCounts = countByStatus(selectedPurchases, ['DRAFT', 'SUBMITTED', 'PARTIALLY_RECEIVED']);
    const labels = ['DRAFT', 'CONFIRMED', 'PARTIALLY_FULFILLED', 'FULFILLED', 'SUBMITTED', 'PARTIALLY_RECEIVED'];
    return labels.map((label) => ({
      status: label,
      sales: salesCounts[label] || 0,
      purchase: purchaseCounts[label] || 0,
    }));
  }, [salesOrders, purchaseOrders, scope]);

  const salesDelta = useMemo(() => previousWeekDelta(salesOrders, SALES_OPEN_STATUSES), [salesOrders]);
  const purchaseDelta = useMemo(() => previousWeekDelta(purchaseOrders, PURCHASE_OPEN_STATUSES), [purchaseOrders]);

  const alertItems = useMemo(() => {
    return (dashboard?.insights || []).map((insight) => ({
      severity: insight.severity,
      title: insight.title,
      message: insight.message,
      action_url: insight.action_url || undefined,
    }));
  }, [dashboard]);

  if (isLoading) return <DashboardSkeleton />;
  if (error) return <ErrorState description={error} />;
  if (!dashboard) {
    return <EmptyState description="Unable to load tenant dashboard data." illustration={emptyStateIllustrations.overview} title="Dashboard unavailable" />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        kicker="Tenant Admin"
        title="Operations Overview"
        description="Order flow, warehouse alerts, and cross-role task visibility."
      />

      <div className="sticky top-2 z-20 flex flex-wrap items-center gap-2 rounded-xl border border-warelyn-border bg-white p-3 shadow-sm">
        <Link className="inline-flex items-center gap-2 rounded-md bg-amber-50 px-3 py-1.5 text-xs font-semibold text-amber-700" to="/reports/low-stock">
          <PackageSearch size={14} />
          Low stock: {dashboard.low_stock_items.length}
        </Link>
        <Link className="inline-flex items-center gap-2 rounded-md bg-red-50 px-3 py-1.5 text-xs font-semibold text-red-700" to="/reports/blocked-stock">
          <ShieldAlert size={14} />
          Blocked: {dashboard.blocked_stock_count}
        </Link>
        <Link className="inline-flex items-center gap-2 rounded-md bg-blue-50 px-3 py-1.5 text-xs font-semibold text-blue-700" to="/reports/batch-expiry">
          <Boxes size={14} />
          Expiring: {dashboard.expiring_soon_count}
        </Link>
      </div>

      <AlertBanner alerts={alertItems} sessionKey="tenant-admin-insights" />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard delta={salesDelta} icon={AlertTriangle} label="Open Sales Orders" to="/sales" tone="primary" value={dashboard.open_sales_orders} />
        <KpiCard delta={purchaseDelta} icon={AlertTriangle} label="Pending Purchase Orders" to="/purchases" tone="warning" value={dashboard.pending_purchase_orders} />
        <KpiCard icon={AlertTriangle} label="Active Pick Tasks" to="/pick-tasks" tone="primary" value={dashboard.active_pick_tasks} />
        <KpiCard icon={AlertTriangle} label="Returns Pending QC" to="/returns/qc" tone="danger" value={dashboard.pending_returns_qc} />
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <Card>
          <CardHeader className="space-y-3">
            <h2 className="text-lg font-semibold text-warelyn-text">Order status (sales vs purchase)</h2>
            <ChartFilterBar onChange={setScope} options={[{ value: 'CURRENT', label: 'Current' }, { value: 'ALL', label: 'All time' }]} value={scope} />
          </CardHeader>
          <CardBody>
            <ResponsiveContainer height={260} width="100%">
              <BarChart data={statusRows}>
                <CartesianGrid stroke="#e5e7eb" strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="status" tick={{ fontSize: 10, fill: '#6b7280' }} angle={-20} interval={0} height={56} textAnchor="end" />
                <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: '#6b7280' }} />
                <Tooltip contentStyle={TOOLTIP_STYLE} />
                <Bar dataKey="sales" fill="#f59e0b" name="Sales Orders" radius={[4, 4, 0, 0]} />
                <Bar dataKey="purchase" fill="#6366f1" name="Purchase Orders" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardBody>
        </Card>

        <Card>
          <CardHeader className="space-y-3">
            <h2 className="text-lg font-semibold text-warelyn-text">Stock movements</h2>
            <ChartFilterBar onChange={setMovementDays} options={[{ value: 7, label: '7d' }, { value: 30, label: '30d' }]} value={movementDays} />
          </CardHeader>
          <CardBody>
            <ResponsiveContainer height={260} width="100%">
              <AreaChart data={stockMovementRows}>
                <CartesianGrid stroke="#e5e7eb" strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#6b7280' }} tickFormatter={(value) => String(value).slice(5)} />
                <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: '#6b7280' }} />
                <Tooltip contentStyle={TOOLTIP_STYLE} />
                <Area dataKey="inbound" fill="#10b981" fillOpacity={0.2} stroke="#10b981" strokeWidth={2} type="monotone" />
                <Area dataKey="outbound" fill="#ef4444" fillOpacity={0.2} stroke="#ef4444" strokeWidth={2} type="monotone" />
              </AreaChart>
            </ResponsiveContainer>
          </CardBody>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-warelyn-text">Task team breakdown</h2>
          </CardHeader>
          <CardBody>
            {taskByRole.length ? (
              <div className="space-y-2">
                {taskByRole.map((row, index) => (
                  <Link className="flex items-center justify-between rounded-lg border border-warelyn-border px-3 py-2 text-sm hover:bg-gray-50" key={row.role} to={`/my-tasks?role=${row.role}`}>
                    <span className="inline-flex items-center gap-2">
                      <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: ROLE_COLORS[index % ROLE_COLORS.length] }} />
                      <span className="font-medium text-warelyn-text">{row.role.replace(/_/g, ' ')}</span>
                    </span>
                    <strong className="text-warelyn-primary">{row.count}</strong>
                  </Link>
                ))}
                <Link className="text-xs font-semibold text-warelyn-primary hover:underline" to="/my-tasks">
                  View all roles →
                </Link>
              </div>
            ) : (
              <EmptyState description="No open tasks across team roles." illustration={emptyStateIllustrations.overview} title="No team queue" />
            )}
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-warelyn-text">Pending actions</h2>
          </CardHeader>
          <CardBody>
            <div className="space-y-2">
              {dashboard.pending_actions.map((action) => (
                <Link className="flex items-center justify-between rounded-lg border border-warelyn-border px-3 py-2 text-sm hover:bg-gray-50" key={action.label} to={pendingActionUrl(action.label)}>
                  <span className="font-medium text-warelyn-text">{action.label}</span>
                  <StatusBadge status={action.tone === 'danger' ? 'CANCELLED' : action.tone === 'warning' ? 'PENDING' : 'ACTIVE'}>
                    {formatNumber(action.count)}
                  </StatusBadge>
                </Link>
              ))}
            </div>
          </CardBody>
        </Card>
      </div>

      <Card>
        <CardHeader className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-warelyn-text">Recent stock movements</h2>
          <Link className="text-sm font-semibold text-warelyn-primary hover:underline" to="/reports/stock-movements">
            View all
          </Link>
        </CardHeader>
        <CardBody>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="text-left text-xs uppercase tracking-wide text-warelyn-muted">
                <tr>
                  <th className="pb-2">Product</th>
                  <th className="pb-2">Type</th>
                  <th className="pb-2">Qty</th>
                  <th className="pb-2">When</th>
                </tr>
              </thead>
              <tbody>
                {(dashboard.recent_stock_movements || []).slice(0, 5).map((row) => (
                  <tr className="border-t border-warelyn-border" key={row.ledger_id}>
                    <td className="py-2">{row.product_name}</td>
                    <td className="py-2">
                      <StatusBadge status={row.movement_type}>{row.movement_type}</StatusBadge>
                    </td>
                    <td className="py-2">{formatNumber(row.quantity_delta, { maximumFractionDigits: 2 })}</td>
                    <td className="py-2 text-warelyn-muted">{formatDateTime(row.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardBody>
      </Card>

      <Card>
        <CardHeader className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-warelyn-text">Open team tasks</h2>
          <Link className="text-sm font-semibold text-warelyn-primary hover:underline" to="/my-tasks">
            View all
          </Link>
        </CardHeader>
        <CardBody>
          <TaskInboxWidget maxItems={5} tasks={tasks} />
        </CardBody>
      </Card>
    </div>
  );
}

