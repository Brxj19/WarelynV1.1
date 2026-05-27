import { useWarehouses } from '../hooks/useWarehouses.jsx';
import * as reportsService from '../services/reportsService.js';
import { SimpleReportPage } from './ReportsPage.jsx';

const columns = [{ key: 'warehouse_name', label: 'Warehouse' }, { key: 'location_code', label: 'Location' }, { key: 'location_type', label: 'Type' }, { key: 'product_name', label: 'Product' }, { key: 'sku', label: 'SKU' }, { key: 'on_hand', label: 'On hand' }, { key: 'reserved', label: 'Reserved' }, { key: 'available', label: 'Available' }, { key: 'stock_value', label: 'Value' }];

export function LocationStockReportPage() {
  const warehouses = useWarehouses();
  return (
    <SimpleReportPage
      title="Location stock"
      description="Backend location-level stock projection by SKU."
      load={reportsService.getLocationStock}
      columns={columns}
      filters={[
        { key: 'warehouse_id', label: 'Warehouse', options: warehouses },
      ]}
    />
  );
}
