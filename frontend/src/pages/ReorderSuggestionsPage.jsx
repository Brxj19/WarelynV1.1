import { useWarehouses } from '../hooks/useWarehouses.jsx';
import * as reportsService from '../services/reportsService.js';
import { SimpleReportPage } from './ReportsPage.jsx';

const columns = [{ key: 'product_name', label: 'Product' }, { key: 'sku', label: 'SKU' }, { key: 'warehouse_name', label: 'Warehouse' }, { key: 'available', label: 'Available' }, { key: 'reorder_level', label: 'Reorder level' }, { key: 'suggested_quantity', label: 'Suggested qty' }, { key: 'reason', label: 'Reason' }];

export function ReorderSuggestionsPage() {
  const warehouses = useWarehouses();
  return (
    <SimpleReportPage
      title="Reorder suggestions"
      description="Advisory suggestions only. Purchase orders are not created automatically."
      load={reportsService.getReorderSuggestions}
      columns={columns}
      filters={[
        { key: 'warehouse_id', label: 'Warehouse', options: warehouses },
      ]}
    />
  );
}
