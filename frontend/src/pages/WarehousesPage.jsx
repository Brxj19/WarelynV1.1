import { Plus } from 'lucide-react';
import { Link } from 'react-router-dom';

import { Button } from '../components/ui/Button.jsx';
import { emptyStateIllustrations } from '../lib/emptyStates.js';
import * as warehouseService from '../services/warehouseService.js';
import { MasterDataFormPage, MasterDataListPage } from './MasterDataPage.jsx';

const fields = [
  { name: 'name', label: 'Name' },
  { name: 'code', label: 'Code' },
  { name: 'address', label: 'Address' },
];

export function WarehousesPage() {
  return (
    <MasterDataListPage
      actions={
        <Link to="/warehouses/new">
          <Button>
            <Plus size={16} />
            Warehouse
          </Button>
        </Link>
      }
      description="Manage warehouse records and open a warehouse to configure locations."
      emptyDescription="Create warehouses to organize stock across locations."
      emptyFilteredDescription="Try changing your search or location filter."
      emptyFilteredTitle="No matching warehouses found"
      emptyIllustration={emptyStateIllustrations.warehouse}
      emptyTitle="No warehouses created yet"
      fields={fields}
      kicker="Warehousing"
      listRecords={warehouseService.listWarehouses}
      rowLink={(warehouse) => `/warehouses/${warehouse.id}`}
      searchPlaceholder="Search warehouses by name or code"
      title="Warehouses"
    />
  );
}

export function WarehouseFormPage() {
  return (
    <MasterDataFormPage
      backTo="/warehouses"
      createRecord={warehouseService.createWarehouse}
      description="Create a focused warehouse record before configuring locations or receiving stock."
      fields={[
        { name: 'name', label: 'Name', required: true },
        { name: 'code', label: 'Code', required: true },
        { name: 'address', label: 'Address' },
      ]}
      helperText="Saving creates the warehouse master only. Storage locations and stock balances are configured in downstream screens."
      kicker="Warehousing"
      submitLabel="Create warehouse"
      title="Create warehouse"
    />
  );
}
