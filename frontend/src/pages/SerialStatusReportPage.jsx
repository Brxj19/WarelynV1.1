import { useWarehouses } from '../hooks/useWarehouses.jsx';
import * as reportsService from '../services/reportsService.js';
import { SimpleReportPage } from './ReportsPage.jsx';

const columns = [{ key: 'serial_number', label: 'Serial' }, { key: 'product_name', label: 'Product' }, { key: 'sku', label: 'SKU' }, { key: 'warehouse_name', label: 'Warehouse' }, { key: 'location_name', label: 'Location' }, { key: 'batch_id', label: 'Batch' }, { key: 'status', label: 'Status' }, { key: 'warranty_until', label: 'Warranty' }, { key: 'expires_on', label: 'Expires' }, { key: 'created_at', label: 'Created' }];

export function SerialStatusReportPage() {
  const warehouses = useWarehouses();
  return (
    <SimpleReportPage
      title="Serial status"
      description="Backend serial-level status report."
      load={reportsService.getSerialStatus}
      columns={columns}
      filters={[
        { key: 'warehouse_id', label: 'Warehouse', options: warehouses },
      ]}
    />
  );
}
