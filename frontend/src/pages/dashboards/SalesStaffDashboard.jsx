import { AlertTriangle, ClipboardList, PackageSearch, ShieldAlert } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

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
import * as catalogService from '../../services/catalogService.js';
import * as reportsService from '../../services/reportsService.js';
import * as returnsService from '../../services/returnsService.js';
import * as salesService from '../../services/salesService.js';
import * as workflowService from '../../services/workflowService.js';
import { formatDateTime, formatNumber } from '../../utils/formatters.js';

const TOOLTIP_STYLE = { borderRadius: '0.5rem', border: '1px solid #e5e7eb', fontSize: '0.8rem' };
const OUTBOUND_MOVEMENTS = new Set(['SALES_DEDUCT', 'STOCK_OUT']);

export function SalesStaffDashboard() {
  const { accessToken } = useAuth();
  const navigate = useNavigate();
  const [dashboard, setDashboard] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [pendingReturns, setPendingReturns] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let mounted = true;
    async function load() {
      setIsLoading(true);
      setError('');
      try {
        const [dashboardRow, taskRows, returnRows, salesOrders, customerRows] = await Promise.all([
          reportsService.getOperationalDashboard(accessToken),
          workflowService.getMyTasks(accessToken, 'OPEN').catch(() => []),
          returnsService.listSalesReturns(accessToken),
          salesService.listSalesOrders(accessToken),
          catalogService.listCustomers(accessToken).catch(() => []),
        ]);
        if (!mounted) return;
        setDashboard(dashboardRow);
        setTasks(taskRows.filter((task) => task.step_key === 'CREATE_INVOICE'));

        const salesById = Object.fromEntries(salesOrders.map((row) => [row.id, row]));
        const customersById = Object.fromEntries(customerRows.map((row) => [row.id, row]));
        const filtered = returnRows
          .filter((row) => row.status === 'SUBMITTED' || row.status === 'INSPECTION_PENDING')
          .map((row) => {
            const order = salesById[row.sales_order_id];
            const customer = order?.customer_id ? customersById[order.customer_id] : null;
            return { ...row, customer_name: customer?.name || 'Customer' };
          })
          .slice(0, 5);
        setPendingReturns(filtered);
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

  const salesStatusRows = useMemo(() => {
    const counts = dashboard?.charts?.order_status_summary?.sales_orders || {};
    const statuses = ['DRAFT', 'CONFIRMED', 'PARTIALLY_FULFILLED', 'FULFILLED', 'CANCELLED'];
    return statuses.map((status) => ({ status, count: counts[status] || 0 }));
  }, [dashboard]);

  const recentOutbound = useMemo(() => {
    return (dashboard?.recent_stock_movements || []).filter((row) => OUTBOUND_MOVEMENTS.has(row.movement_type)).slice(0, 5);
  }, [dashboard]);

  if (isLoading) return <DashboardSkeleton />;
  if (error) return <ErrorState description={error} />;
  if (!dashboard) {
    return <EmptyState description="Unable to load sales dashboard data." illustration={emptyStateIllustrations.sales} title="Dashboard unavailable" />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        kicker="Sales Staff"
        title="Sales Workboard"
        description="Order progress, invoice tasks, returns queue, and stock constraints."
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard icon={ClipboardList} label="Open Sales Orders" to="/sales" tone="primary" value={dashboard.open_sales_orders} />
        <KpiCard icon={PackageSearch} label="Active Pick Tasks" to="/pick-tasks" tone="warning" value={dashboard.active_pick_tasks} />
        <KpiCard icon={AlertTriangle} label="Returns Pending QC" to="/returns/qc" tone="danger" value={dashboard.pending_returns_qc} />
        <KpiCard icon={ShieldAlert} label="Blocked Stock" to="/reports/blocked-stock" tone="danger" value={dashboard.blocked_stock_count} />
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <Card className="chart-card dashboard-card-hover">
          <CardHeader>
            <h2 className="text-lg font-semibold text-warelyn-text">Sales orders by status</h2>
          </CardHeader>
          <CardBody>
            <div className="chart-shell">
            <ResponsiveContainer height={280} width="100%">
              <BarChart
                data={salesStatusRows}
                margin={{ top: 6, right: 14, left: 8, bottom: 10 }}
                onClick={(state) => {
                  const payload = state?.activePayload?.[0]?.payload;
                  if (payload?.status) navigate(`/sales?status=${payload.status}`);
                }}
              >
                <CartesianGrid stroke="#e5e7eb" strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="status" tick={{ fontSize: 10, fill: '#6b7280' }} interval={0} height={42} tickMargin={8} />
                <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: '#6b7280' }} width={42} />
                <Tooltip contentStyle={TOOLTIP_STYLE} />
                <Legend verticalAlign="top" wrapperStyle={{ fontSize: 12, paddingBottom: 8 }} />
                <Bar dataKey="count" fill="#f59e0b" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardHeader className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-warelyn-text">My open tasks</h2>
            <Link className="text-sm font-semibold text-warelyn-primary hover:underline" to="/my-tasks">
              View all
            </Link>
          </CardHeader>
          <CardBody>
            <TaskInboxWidget maxItems={5} tasks={tasks} />
          </CardBody>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-1">
          <CardHeader>
            <h2 className="text-lg font-semibold text-warelyn-text">Recent outbound movements</h2>
          </CardHeader>
          <CardBody>
            <div className="space-y-2">
              {recentOutbound.map((row) => (
                <div className="rounded-lg border border-warelyn-border px-3 py-2" key={row.ledger_id}>
                  <p className="text-sm font-semibold text-warelyn-text">{row.product_name}</p>
                  <p className="text-xs text-warelyn-muted">
                    {row.movement_type} • {formatNumber(row.quantity_delta, { maximumFractionDigits: 2 })}
                  </p>
                  <p className="text-xs text-warelyn-muted">{formatDateTime(row.created_at)}</p>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>

        <Card className="xl:col-span-1">
          <CardHeader>
            <h2 className="text-lg font-semibold text-warelyn-text">Low stock alerts</h2>
          </CardHeader>
          <CardBody>
            <div className="space-y-2">
              {(dashboard.low_stock_items || []).slice(0, 5).map((item) => (
                <div className="rounded-lg border border-warelyn-border px-3 py-2" key={`${item.product_id}-${item.warehouse_id}`}>
                  <p className="text-sm font-semibold text-warelyn-text">{item.product_name}</p>
                  <p className="text-xs text-warelyn-muted">
                    Available {formatNumber(item.available, { maximumFractionDigits: 2 })} / Reorder {formatNumber(item.reorder_level)}
                  </p>
                  <div className="mt-1">
                    <StatusBadge status={item.status}>{item.status}</StatusBadge>
                  </div>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>

        <Card className="xl:col-span-1">
          <CardHeader>
            <h2 className="text-lg font-semibold text-warelyn-text">Returns pending</h2>
          </CardHeader>
          <CardBody>
            <div className="space-y-2">
              {pendingReturns.map((row) => (
                <Link className="block rounded-lg border border-warelyn-border px-3 py-2 hover:bg-gray-50" key={row.id} to={`/returns/${row.id}`}>
                  <p className="text-sm font-semibold text-warelyn-text">{row.return_number || `Return #${row.id}`}</p>
                  <p className="text-xs text-warelyn-muted">{row.customer_name}</p>
                  <div className="mt-1">
                    <StatusBadge status={row.status}>{row.status}</StatusBadge>
                  </div>
                </Link>
              ))}
            </div>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}

