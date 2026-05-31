import { SimpleReportPage } from './ReportsPage.jsx';
import { useTenantSettings } from '../context/TenantSettingsContext.jsx';
import { Card, CardBody } from '../components/ui/Card.jsx';
import * as reportsService from '../services/reportsService.js';
import { formatMoney, formatNumber } from '../utils/formatters.js';

const SUMMARY_COLUMNS = [
  { key: 'metric', label: 'Metric' },
  {
    key: 'value',
    label: 'Value',
    numeric: true,
    render: (_value, row) => row.display,
  },
];

function summaryRows(data, currencyCode) {
  if (!data) return [];
  return [
    { id: 'total_products', metric: 'Total products', display: formatNumber(data.total_products, { maximumFractionDigits: 0 }) },
    { id: 'active_products', metric: 'Active products', display: formatNumber(data.active_products, { maximumFractionDigits: 0 }) },
    { id: 'total_skus_with_stock', metric: 'SKUs with stock', display: formatNumber(data.total_skus_with_stock, { maximumFractionDigits: 0 }) },
    { id: 'total_on_hand_quantity', metric: 'On hand units', display: formatNumber(data.total_on_hand_quantity, { maximumFractionDigits: 0 }) },
    { id: 'total_available_quantity', metric: 'Available units', display: formatNumber(data.total_available_quantity, { maximumFractionDigits: 0 }) },
    { id: 'total_reserved_quantity', metric: 'Reserved units', display: formatNumber(data.total_reserved_quantity, { maximumFractionDigits: 0 }) },
    { id: 'total_stock_value_cost', metric: 'Stock value (cost)', display: formatMoney(data.total_stock_value_cost, currencyCode) },
    { id: 'low_stock_count', metric: 'Low stock items', display: formatNumber(data.low_stock_count, { maximumFractionDigits: 0 }) },
    { id: 'out_of_stock_count', metric: 'Out of stock items', display: formatNumber(data.out_of_stock_count, { maximumFractionDigits: 0 }) },
    { id: 'expiring_soon_batch_count', metric: 'Expiring soon batches', display: formatNumber(data.expiring_soon_batch_count, { maximumFractionDigits: 0 }) },
    { id: 'expired_batch_count', metric: 'Expired batches', display: formatNumber(data.expired_batch_count, { maximumFractionDigits: 0 }) },
    { id: 'damaged_blocked_qc_count', metric: 'Blocked/QC stock records', display: formatNumber(data.damaged_blocked_qc_count, { maximumFractionDigits: 0 }) },
    { id: 'reconciliation_mismatch_count', metric: 'Reconciliation mismatches', display: formatNumber(data.reconciliation_mismatch_count, { maximumFractionDigits: 0 }) },
  ];
}

export function InventorySummaryReportPage() {
  const { currency } = useTenantSettings();

  return (
    <SimpleReportPage
      title="Inventory summary"
      description="Backend-calculated inventory KPIs and exception counts."
      load={reportsService.getInventorySummary}
      columns={SUMMARY_COLUMNS}
      loadRows={(data) => summaryRows(data, data?.currency_code || currency || 'USD')}
      summary={(data) =>
        data ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[
              { key: 'total_products', label: 'Total products', value: formatNumber(data.total_products, { maximumFractionDigits: 0 }) },
              { key: 'total_on_hand_quantity', label: 'On hand units', value: formatNumber(data.total_on_hand_quantity, { maximumFractionDigits: 0 }) },
              { key: 'total_stock_value_cost', label: 'Stock value (cost)', value: formatMoney(data.total_stock_value_cost, data.currency_code || currency || 'USD') },
              { key: 'low_stock_count', label: 'Low stock items', value: formatNumber(data.low_stock_count, { maximumFractionDigits: 0 }) },
            ].map((item) => (
              <Card key={item.key}>
                <CardBody>
                  <p className="text-xs font-semibold uppercase tracking-wide text-warelyn-muted">
                    {item.label}
                  </p>
                  <p className="mt-1 text-2xl font-bold text-warelyn-text">
                    {item.value}
                  </p>
                </CardBody>
              </Card>
            ))}
          </div>
        ) : null
      }
    />
  );
}
