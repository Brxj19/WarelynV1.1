import { Activity, AlertTriangle, ArrowRight, Boxes, ClipboardList, Info, PackageCheck, ShieldAlert, ShoppingCart, TrendingDown, TrendingUp, Undo2, Warehouse, XCircle } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { Link, Navigate } from 'react-router-dom';
import { Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import { EmptyState } from '../components/ui/EmptyState.jsx';
import { ErrorState } from '../components/ui/ErrorState.jsx';
import { PageHeader } from '../components/ui/PageHeader.jsx';
import { StatusBadge } from '../components/ui/Badge.jsx';
import { Button } from '../components/ui/Button.jsx';
import { Card, CardBody, CardHeader } from '../components/ui/Card.jsx';
import { LoadingState } from '../components/ui/LoadingState.jsx';
import { TableShell } from '../components/ui/TableShell.jsx';
import { emptyStateIllustrations } from '../lib/emptyStates.js';
import { formatDate, formatMoney } from '../utils/formatters.js';
import { useAuth } from '../context/AuthContext.jsx';
import * as fulfillmentService from '../services/fulfillmentService.js';
import * as purchasingService from '../services/purchasingService.js';
import * as reportsService from '../services/reportsService.js';
import * as returnsService from '../services/returnsService.js';
import * as salesService from '../services/salesService.js';

const kpiCards = [
  ['total_products', 'Total products', 'Catalog scope', 'primary', Boxes, '/catalog/products', null],
  ['total_stock_value_cost', 'Stock value', 'Backend valuation', 'success', TrendingUp, '/reports/product-valuation', ['TENANT_ADMIN', 'INVENTORY_MANAGER', 'VIEWER']],
  ['low_stock_count', 'Low stock', 'Needs attention', 'warning', ShieldAlert, '/reports/low-stock', ['TENANT_ADMIN', 'INVENTORY_MANAGER', 'VIEWER']],
  ['openPurchaseOrders', 'Open purchase orders', 'Ready for receiving', 'primary', ClipboardList, '/purchases', ['TENANT_ADMIN', 'INVENTORY_MANAGER', 'PURCHASE_STAFF']],
  ['openSalesOrders', 'Open sales orders', 'Awaiting workflow steps', 'primary', ShoppingCart, '/sales', ['TENANT_ADMIN', 'INVENTORY_MANAGER', 'SALES_STAFF']],
  ['pickQueue', 'Pick / pack queue', 'Operational queue', 'warning', PackageCheck, '/pick-tasks', ['TENANT_ADMIN', 'INVENTORY_MANAGER', 'SALES_STAFF']],
  ['returnsQc', 'Returns QC', 'Inspection workload', 'warning', Undo2, '/returns', ['TENANT_ADMIN', 'INVENTORY_MANAGER', 'SALES_STAFF']],
  ['reconciliation_mismatch_count', 'Reconciliation health', 'Ledger visibility', 'danger', Activity, '/reports/reconciliation', ['TENANT_ADMIN', 'INVENTORY_MANAGER', 'VIEWER']],
];

function ActionList({ emptyDescription, emptyTitle, illustration, items, renderItem }) {
  if (!items?.length) return <EmptyState illustration={illustration} title={emptyTitle} description={emptyDescription} />;
  return <div className="divide-y divide-warelyn-border overflow-hidden rounded-2xl border border-warelyn-border bg-white">{items.map(renderItem)}</div>;
}

export function DashboardPage() {
  const { accessToken, logout, tenant, user } = useAuth();
  const [dashboard, setDashboard] = useState(null);
  const [purchaseOrders, setPurchaseOrders] = useState([]);
  const [salesOrders, setSalesOrders] = useState([]);
  const [pickTasks, setPickTasks] = useState([]);
  const [salesReturns, setSalesReturns] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    async function load() {
      setIsLoading(true);
      setError('');
      try {
        const [dashboardData, purchaseRows, salesRows, pickRows, returnRows] = await Promise.all([
          reportsService.getOperationalDashboard(accessToken, { compare_previous: true }),
          purchasingService.listPurchaseOrders(accessToken),
          salesService.listSalesOrders(accessToken),
          fulfillmentService.listPickTasks(accessToken),
          returnsService.listSalesReturns(accessToken),
        ]);
        setDashboard(dashboardData);
        setPurchaseOrders(purchaseRows);
        setSalesOrders(salesRows);
        setPickTasks(pickRows);
        setSalesReturns(returnRows);
      } catch (loadError) {
        setError(loadError.message);
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, [accessToken]);

  const derivedKpis = useMemo(() => ({
    openPurchaseOrders: purchaseOrders.filter((row) => ['DRAFT', 'SUBMITTED', 'PARTIALLY_RECEIVED'].includes(row.status)).length,
    openSalesOrders: salesOrders.filter((row) => ['DRAFT', 'CONFIRMED', 'PARTIALLY_FULFILLED'].includes(row.status)).length,
    pickQueue: pickTasks.filter((row) => ['PENDING', 'IN_PROGRESS'].includes(row.status)).length,
    returnsQc: salesReturns.filter((row) => ['SUBMITTED', 'INSPECTION_PENDING', 'PARTIALLY_PROCESSED'].includes(row.status)).length,
  }), [pickTasks, purchaseOrders, salesOrders, salesReturns]);

  if (user?.role === 'SUPER_ADMIN') {
    return <Navigate replace to="/admin" />;
  }

  if (isLoading) return <LoadingState />;

  return (
    <div className="space-y-6">
      <PageHeader
        kicker="Operational dashboard"
        title={`Welcome, ${user?.name ?? 'Warelyn user'}`}
        description={`Backend-driven operational KPIs for ${tenant?.company_name ?? 'your workspace'}. Reports stay read-only and inventory truth remains backend-controlled.`}
        actions={<>{['TENANT_ADMIN', 'INVENTORY_MANAGER', 'VIEWER'].includes(user?.role) && <Link to="/reports"><Button variant="secondary">Open reports</Button></Link>}<Button variant="ghost" onClick={logout}>Logout</Button></>}
      />
      {error ? <ErrorState description={error} /> : null}

      {(dashboard?.kpis?.low_stock_count ?? 0) > 0 && (
        <div className="flex items-center gap-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3">
          <ShieldAlert className="shrink-0 text-amber-600" size={20} />
          <p className="flex-1 text-sm font-medium text-amber-800">
            {dashboard.kpis.low_stock_count} product{dashboard.kpis.low_stock_count > 1 ? 's' : ''} below reorder level
          </p>
          <Link className="text-sm font-semibold text-amber-700 hover:text-amber-900" to="/reports/low-stock">
            View report
          </Link>
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {kpiCards
          .filter(([, , , , , , roles]) => !roles || roles.includes(user?.role))
          .map(([key, label, description, tone, Icon, to]) => {
          const value = derivedKpis[key] ?? dashboard?.kpis?.[key] ?? 0;
          const previousValue = dashboard?.previous_kpis?.[key];
          let TrendIcon = null;
          let trendColor = '';
          if (previousValue !== undefined && previousValue !== null && typeof value === 'number') {
            if (value > previousValue) {
              TrendIcon = TrendingUp;
              trendColor = key === 'low_stock_count' || key === 'reconciliation_mismatch_count' ? 'text-red-500' : 'text-emerald-500';
            } else if (value < previousValue) {
              TrendIcon = TrendingDown;
              trendColor = key === 'low_stock_count' || key === 'reconciliation_mismatch_count' ? 'text-emerald-500' : 'text-red-500';
            }
          }
          return (
            <Link className="metric-link-card" key={key} to={to}>
              <div className="metric-link-card-body">
                <div className="metric-link-card-icon">
                  <Icon size={20} />
                </div>
                <p className="metric-link-card-label">{label}</p>
                <p className="metric-link-card-value">
                  {typeof value === 'number' && key === 'total_stock_value_cost' ? formatMoney(value) : value}
                  {TrendIcon && <TrendIcon className={`ml-1.5 inline ${trendColor}`} size={16} />}
                </p>
                <p className="metric-link-card-copy">{description}</p>
                <span className={`metric-link-card-status ${tone}`}>
                  Open related screen
                  <ArrowRight className="ml-1" size={12} />
                </span>
              </div>
            </Link>
          );
        })}
      </div>

      {/* Insights */}
      {dashboard?.insights?.length > 0 && (
        <div className="space-y-3">
          {dashboard.insights.map((insight, idx) => {
            const Icon = insight.severity === 'danger' ? XCircle : insight.severity === 'warning' ? AlertTriangle : Info;
            const colors = insight.severity === 'danger'
              ? 'border-red-200 bg-red-50 text-red-800'
              : insight.severity === 'warning'
                ? 'border-amber-200 bg-amber-50 text-amber-800'
                : 'border-blue-200 bg-blue-50 text-blue-800';
            const iconColor = insight.severity === 'danger' ? 'text-red-600' : insight.severity === 'warning' ? 'text-amber-600' : 'text-blue-600';
            return (
              <div key={idx} className={`flex items-start gap-3 rounded-xl border px-4 py-3 ${colors}`}>
                <Icon className={`mt-0.5 shrink-0 ${iconColor}`} size={18} />
                <div className="flex-1">
                  <p className="text-sm font-semibold">{insight.title}</p>
                  <p className="text-sm opacity-90">{insight.message}</p>
                </div>
                {insight.action_url && (
                  <Link className="text-sm font-semibold hover:underline" to={insight.action_url}>View</Link>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Charts */}
      {dashboard?.charts && (
        <div className="grid gap-6 xl:grid-cols-2">
          {/* Stock Movements Area Chart */}
          <Card>
            <CardHeader>
              <h2 className="text-lg font-semibold text-warelyn-text">Stock movements (last 30 days)</h2>
            </CardHeader>
            <CardBody>
              {dashboard.charts.stock_movements_by_day?.length > 0 &&
               dashboard.charts.stock_movements_by_day.some((row) => row.inbound > 0 || row.outbound > 0) ? (
                <ResponsiveContainer height={260} width="100%">
                  <AreaChart data={dashboard.charts.stock_movements_by_day} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                    <defs>
                      <linearGradient id="gradientInbound" x1="0" x2="0" y1="0" y2="1">
                        <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                      </linearGradient>
                      <linearGradient id="gradientOutbound" x1="0" x2="0" y1="0" y2="1">
                        <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
                    <XAxis
                      dataKey="date"
                      tick={{ fontSize: 11, fill: '#6b7280' }}
                      tickFormatter={(val) => val.slice(5)}
                      interval="preserveStartEnd"
                    />
                    <YAxis tick={{ fontSize: 11, fill: '#6b7280' }} allowDecimals={false} />
                    <Tooltip
                      contentStyle={{ borderRadius: '0.5rem', border: '1px solid #e5e7eb', fontSize: '0.8rem' }}
                      labelFormatter={(label) => `Date: ${label}`}
                    />
                    <Legend verticalAlign="top" height={36} iconType="circle" />
                    <Area type="monotone" dataKey="inbound" name="Inbound" stroke="#10b981" fill="url(#gradientInbound)" strokeWidth={2} />
                    <Area type="monotone" dataKey="outbound" name="Outbound" stroke="#ef4444" fill="url(#gradientOutbound)" strokeWidth={2} />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <EmptyState illustration={emptyStateIllustrations.overview} title="No movement data" description="Stock movement chart data will appear after inventory activity." />
              )}
            </CardBody>
          </Card>

          {/* Order Status Bar Chart */}
          <Card>
            <CardHeader>
              <h2 className="text-lg font-semibold text-warelyn-text">Order status summary</h2>
            </CardHeader>
            <CardBody>
              {(() => {
                const poData = dashboard.charts.order_status_summary?.purchase_orders || {};
                const soData = dashboard.charts.order_status_summary?.sales_orders || {};
                const hasPO = Object.keys(poData).length > 0;
                const hasSO = Object.keys(soData).length > 0;
                if (!hasPO && !hasSO) {
                  return <EmptyState illustration={emptyStateIllustrations.overview} title="No orders" description="Order status data will appear after orders are created." />;
                }
                const allStatuses = [...new Set([...Object.keys(poData), ...Object.keys(soData)])];
                const barData = allStatuses.map((status) => ({
                  status: status.replace(/_/g, ' '),
                  'Purchase Orders': poData[status] || 0,
                  'Sales Orders': soData[status] || 0,
                }));
                return (
                  <ResponsiveContainer height={260} width="100%">
                    <BarChart data={barData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
                      <XAxis dataKey="status" tick={{ fontSize: 10, fill: '#6b7280' }} interval={0} angle={-20} textAnchor="end" height={60} />
                      <YAxis tick={{ fontSize: 11, fill: '#6b7280' }} allowDecimals={false} />
                      <Tooltip contentStyle={{ borderRadius: '0.5rem', border: '1px solid #e5e7eb', fontSize: '0.8rem' }} />
                      <Legend verticalAlign="top" height={36} iconType="circle" />
                      <Bar dataKey="Purchase Orders" fill="#6366f1" radius={[4, 4, 0, 0]} />
                      <Bar dataKey="Sales Orders" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                );
              })()}
            </CardBody>
          </Card>

          {/* Low Stock by Category Pie Chart */}
          {dashboard.charts.low_stock_by_category?.length > 0 && (
            <Card>
              <CardHeader>
                <h2 className="text-lg font-semibold text-warelyn-text">Low stock by category</h2>
              </CardHeader>
              <CardBody>
                <ResponsiveContainer height={260} width="100%">
                  <PieChart>
                    <Pie
                      data={dashboard.charts.low_stock_by_category}
                      dataKey="count"
                      nameKey="category"
                      cx="50%"
                      cy="50%"
                      outerRadius={90}
                      label={({ category, count }) => `${category} (${count})`}
                      labelLine={true}
                    >
                      {dashboard.charts.low_stock_by_category.map((entry, index) => (
                        <Cell key={entry.category} fill={['#6366f1', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899', '#84cc16'][index % 8]} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{ borderRadius: '0.5rem', border: '1px solid #e5e7eb', fontSize: '0.8rem' }} />
                  </PieChart>
                </ResponsiveContainer>
              </CardBody>
            </Card>
          )}
        </div>
      )}

      <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <Card>
          <CardHeader className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-warelyn-text">Pending actions</h2>
            <Link className="text-sm font-semibold text-warelyn-primary" to="/reports/reorder-suggestions">View all</Link>
          </CardHeader>
          <CardBody>
            <ActionList
              emptyDescription="No operational exceptions are currently reported."
              emptyTitle="No pending actions"
              illustration={emptyStateIllustrations.overview}
              items={dashboard?.pending_actions}
              renderItem={(action) => (
                <div className="flex items-center justify-between gap-3 p-4" key={action.label}>
                  <span className="font-semibold text-warelyn-text">{action.label}</span>
                  <StatusBadge status={action.tone === 'danger' ? 'CANCELLED' : action.tone === 'warning' ? 'PENDING' : 'CONFIRMED'}>
                    {action.count}
                  </StatusBadge>
                </div>
              )}
            />
          </CardBody>
        </Card>

        <Card>
          <CardHeader className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-warelyn-text">Reconciliation health</h2>
            <Link className="text-sm font-semibold text-warelyn-primary" to="/reports/reconciliation">Open report</Link>
          </CardHeader>
          <CardBody>
            <div className="workflow-helper-panel">
              <h3>Projection versus ledger</h3>
              <p>Use the reconciliation report for backend-calculated mismatches across stock projection and ledger history.</p>
              <div className="mt-4 flex items-center justify-between">
                <StatusBadge status={(dashboard?.kpis?.reconciliation_mismatch_count ?? 0) > 0 ? 'CANCELLED' : 'COMMITTED'}>
                  {(dashboard?.kpis?.reconciliation_mismatch_count ?? 0) > 0 ? 'Needs review' : 'Healthy'}
                </StatusBadge>
                <strong className="text-2xl font-bold text-warelyn-text">{dashboard?.kpis?.reconciliation_mismatch_count ?? 0}</strong>
              </div>
            </div>
          </CardBody>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <TableShell
          description="Recent backend-authored movement history."
          emptyDescription="Stock movements will appear after inventory activity."
          emptyIllustration={emptyStateIllustrations.reports}
          emptyTitle="No movements"
          isEmpty={!dashboard?.recent_stock_movements?.length}
          rowCount={dashboard?.recent_stock_movements?.length ?? 0}
          title="Recent stock movements"
        >
          <table>
            <thead>
              <tr>
                <th>Product</th>
                <th>Movement</th>
                <th>Warehouse</th>
                <th className="text-right">Qty delta</th>
              </tr>
            </thead>
            <tbody>
              {(dashboard?.recent_stock_movements ?? []).map((movement) => (
                <tr key={movement.ledger_id}>
                  <td>
                    <div className="font-semibold text-warelyn-text">{movement.product_name}</div>
                    <div className="text-xs text-warelyn-muted">{movement.location_name}</div>
                  </td>
                  <td><StatusBadge status={movement.movement_type}>{movement.movement_type}</StatusBadge></td>
                  <td>{movement.warehouse_name}</td>
                  <td className="number-cell">{movement.quantity_delta}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </TableShell>

        <div className="space-y-6">
          <Card>
            <CardHeader className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-warelyn-text">Low stock list</h2>
              <Link className="text-sm font-semibold text-warelyn-primary" to="/reports/low-stock">Open report</Link>
            </CardHeader>
            <CardBody>
              <ActionList
                emptyDescription="All stocked products are above reorder thresholds."
                emptyTitle="No low stock"
                illustration={emptyStateIllustrations.reports}
                items={dashboard?.low_stock_items}
                renderItem={(item) => (
                  <div className="p-4" key={`${item.product_id}-${item.warehouse_id}`}>
                    <div className="flex items-center justify-between gap-3">
                      <span className="font-semibold text-warelyn-text">{item.product_name}</span>
                      <StatusBadge status={item.status}>{item.status}</StatusBadge>
                    </div>
                    <p className="mt-2 text-sm text-warelyn-muted">Available {item.available}; reorder level {item.reorder_level}</p>
                  </div>
                )}
              />
            </CardBody>
          </Card>

          <Card>
            <CardHeader className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-warelyn-text">Expiring batches</h2>
              <Link className="text-sm font-semibold text-warelyn-primary" to="/reports/batch-expiry">Open report</Link>
            </CardHeader>
            <CardBody>
              <ActionList
                emptyDescription="No batches are currently expired or expiring soon."
                emptyTitle="No expiring batches"
                illustration={emptyStateIllustrations.reports}
                items={dashboard?.expiring_batches}
                renderItem={(batch) => (
                  <div className="p-4" key={batch.batch_id}>
                    <div className="flex items-center justify-between gap-3">
                      <span className="font-semibold text-warelyn-text">{batch.batch_number}</span>
                      <StatusBadge status={batch.expiry_status}>{batch.expiry_status}</StatusBadge>
                    </div>
                    <p className="mt-2 text-sm text-warelyn-muted">{batch.product_name}; expires {batch.expiry_date ? formatDate(batch.expiry_date) : 'not set'}</p>
                  </div>
                )}
              />
            </CardBody>
          </Card>
        </div>
      </div>
    </div>
  );
}
