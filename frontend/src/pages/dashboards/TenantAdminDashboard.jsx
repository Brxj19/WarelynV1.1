import {
  AlertTriangle, Banknote, Boxes, PackageSearch, Percent, ShieldAlert,
  ShoppingCart, TrendingDown, TrendingUp,
} from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Pie, PieChart,
  Legend, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts';

import { AlertBanner } from '../../components/dashboard/AlertBanner.jsx';
import { ChartFilterBar } from '../../components/dashboard/ChartFilterBar.jsx';
import { DashboardSkeleton } from '../../components/dashboard/DashboardSkeleton.jsx';
import { KpiCard } from '../../components/dashboard/KpiCard.jsx';
import { TaskInboxWidget } from '../../components/dashboard/TaskInboxWidget.jsx';
import { Card, CardBody, CardHeader } from '../../components/ui/Card.jsx';
import { EmptyState } from '../../components/ui/EmptyState.jsx';
import { ErrorState } from '../../components/ui/ErrorState.jsx';
import { PageHeader } from '../../components/ui/PageHeader.jsx';
import { PaginationControls } from '../../components/ui/PaginationControls.jsx';
import { StatusBadge } from '../../components/ui/Badge.jsx';
import { useAuth } from '../../context/AuthContext.jsx';
import { emptyStateIllustrations } from '../../lib/emptyStates.js';
import * as dashboardService from '../../services/dashboardService.js';
import * as purchasingService from '../../services/purchasingService.js';
import * as reportsService from '../../services/reportsService.js';
import * as salesService from '../../services/salesService.js';
import * as workflowService from '../../services/workflowService.js';
import { formatDateTime, formatMoney, formatNumber } from '../../utils/formatters.js';

const TOOLTIP_STYLE = { borderRadius: '0.5rem', border: '1px solid #e5e7eb', fontSize: '0.8rem' };
const COLORS = ['#1e3a5f', '#10b981', '#6366f1', '#f59e0b', '#8b5cf6', '#ef4444', '#ec4899', '#14b8a6'];
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
  const [scope, setScope] = useState('CURRENT');
  const [movementDays, setMovementDays] = useState(30);
  const [revenueDays, setRevenueDays] = useState(30);
  const [dashboard, setDashboard] = useState(null);
  const [adminDash, setAdminDash] = useState(null);
  const [salesDash, setSalesDash] = useState(null);
  const [purchaseDash, setPurchaseDash] = useState(null);
  const [inventoryDash, setInventoryDash] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [salesOrders, setSalesOrders] = useState([]);
  const [purchaseOrders, setPurchaseOrders] = useState([]);
  const [movementQuery, setMovementQuery] = useState('');
  const [movementTypeFilter, setMovementTypeFilter] = useState('ALL');
  const [movementPage, setMovementPage] = useState(1);
  const [movementPageSize, setMovementPageSize] = useState(10);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let mounted = true;
    async function load() {
      setIsLoading(true);
      setError('');
      try {
        const [dashboardRow, adminRow, salesRow, purchaseRow, inventoryRow, taskRows, salesOrderRows, purchaseOrderRows] = await Promise.all([
          reportsService.getOperationalDashboard(accessToken),
          dashboardService.getAdminDashboard(accessToken),
          dashboardService.getSalesDashboard(accessToken),
          dashboardService.getPurchaseDashboard(accessToken),
          dashboardService.getInventoryDashboard(accessToken),
          workflowService.getMyTasks(accessToken, 'OPEN').catch(() => []),
          salesService.listSalesOrders(accessToken),
          purchasingService.listPurchaseOrders(accessToken),
        ]);
        if (!mounted) return;
        setDashboard(dashboardRow);
        setAdminDash(adminRow);
        setSalesDash(salesRow);
        setPurchaseDash(purchaseRow);
        setInventoryDash(inventoryRow);
        setTasks(taskRows);
        setSalesOrders(salesOrderRows);
        setPurchaseOrders(purchaseOrderRows);
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

  const currency = dashboard?.kpis?.currency_code || 'USD';

  const stockMovementRows = useMemo(() => {
    const rows = dashboard?.charts?.stock_movements_by_day || [];
    return rows.slice(-movementDays);
  }, [dashboard, movementDays]);

  const revenueSpendRows = useMemo(() => {
    const rows = adminDash?.activity_by_day || [];
    return rows.slice(-revenueDays);
  }, [adminDash, revenueDays]);

  const taskByRole = useMemo(() => {
    const grouped = tasks.reduce((acc, task) => {
      acc[task.assigned_role] = (acc[task.assigned_role] || 0) + 1;
      return acc;
    }, {});
    return Object.entries(grouped).map(([role, count]) => ({ role, count }));
  }, [tasks]);

  const openTasksByRole = useMemo(() => {
    const data = adminDash?.open_tasks_by_role || {};
    return Object.entries(data).map(([role, count]) => ({ role, count }));
  }, [adminDash]);

  const recentMovementRows = dashboard?.recent_stock_movements || [];
  const movementTypes = useMemo(() => {
    return Array.from(new Set(recentMovementRows.map((row) => row.movement_type).filter(Boolean)));
  }, [recentMovementRows]);
  const filteredMovementRows = useMemo(() => {
    const normalizedQuery = movementQuery.toLowerCase().trim();
    return recentMovementRows.filter((row) => {
      const matchesType = movementTypeFilter === 'ALL' || row.movement_type === movementTypeFilter;
      if (!matchesType) return false;
      if (!normalizedQuery) return true;
      const haystack = [row.product_name, row.movement_type, row.quantity_delta, row.created_at].join(' ').toLowerCase();
      return haystack.includes(normalizedQuery);
    });
  }, [movementQuery, movementTypeFilter, recentMovementRows]);
  const movementPageCount = Math.max(1, Math.ceil(filteredMovementRows.length / movementPageSize));
  const movementStart = (movementPage - 1) * movementPageSize;
  const pagedMovementRows = filteredMovementRows.slice(movementStart, movementStart + movementPageSize);

  useEffect(() => {
    if (movementPage > movementPageCount) {
      setMovementPage(movementPageCount);
    }
  }, [movementPage, movementPageCount]);

  useEffect(() => {
    setMovementPage(1);
  }, [movementQuery, movementTypeFilter]);

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
  const revenueDelta = useMemo(() => {
    if (!salesDash) return null;
    return percentageDelta(Number(salesDash.total_revenue_mtd), Number(salesDash.total_revenue_prev_month));
  }, [salesDash]);
  const spendDelta = useMemo(() => {
    if (!purchaseDash) return null;
    return percentageDelta(Number(purchaseDash.total_spend_mtd), Number(purchaseDash.total_spend_prev_month));
  }, [purchaseDash]);
  const grossMarginPct = useMemo(() => {
    if (!adminDash || !adminDash.revenue_mtd) return null;
    return (Number(adminDash.gross_margin_mtd) / Number(adminDash.revenue_mtd)) * 100;
  }, [adminDash]);

  const stockHealthPct = inventoryDash?.stock_health_score ?? 0;
  const stockHealthTone = stockHealthPct >= 80 ? 'success' : stockHealthPct >= 50 ? 'warning' : 'danger';

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
          Low stock: {dashboard.kpis?.low_stock_count ?? dashboard.low_stock_count ?? dashboard.low_stock_items.length}
        </Link>
        <Link className="inline-flex items-center gap-2 rounded-md bg-red-50 px-3 py-1.5 text-xs font-semibold text-red-700" to="/reports/blocked-stock">
          <ShieldAlert size={14} />
          Blocked: {dashboard.blocked_stock_count}
        </Link>
        <Link className="inline-flex items-center gap-2 rounded-md bg-blue-50 px-3 py-1.5 text-xs font-semibold text-blue-700" to="/reports/batch-expiry">
          <Boxes size={14} />
          Expiring: {dashboard.expiring_soon_count}
        </Link>
        {purchaseDash?.overdue_bills_count > 0 && (
          <Link className="inline-flex items-center gap-2 rounded-md bg-purple-50 px-3 py-1.5 text-xs font-semibold text-purple-700" to="/bills">
            <Banknote size={14} />
            Overdue bills: {purchaseDash.overdue_bills_count}
          </Link>
        )}
        {salesDash?.overdue_invoices_count > 0 && (
          <Link className="inline-flex items-center gap-2 rounded-md bg-rose-50 px-3 py-1.5 text-xs font-semibold text-rose-700" to="/documents?type=invoice&status=SENT">
            <Banknote size={14} />
            Overdue invoices: {salesDash.overdue_invoices_count}
          </Link>
        )}
      </div>

      <AlertBanner alerts={alertItems} sessionKey="tenant-admin-insights" />

      {/* Financial KPIs */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          delta={revenueDelta}
          deltaInvert={false}
          icon={TrendingUp}
          label="Revenue MTD"
          to="/reports"
          tone="success"
          value={adminDash ? formatMoney(adminDash.revenue_mtd, currency) : '-'}
        />
        <KpiCard
          delta={spendDelta}
          deltaInvert
          icon={TrendingDown}
          label="Spend MTD"
          to="/reports"
          tone="danger"
          value={adminDash ? formatMoney(adminDash.spend_mtd, currency) : '-'}
        />
        <KpiCard
          icon={Percent}
          label="Gross Margin"
          to="/reports"
          tone="primary"
          value={adminDash ? formatMoney(adminDash.gross_margin_mtd, currency) : '-'}
          helper={grossMarginPct != null ? `${grossMarginPct.toFixed(1)}% margin` : ''}
        />
        <KpiCard
          icon={ShoppingCart}
          label="Avg Order Value"
          to="/sales"
          tone="primary"
          value={salesDash ? formatMoney(salesDash.avg_order_value, currency) : '-'}
        />
      </div>

      {/* Operational KPIs + Inventory Health */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-6">
        <KpiCard delta={salesDelta} icon={AlertTriangle} label="Open Sales Orders" to="/sales" tone="primary" value={dashboard.open_sales_orders} />
        <KpiCard delta={purchaseDelta} icon={AlertTriangle} label="Pending POs" to="/purchases" tone="warning" value={dashboard.pending_purchase_orders} />
        <KpiCard icon={AlertTriangle} label="Active Pick Tasks" to="/pick-tasks" tone="primary" value={dashboard.active_pick_tasks} />
        <KpiCard icon={AlertTriangle} label="Returns Pending QC" to="/returns/qc" tone="danger" value={dashboard.pending_returns_qc} />
        <KpiCard
          icon={Banknote}
          label="Overdue Invoices"
          to="/documents?type=invoice&status=SENT"
          tone={salesDash?.overdue_invoices_count > 0 ? 'danger' : 'success'}
          value={salesDash?.overdue_invoices_count ?? 0}
          helper={salesDash?.overdue_invoices_count > 0 ? formatMoney(salesDash.overdue_invoices_value, currency) : ''}
        />
        <KpiCard
          icon={Banknote}
          label="Overdue Bills"
          to="/documents?type=bill&status=SENT"
          tone={purchaseDash?.overdue_bills_count > 0 ? 'danger' : 'success'}
          value={purchaseDash?.overdue_bills_count ?? 0}
          helper={purchaseDash?.overdue_bills_count > 0 ? formatMoney(purchaseDash.overdue_bills_value, currency) : ''}
        />
      </div>

      {/* Inventory Health KPIs */}
      {inventoryDash && (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <KpiCard
            icon={Percent}
            label="Stock Health Score"
            to="/reports/inventory-summary"
            tone={stockHealthTone}
            value={`${stockHealthPct}%`}
          />
          <KpiCard
            icon={PackageSearch}
            label="Low Stock SKUs"
            to="/reports/low-stock"
            tone={inventoryDash.low_stock_count > 0 ? 'warning' : 'success'}
            value={inventoryDash.low_stock_count}
          />
          <KpiCard
            icon={ShieldAlert}
            label="Blocked Stock"
            to="/reports/blocked-stock"
            tone={inventoryDash.blocked_stock_count > 0 ? 'danger' : 'success'}
            value={inventoryDash.blocked_stock_count}
          />
          <KpiCard
            icon={Boxes}
            label="Expiring (30d)"
            to="/reports/batch-expiry"
            tone={inventoryDash.expiring_soon_count > 0 ? 'warning' : 'success'}
            value={inventoryDash.expiring_soon_count}
          />
        </div>
      )}

      {/* Chart Row 1: Revenue vs Spend */}
      {revenueSpendRows.length > 0 && (
        <Card className="chart-card dashboard-card-hover">
          <CardHeader className="space-y-3">
            <h2 className="text-lg font-semibold text-warelyn-text">Revenue vs Spend</h2>
            <ChartFilterBar onChange={setRevenueDays} options={[{ value: 7, label: '7d' }, { value: 30, label: '30d' }, { value: 90, label: '90d' }]} value={revenueDays} />
          </CardHeader>
          <CardBody>
            <div className="chart-shell">
            <ResponsiveContainer height={300} width="100%">
              <AreaChart data={revenueSpendRows} margin={{ top: 6, right: 14, left: 10, bottom: 10 }}>
                <CartesianGrid stroke="#e5e7eb" strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#6b7280' }} tickFormatter={(value) => String(value).slice(5)} tickMargin={8} />
                <YAxis tick={{ fontSize: 11, fill: '#6b7280' }} tickFormatter={(value) => formatMoney(value, currency)} width={90} />
                <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(value) => formatMoney(value, currency)} />
                <Legend verticalAlign="top" wrapperStyle={{ fontSize: 12, paddingBottom: 8 }} />
                <Area dataKey="revenue" fill="#10b981" fillOpacity={0.2} stroke="#10b981" strokeWidth={2} type="monotone" name="Revenue" />
                <Area dataKey="spend" fill="#ef4444" fillOpacity={0.15} stroke="#ef4444" strokeWidth={2} type="monotone" name="Spend" />
              </AreaChart>
            </ResponsiveContainer>
            </div>
          </CardBody>
        </Card>
      )}

      {/* Chart Row 2: Order status + Stock movements */}
      <div className="grid gap-6 xl:grid-cols-2">
        <Card className="chart-card dashboard-card-hover">
          <CardHeader className="space-y-3">
            <h2 className="text-lg font-semibold text-warelyn-text">Order status (sales vs purchase)</h2>
            <ChartFilterBar onChange={setScope} options={[{ value: 'CURRENT', label: 'Current' }, { value: 'ALL', label: 'All time' }]} value={scope} />
          </CardHeader>
          <CardBody>
            <div className="chart-shell">
            <ResponsiveContainer height={280} width="100%">
              <BarChart data={statusRows} margin={{ top: 6, right: 14, left: 8, bottom: 12 }}>
                <CartesianGrid stroke="#e5e7eb" strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="status" tick={{ fontSize: 10, fill: '#6b7280' }} interval={0} height={42} tickMargin={8} />
                <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: '#6b7280' }} width={42} />
                <Tooltip contentStyle={TOOLTIP_STYLE} />
                <Legend verticalAlign="top" wrapperStyle={{ fontSize: 12, paddingBottom: 8 }} />
                <Bar dataKey="sales" fill="#f59e0b" name="Sales Orders" radius={[4, 4, 0, 0]} />
                <Bar dataKey="purchase" fill="#6366f1" name="Purchase Orders" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
            </div>
          </CardBody>
        </Card>

        <Card className="chart-card dashboard-card-hover">
          <CardHeader className="space-y-3">
            <h2 className="text-lg font-semibold text-warelyn-text">Stock movements</h2>
            <ChartFilterBar onChange={setMovementDays} options={[{ value: 7, label: '7d' }, { value: 30, label: '30d' }]} value={movementDays} />
          </CardHeader>
          <CardBody>
            <div className="chart-shell">
            <ResponsiveContainer height={280} width="100%">
              <AreaChart data={stockMovementRows} margin={{ top: 6, right: 14, left: 8, bottom: 10 }}>
                <CartesianGrid stroke="#e5e7eb" strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#6b7280' }} tickFormatter={(value) => String(value).slice(5)} tickMargin={8} />
                <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: '#6b7280' }} width={42} />
                <Tooltip contentStyle={TOOLTIP_STYLE} />
                <Legend verticalAlign="top" wrapperStyle={{ fontSize: 12, paddingBottom: 8 }} />
                <Area dataKey="inbound" fill="#10b981" fillOpacity={0.2} stroke="#10b981" strokeWidth={2} type="monotone" />
                <Area dataKey="outbound" fill="#ef4444" fillOpacity={0.2} stroke="#ef4444" strokeWidth={2} type="monotone" />
              </AreaChart>
            </ResponsiveContainer>
            </div>
          </CardBody>
        </Card>
      </div>

      {/* Chart Row 3: Top products, top vendors, tasks by role, stock health */}
      <div className="grid gap-6 xl:grid-cols-2 2xl:grid-cols-4">
        {salesDash?.top_products_by_revenue?.length > 0 && (
          <Card>
            <CardHeader>
              <h2 className="text-lg font-semibold text-warelyn-text">Top Products by Revenue</h2>
            </CardHeader>
            <CardBody>
              <div className="space-y-2">
                {salesDash.top_products_by_revenue.slice(0, 5).map((item, index) => (
                  <div key={item.product_name} className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2 min-w-0 flex-1">
                      <span className="text-xs font-bold text-warelyn-muted w-4 flex-shrink-0">{index + 1}</span>
                      <span className="text-sm text-warelyn-text truncate">{item.product_name}</span>
                    </div>
                    <div className="flex items-center gap-3 flex-shrink-0">
                      <span className="text-xs text-warelyn-muted">{formatNumber(item.units_sold)} sold</span>
                      <span className="text-sm font-semibold text-warelyn-text">{formatMoney(item.revenue, currency)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </CardBody>
          </Card>
        )}

        {purchaseDash?.top_vendors_by_spend?.length > 0 && (
          <Card>
            <CardHeader>
              <h2 className="text-lg font-semibold text-warelyn-text">Top Vendors by Spend</h2>
            </CardHeader>
            <CardBody>
              <div className="space-y-2">
                {purchaseDash.top_vendors_by_spend.slice(0, 5).map((item, index) => (
                  <div key={item.vendor_name} className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2 min-w-0 flex-1">
                      <span className="text-xs font-bold text-warelyn-muted w-4 flex-shrink-0">{index + 1}</span>
                      <span className="text-sm text-warelyn-text truncate">{item.vendor_name}</span>
                    </div>
                    <div className="flex items-center gap-3 flex-shrink-0">
                      <span className="text-xs text-warelyn-muted">{item.order_count} orders</span>
                      <span className="text-sm font-semibold text-warelyn-text">{formatMoney(item.spend, currency)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </CardBody>
          </Card>
        )}

        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-warelyn-text">Open Tasks by Role</h2>
          </CardHeader>
          <CardBody>
            {openTasksByRole.length > 0 ? (
              <div className="flex flex-col items-center gap-4">
                <ResponsiveContainer height={140} width="100%">
                  <PieChart>
                    <Pie
                      cx="50%" cy="50%" data={openTasksByRole} dataKey="count" nameKey="role"
                      innerRadius={32} outerRadius={60} paddingAngle={2}
                    >
                      {openTasksByRole.map((_, i) => (
                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={TOOLTIP_STYLE} />
                  </PieChart>
                </ResponsiveContainer>
                <div className="flex flex-wrap justify-center gap-x-4 gap-y-1">
                  {openTasksByRole.map((row, i) => (
                    <Link key={row.role} className="flex items-center gap-1.5 text-xs hover:underline" to={`/my-tasks?role=${row.role}`}>
                      <span className="h-2 w-2 rounded-full" style={{ backgroundColor: COLORS[i % COLORS.length] }} />
                      <span className="text-warelyn-text">{row.role.replace(/_/g, ' ')}</span>
                      <strong className="text-warelyn-primary">{row.count}</strong>
                    </Link>
                  ))}
                </div>
              </div>
            ) : (
              <EmptyState description="No open tasks across roles." illustration={emptyStateIllustrations.overview} title="No tasks" />
            )}
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-warelyn-text">Stock Health</h2>
          </CardHeader>
          <CardBody>
            {inventoryDash ? (
              <div className="flex flex-col items-center gap-4">
                <ResponsiveContainer height={140} width="100%">
                  <PieChart>
                    <Pie
                      cx="50%" cy="50%" data={[
                        { name: 'Healthy', value: Math.max(0, inventoryDash.total_sku_count - inventoryDash.low_stock_count - inventoryDash.blocked_stock_count) },
                        { name: 'Low Stock', value: inventoryDash.low_stock_count },
                        { name: 'Blocked', value: inventoryDash.blocked_stock_count },
                        { name: 'Expiring', value: inventoryDash.expiring_soon_count },
                      ].filter((d) => d.value > 0)} dataKey="value" nameKey="name"
                      innerRadius={32} outerRadius={60} paddingAngle={2}
                    >
                      <Cell fill="#10b981" />
                      <Cell fill="#f59e0b" />
                      <Cell fill="#ef4444" />
                      <Cell fill="#8b5cf6" />
                    </Pie>
                    <Tooltip contentStyle={TOOLTIP_STYLE} />
                  </PieChart>
                </ResponsiveContainer>
                <div className="flex flex-wrap justify-center gap-x-4 gap-y-1 text-xs text-warelyn-text">
                  <span className="inline-flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-emerald-500" /> Healthy</span>
                  <span className="inline-flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-amber-500" /> Low Stock</span>
                  <span className="inline-flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-red-500" /> Blocked</span>
                  <span className="inline-flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-purple-500" /> Expiring</span>
                </div>
                <Link className="text-xs font-semibold text-warelyn-primary hover:underline" to="/reports/inventory-summary">View inventory summary →</Link>
              </div>
            ) : (
              <EmptyState description="No inventory data." illustration={emptyStateIllustrations.overview} title="No data" />
            )}
          </CardBody>
        </Card>
      </div>

      {/* Team breakdown + Pending actions */}
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
                      <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: COLORS[index % COLORS.length] }} />
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
          <div className="mb-3 flex flex-col gap-2 sm:flex-row">
            <input
              className="w-full rounded-md border border-warelyn-border bg-white px-3 py-2 text-sm text-warelyn-text placeholder:text-warelyn-muted focus:border-warelyn-primary focus:outline-none"
              onChange={(event) => setMovementQuery(event.target.value)}
              placeholder="Filter by product or movement type..."
              value={movementQuery}
            />
            <select
              className="rounded-md border border-warelyn-border bg-white px-3 py-2 text-sm text-warelyn-text focus:border-warelyn-primary focus:outline-none sm:w-56"
              onChange={(event) => setMovementTypeFilter(event.target.value)}
              value={movementTypeFilter}
            >
              <option value="ALL">All movement types</option>
              {movementTypes.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
          </div>
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
                {pagedMovementRows.map((row) => (
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
          <PaginationControls
            page={movementPage}
            pageCount={movementPageCount}
            pageSize={movementPageSize}
            setPage={setMovementPage}
            setPageSize={setMovementPageSize}
            totalRows={filteredMovementRows.length}
          />
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
