import { AlertTriangle, ClipboardList, PackageSearch, ShieldAlert } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Area, AreaChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

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
import * as reportsService from '../../services/reportsService.js';
import * as workflowService from '../../services/workflowService.js';
import { formatDate, formatNumber } from '../../utils/formatters.js';

const TOOLTIP_STYLE = { borderRadius: '0.5rem', border: '1px solid #e5e7eb', fontSize: '0.8rem' };
const DONUT_COLORS = ['#10b981', '#6366f1', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];

export function InventoryManagerDashboard() {
  const { accessToken } = useAuth();
  const navigate = useNavigate();
  const [days, setDays] = useState(30);
  const [dashboard, setDashboard] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let mounted = true;
    async function load() {
      setIsLoading(true);
      setError('');
      try {
        const [dashboardRow, taskRows] = await Promise.all([
          reportsService.getOperationalDashboard(accessToken),
          workflowService.getMyTasks(accessToken, 'OPEN').catch(() => []),
        ]);
        if (!mounted) return;
        setDashboard(dashboardRow);
        setTasks(taskRows.filter((task) => ['PICK_ORDER', 'PUTAWAY_STOCK', 'RETURN_QC'].includes(task.step_key)));
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

  const movementRows = useMemo(() => {
    const rows = dashboard?.charts?.stock_movements_by_day || [];
    return rows.slice(-days);
  }, [dashboard, days]);

  if (isLoading) return <DashboardSkeleton />;
  if (error) return <ErrorState description={error} />;
  if (!dashboard) {
    return <EmptyState description="Unable to load inventory manager dashboard." illustration={emptyStateIllustrations.overview} title="Dashboard unavailable" />;
  }

  const mismatchCount = dashboard.reconciliation_mismatch_count || 0;
  const reconciliationHealth = mismatchCount === 0 ? 'Healthy' : 'Needs review';

  return (
    <div className="space-y-6">
      <PageHeader
        kicker="Inventory Manager"
        title="Warehouse Work Queue"
        description="Pick/putaway workload, stock risk, and reconciliation health."
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard icon={ClipboardList} label="Active Pick Tasks" to="/pick-tasks" tone="primary" value={dashboard.active_pick_tasks} />
        <KpiCard icon={ShieldAlert} label="Returns Pending QC" to="/returns/qc" tone="warning" value={dashboard.pending_returns_qc} />
        <KpiCard icon={PackageSearch} label="Low Stock Count" to="/reports/low-stock" tone="danger" value={dashboard.kpis?.low_stock_count ?? dashboard.low_stock_items.length} />
        <KpiCard icon={AlertTriangle} label="Expiring Soon" to="/reports/batch-expiry" tone="warning" value={dashboard.expiring_soon_count} />
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <Card>
          <CardHeader className="space-y-3">
            <h2 className="text-lg font-semibold text-warelyn-text">Stock movements</h2>
            <ChartFilterBar onChange={setDays} options={[{ value: 7, label: '7d' }, { value: 30, label: '30d' }]} value={days} />
          </CardHeader>
          <CardBody>
            <ResponsiveContainer height={260} width="100%">
              <AreaChart data={movementRows}>
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

        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-warelyn-text">Low stock by category</h2>
          </CardHeader>
          <CardBody>
            {(dashboard.charts?.low_stock_by_category || []).length ? (
              <ResponsiveContainer height={260} width="100%">
                <PieChart>
                  <Pie
                    data={dashboard.charts.low_stock_by_category}
                    dataKey="count"
                    nameKey="category"
                    onClick={() => navigate('/reports/low-stock')}
                    outerRadius={88}
                  >
                    {dashboard.charts.low_stock_by_category.map((item, index) => (
                      <Cell key={item.category} fill={DONUT_COLORS[index % DONUT_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={TOOLTIP_STYLE} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <EmptyState description="No low-stock category data yet." illustration={emptyStateIllustrations.overview} title="No low-stock categories" />
            )}
          </CardBody>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-1">
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

        <Card className="xl:col-span-1">
          <CardHeader>
            <h2 className="text-lg font-semibold text-warelyn-text">Low stock items</h2>
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
            <h2 className="text-lg font-semibold text-warelyn-text">Expiring batches</h2>
          </CardHeader>
          <CardBody>
            <div className="space-y-2">
              {(dashboard.expiring_batches || []).map((batch) => (
                <div className="rounded-lg border border-warelyn-border px-3 py-2" key={batch.batch_id}>
                  <p className="text-sm font-semibold text-warelyn-text">{batch.batch_number}</p>
                  <p className="text-xs text-warelyn-muted">
                    {batch.product_name} • {formatDate(batch.expiry_date)}
                  </p>
                  <div className="mt-1">
                    <StatusBadge status={batch.expiry_status}>{batch.expiry_status}</StatusBadge>
                  </div>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>
      </div>

      <Card>
        <CardHeader className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-warelyn-text">Reconciliation health</h2>
          <Link className="text-sm font-semibold text-warelyn-primary hover:underline" to="/reports/reconciliation">
            Open report
          </Link>
        </CardHeader>
        <CardBody className="flex items-center justify-between">
          <div>
            <p className="text-3xl font-bold text-warelyn-text">{formatNumber(mismatchCount)}</p>
            <p className="text-sm text-warelyn-muted">Mismatch count</p>
          </div>
          <StatusBadge status={mismatchCount === 0 ? 'ACTIVE' : 'PENDING'}>{reconciliationHealth}</StatusBadge>
        </CardBody>
      </Card>
    </div>
  );
}

