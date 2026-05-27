import { useWarehouses } from '../hooks/useWarehouses.jsx';
import * as reportsService from '../services/reportsService.js';
import { SimpleReportPage } from './ReportsPage.jsx';

const columns = [{ key: 'product_name', label: 'Product' }, { key: 'sku', label: 'SKU' }, { key: 'warehouse_name', label: 'Warehouse' }, { key: 'available', label: 'Available' }, { key: 'reserved', label: 'Reserved' }, { key: 'on_hand', label: 'On hand' }, { key: 'reorder_level', label: 'Reorder level' }, { key: 'suggested_reorder_quantity', label: 'Suggested qty' }, { key: 'status', label: 'Status' }];

export function LowStockReportPage() {
  const warehouses = useWarehouses();
  return (
    <SimpleReportPage
      title="Low stock"
      description="Items at or below backend reorder thresholds."
      load={reportsService.getLowStock}
      columns={columns}
      filters={[
        { key: 'warehouse_id', label: 'Warehouse', options: warehouses },
      ]}
    />
  );
}
