import { useWarehouses } from '../hooks/useWarehouses.jsx';
import * as reportsService from '../services/reportsService.js';
import { SimpleReportPage } from './ReportsPage.jsx';

const columns = [{ key: 'ledger_id', label: 'Ledger' }, { key: 'created_at', label: 'Created' }, { key: 'movement_type', label: 'Movement' }, { key: 'reference_type', label: 'Reference' }, { key: 'reference_id', label: 'Ref ID' }, { key: 'product_name', label: 'Product' }, { key: 'sku', label: 'SKU' }, { key: 'warehouse_name', label: 'Warehouse' }, { key: 'location_name', label: 'Location' }, { key: 'quantity_delta', label: 'Qty delta' }, { key: 'reserved_delta', label: 'Reserved delta' }, { key: 'available_delta', label: 'Available delta' }];

export function StockMovementReportPage() {
  const warehouses = useWarehouses();
  return (
    <SimpleReportPage
      title="Stock movements"
      description="Immutable stock ledger movement report."
      load={reportsService.getStockMovements}
      columns={columns}
      filters={[
        { key: 'warehouse_id', label: 'Warehouse', options: warehouses },
        { key: 'date_from', label: 'From date', type: 'date' },
        { key: 'date_to', label: 'To date', type: 'date' },
      ]}
    />
  );
}
