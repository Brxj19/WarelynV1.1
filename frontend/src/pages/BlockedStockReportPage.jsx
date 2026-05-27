import { useWarehouses } from '../hooks/useWarehouses.jsx';
import * as reportsService from '../services/reportsService.js';
import { SimpleReportPage } from './ReportsPage.jsx';

const columns = [{ key: 'source_type', label: 'Source' }, { key: 'product_name', label: 'Product' }, { key: 'sku', label: 'SKU' }, { key: 'warehouse_name', label: 'Warehouse' }, { key: 'location_name', label: 'Location' }, { key: 'batch_id', label: 'Batch' }, { key: 'serial_id', label: 'Serial' }, { key: 'quantity', label: 'Quantity' }, { key: 'status', label: 'Status' }, { key: 'reason', label: 'Reason' }, { key: 'created_at', label: 'Created' }];

export function BlockedStockReportPage() {
  const warehouses = useWarehouses();
  return (
    <SimpleReportPage
      title="Blocked stock"
      description="Non-sellable return, batch, and serial stock records from backend reports."
      load={reportsService.getBlockedStock}
      columns={columns}
      filters={[
        { key: 'warehouse_id', label: 'Warehouse', options: warehouses },
      ]}
    />
  );
}
