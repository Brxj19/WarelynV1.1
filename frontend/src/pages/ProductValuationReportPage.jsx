import { Card, CardBody } from '../components/ui/Card.jsx';
import { useWarehouses } from '../hooks/useWarehouses.jsx';
import * as reportsService from '../services/reportsService.js';
import { SimpleReportPage } from './ReportsPage.jsx';

const columns = [{ key: 'product_name', label: 'Product' }, { key: 'sku', label: 'SKU' }, { key: 'warehouse_name', label: 'Warehouse' }, { key: 'on_hand', label: 'On hand' }, { key: 'cost_price', label: 'Cost' }, { key: 'stock_value', label: 'Value' }];

export function ProductValuationReportPage() {
  const warehouses = useWarehouses();
  return (
    <SimpleReportPage
      title="Product valuation"
      description="Current-cost valuation based on backend stock projection."
      load={reportsService.getProductValuation}
      columns={columns}
      loadRows={(data) => data?.rows ?? []}
      filters={[
        { key: 'warehouse_id', label: 'Warehouse', options: warehouses },
      ]}
      summary={(data) => (
        <Card>
          <CardBody className="grid gap-4 md:grid-cols-2">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-warelyn-muted">Total value</p>
              <p className="mt-1 text-2xl font-bold text-warelyn-text">{data?.total_stock_value ?? '0'}</p>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-warelyn-muted">Total units</p>
              <p className="mt-1 text-2xl font-bold text-warelyn-text">{data?.total_units ?? '0'}</p>
            </div>
          </CardBody>
        </Card>
      )}
    />
  );
}
