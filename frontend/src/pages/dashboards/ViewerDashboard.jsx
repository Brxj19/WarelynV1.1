import { Activity, AlertTriangle, Boxes, ShieldAlert } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import { DashboardSkeleton } from '../../components/dashboard/DashboardSkeleton.jsx';
import { KpiCard } from '../../components/dashboard/KpiCard.jsx';
import { Card, CardBody, CardHeader } from '../../components/ui/Card.jsx';
import { EmptyState } from '../../components/ui/EmptyState.jsx';
import { ErrorState } from '../../components/ui/ErrorState.jsx';
import { PageHeader } from '../../components/ui/PageHeader.jsx';
import { StatusBadge } from '../../components/ui/Badge.jsx';
import { useAuth } from '../../context/AuthContext.jsx';
import { useTenantSettings } from '../../context/TenantSettingsContext.jsx';
import { emptyStateIllustrations } from '../../lib/emptyStates.js';
import * as reportsService from '../../services/reportsService.js';
import { formatDateTime, formatMoney, formatNumber } from '../../utils/formatters.js';

const TOOLTIP_STYLE = { borderRadius: '0.5rem', border: '1px solid #e5e7eb', fontSize: '0.8rem' };
const DONUT_COLORS = ['#10b981', '#6366f1', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];

export function ViewerDashboard() {
  const { accessToken } = useAuth();
  const { currency } = useTenantSettings();
  const [dashboard, setDashboard] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let mounted = true;
    async function load() {
      setIsLoading(true);
      setError('');
      try {
        const data = await reportsService.getOperationalDashboard(accessToken);
        if (!mounted) return;
        setDashboard(data);
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

  const orderStatusRows = useMemo(() => {
    const purchase = dashboard?.charts?.order_status_summary?.purchase_orders || {};
    const sales = dashboard?.charts?.order_status_summary?.sales_orders || {};
    const statuses = [...new Set([...Object.keys(purchase), ...Object.keys(sales)])];
    return statuses.map((status) => ({ status, purchase: purchase[status] || 0, sales: sales[status] || 0 }));
  }, [dashboard]);

  if (isLoading) return <DashboardSkeleton />;
  if (error) return <ErrorState description={error} />;
  if (!dashboard) {
    return <EmptyState description="Viewer dashboard data is unavailable." illustration={emptyStateIllustrations.overview} title="Dashboard unavailable" />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        kicker="Viewer"
        title="Read-only Operations Snapshot"
        description="Stock, order, and reconciliation state across the tenant."
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard icon={Boxes} label="Total Products" to="/reports/inventory-summary" tone="primary" value={dashboard.kpis.total_products} />
        <KpiCard icon={Activity} label="Total Stock Value" to="/reports/product-valuation" tone="success" value={formatMoney(dashboard.kpis.total_stock_value_cost, currency)} />
        <KpiCard icon={AlertTriangle} label="Low Stock Count" to="/reports/low-stock" tone="warning" value={dashboard.kpis.low_stock_count} />
        <KpiCard icon={ShieldAlert} label="Reconciliation Mismatches" to="/reports/reconciliation" tone="danger" value={dashboard.kpis.reconciliation_mismatch_count} />
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-warelyn-text">Stock movements (30d)</h2>
          </CardHeader>
          <CardBody>
            <ResponsiveContainer height={260} width="100%">
              <AreaChart data={dashboard.charts?.stock_movements_by_day || []}>
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
            <h2 className="text-lg font-semibold text-warelyn-text">Order status summary</h2>
          </CardHeader>
          <CardBody>
            <ResponsiveContainer height={260} width="100%">
              <BarChart data={orderStatusRows}>
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
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-warelyn-text">Low stock by category</h2>
          </CardHeader>
          <CardBody>
            {(dashboard.charts?.low_stock_by_category || []).length ? (
              <ResponsiveContainer height={260} width="100%">
                <PieChart>
                  <Pie data={dashboard.charts.low_stock_by_category} dataKey="count" nameKey="category" outerRadius={88}>
                    {dashboard.charts.low_stock_by_category.map((item, index) => (
                      <Cell key={item.category} fill={DONUT_COLORS[index % DONUT_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={TOOLTIP_STYLE} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <EmptyState description="No low-stock category data available." illustration={emptyStateIllustrations.overview} title="No category split" />
            )}
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-warelyn-text">Recent stock movements</h2>
          </CardHeader>
          <CardBody>
            <div className="space-y-2">
              {(dashboard.recent_stock_movements || []).slice(0, 5).map((row) => (
                <div className="rounded-lg border border-warelyn-border px-3 py-2" key={row.ledger_id}>
                  <p className="text-sm font-semibold text-warelyn-text">{row.product_name}</p>
                  <p className="text-xs text-warelyn-muted">
                    {row.movement_type} • {formatNumber(row.quantity_delta, { maximumFractionDigits: 2 })}
                  </p>
                  <p className="text-xs text-warelyn-muted">{formatDateTime(row.created_at)}</p>
                  <div className="mt-1">
                    <StatusBadge status={row.movement_type}>{row.movement_type}</StatusBadge>
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

