import { AlertTriangle, ClipboardList, PackageCheck, Truck } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import { DashboardSkeleton } from '../../components/dashboard/DashboardSkeleton.jsx';
import { KpiCard } from '../../components/dashboard/KpiCard.jsx';
import { TaskInboxWidget } from '../../components/dashboard/TaskInboxWidget.jsx';
import { Button } from '../../components/ui/Button.jsx';
import { Card, CardBody, CardHeader } from '../../components/ui/Card.jsx';
import { EmptyState } from '../../components/ui/EmptyState.jsx';
import { ErrorState } from '../../components/ui/ErrorState.jsx';
import { PageHeader } from '../../components/ui/PageHeader.jsx';
import { StatusBadge } from '../../components/ui/Badge.jsx';
import { useAuth } from '../../context/AuthContext.jsx';
import { emptyStateIllustrations } from '../../lib/emptyStates.js';
import * as putawayService from '../../services/putawayService.js';
import * as reportsService from '../../services/reportsService.js';
import * as workflowService from '../../services/workflowService.js';
import { formatDate, formatNumber } from '../../utils/formatters.js';

const TOOLTIP_STYLE = { borderRadius: '0.5rem', border: '1px solid #e5e7eb', fontSize: '0.8rem' };
const INBOUND_MOVEMENTS = new Set(['STOCK_IN', 'RETURN_RESTOCK', 'TRANSFER_IN']);

export function PurchaseStaffDashboard() {
  const { accessToken } = useAuth();
  const navigate = useNavigate();
  const [dashboard, setDashboard] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [pendingPutawayCount, setPendingPutawayCount] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let mounted = true;
    async function load() {
      setIsLoading(true);
      setError('');
      try {
        const [dashboardRow, taskRows, putawayRows] = await Promise.all([
          reportsService.getOperationalDashboard(accessToken),
          workflowService.getMyTasks(accessToken, 'OPEN').catch(() => []),
          putawayService.listPutawayTasks(accessToken, 'PENDING').catch(() => []),
        ]);
        if (!mounted) return;
        setDashboard(dashboardRow);
        setTasks(taskRows.filter((task) => ['PUTAWAY_STOCK', 'RECORD_BILL', 'REORDER_STOCK', 'APPROVE_PO'].includes(task.step_key)));
        setPendingPutawayCount(putawayRows.length);
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

  const purchaseStatusRows = useMemo(() => {
    const counts = dashboard?.charts?.order_status_summary?.purchase_orders || {};
    const statuses = ['DRAFT', 'SUBMITTED', 'PARTIALLY_RECEIVED', 'RECEIVED', 'CANCELLED'];
    return statuses.map((status) => ({ status, count: counts[status] || 0 }));
  }, [dashboard]);

  const inboundRows = useMemo(() => {
    return (dashboard?.recent_stock_movements || []).filter((row) => INBOUND_MOVEMENTS.has(row.movement_type)).slice(0, 5);
  }, [dashboard]);

  if (isLoading) return <DashboardSkeleton />;
  if (error) return <ErrorState description={error} />;
  if (!dashboard) {
    return <EmptyState description="Unable to load purchase dashboard data." illustration={emptyStateIllustrations.overview} title="Dashboard unavailable" />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        kicker="Purchase Staff"
        title="Purchase Operations"
        description="PO pipeline, inbound movement context, and procurement task queue."
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard icon={ClipboardList} label="Pending Purchase Orders" to="/purchases" tone="warning" value={dashboard.pending_purchase_orders} />
        <KpiCard icon={Truck} label="Pending Purchase Receipts" to="/purchases" tone="primary" value={dashboard.pending_purchase_receipts} />
        <KpiCard icon={PackageCheck} label="Open Putaway Tasks" to="/putaway-tasks" tone="primary" value={pendingPutawayCount} />
        <KpiCard icon={AlertTriangle} label="Low Stock Count" to="/reports/low-stock" tone="danger" value={dashboard.kpis?.low_stock_count ?? dashboard.low_stock_items.length} />
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-warelyn-text">Purchase orders by status</h2>
          </CardHeader>
          <CardBody>
            <ResponsiveContainer height={260} width="100%">
              <BarChart
                data={purchaseStatusRows}
                onClick={(state) => {
                  const payload = state?.activePayload?.[0]?.payload;
                  if (payload?.status) navigate(`/purchases?status=${payload.status}`);
                }}
              >
                <CartesianGrid stroke="#e5e7eb" strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="status" tick={{ fontSize: 10, fill: '#6b7280' }} angle={-20} interval={0} height={56} textAnchor="end" />
                <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: '#6b7280' }} />
                <Tooltip contentStyle={TOOLTIP_STYLE} />
                <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
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
            <h2 className="text-lg font-semibold text-warelyn-text">Low stock list</h2>
          </CardHeader>
          <CardBody>
            <div className="space-y-2">
              {(dashboard.low_stock_items || []).slice(0, 5).map((item) => (
                <div className="rounded-lg border border-warelyn-border px-3 py-2" key={`${item.product_id}-${item.warehouse_id}`}>
                  <p className="text-sm font-semibold text-warelyn-text">{item.product_name}</p>
                  <p className="text-xs text-warelyn-muted">
                    Available {formatNumber(item.available, { maximumFractionDigits: 2 })} / Reorder {formatNumber(item.reorder_level)}
                  </p>
                  <div className="mt-2">
                    <Link to="/purchases/new">
                      <Button className="px-2 py-1 text-xs" variant="secondary">Create PO</Button>
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>

        <Card className="xl:col-span-1">
          <CardHeader>
            <h2 className="text-lg font-semibold text-warelyn-text">Recent inbound movements</h2>
          </CardHeader>
          <CardBody>
            <div className="space-y-2">
              {inboundRows.map((row) => (
                <div className="rounded-lg border border-warelyn-border px-3 py-2" key={row.ledger_id}>
                  <p className="text-sm font-semibold text-warelyn-text">{row.product_name}</p>
                  <p className="text-xs text-warelyn-muted">
                    {row.movement_type} • {formatNumber(row.quantity_delta, { maximumFractionDigits: 2 })}
                  </p>
                  <p className="text-xs text-warelyn-muted">{formatDate(row.created_at)}</p>
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
    </div>
  );
}

