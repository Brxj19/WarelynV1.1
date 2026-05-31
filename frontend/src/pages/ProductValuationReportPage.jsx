import { useTenantSettings } from '../context/TenantSettingsContext.jsx';
import { useWarehouses } from '../hooks/useWarehouses.jsx';
import { formatMoney, formatNumber } from '../utils/formatters.js';
import { Card, CardBody } from '../components/ui/Card.jsx';
import * as reportsService from '../services/reportsService.js';
import { SimpleReportPage } from './ReportsPage.jsx';

const columns = [
  { key: 'product_name', label: 'Product' },
  { key: 'sku', label: 'SKU' },
  { key: 'warehouse_name', label: 'Warehouse' },
  { key: 'units', label: 'Units', numeric: true },
  { key: 'cost_price', label: 'Cost', numeric: true },
  { key: 'stock_value', label: 'Value', numeric: true },
];

export function ProductValuationReportPage() {
  const warehouses = useWarehouses();
  const { currency } = useTenantSettings();
  return (
    <SimpleReportPage
      title="Product valuation"
      description="Current-cost valuation based on backend stock projection."
      load={reportsService.getProductValuation}
      columns={columns}
      loadRows={(data) => data?.rows ?? []}
      normalize={(row) => ({
        ...row,
        units: Number(row.on_hand ?? 0),
      })}
      filters={[
        { key: 'warehouse_id', label: 'Warehouse', options: warehouses },
      ]}
      summary={(data) => (
        <Card>
          <CardBody className="grid gap-4 md:grid-cols-2">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-warelyn-muted">Total value</p>
              <p className="mt-1 text-2xl font-bold text-warelyn-text">{formatMoney(data?.total_stock_value ?? 0, data?.currency_code || currency || 'USD')}</p>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-warelyn-muted">Total units</p>
              <p className="mt-1 text-2xl font-bold text-warelyn-text">{formatNumber(data?.total_units ?? 0, { maximumFractionDigits: 0 })}</p>
            </div>
          </CardBody>
        </Card>
      )}
    />
  );
}
