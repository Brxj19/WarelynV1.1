import { Eye, PlayCircle } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { ActionMenu } from '../components/ui/ActionMenu.jsx';
import { ErrorState } from '../components/ui/ErrorState.jsx';
import { PageHeader } from '../components/ui/PageHeader.jsx';
import { ScreenToolbar } from '../components/ui/ScreenToolbar.jsx';
import { StatusBadge } from '../components/ui/Badge.jsx';
import { SortableHeader } from '../components/ui/SortableHeader.jsx';
import { TableShell } from '../components/ui/TableShell.jsx';
import { emptyStateIllustrations } from '../lib/emptyStates.js';
import { formatDate } from '../utils/formatters.js';
import { getDateRangeLabel, getNextSort, isDateInRange, sortRows } from '../utils/table.js';
import { useAuth } from '../context/AuthContext.jsx';
import * as catalogService from '../services/catalogService.js';
import * as fulfillmentService from '../services/fulfillmentService.js';
import * as salesService from '../services/salesService.js';
import * as warehouseService from '../services/warehouseService.js';

const statusTabs = ['ALL', 'PENDING', 'IN_PROGRESS', 'PICKED', 'CANCELLED'];

export function PickTasksPage() {
  const { accessToken } = useAuth();
  const navigate = useNavigate();
  const [pickTasks, setPickTasks] = useState([]);
  const [salesOrdersById, setSalesOrdersById] = useState({});
  const [customersById, setCustomersById] = useState({});
  const [warehousesById, setWarehousesById] = useState({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [warehouseFilter, setWarehouseFilter] = useState('ALL');
  const [dateRange, setDateRange] = useState({ from: '', to: '' });
  const [search, setSearch] = useState('');
  const [sortState, setSortState] = useState({ key: 'created_at', direction: 'desc' });

  useEffect(() => {
    async function load() {
      setIsLoading(true);
      setError('');
      try {
        const [taskRows, orderRows, customerRows, warehouseRows] = await Promise.all([
          fulfillmentService.listPickTasks(accessToken),
          salesService.listSalesOrders(accessToken),
          catalogService.listCustomers(accessToken),
          warehouseService.listWarehouses(accessToken),
        ]);
        setPickTasks(taskRows);
        setSalesOrdersById(Object.fromEntries(orderRows.map((order) => [order.id, order])));
        setCustomersById(Object.fromEntries(customerRows.map((customer) => [customer.id, customer])));
        setWarehousesById(Object.fromEntries(warehouseRows.map((warehouse) => [warehouse.id, warehouse])));
      } catch (loadError) {
        setError(loadError.message);
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, [accessToken]);

  const filteredTasks = useMemo(() => {
    return pickTasks.filter((task) => {
      if (statusFilter !== 'ALL' && task.status !== statusFilter) return false;
      const warehouseId = task.items[0]?.warehouse_id;
      if (warehouseFilter !== 'ALL' && String(warehouseId ?? '') !== warehouseFilter) return false;
      if ((dateRange.from || dateRange.to) && !isDateInRange(task.created_at, dateRange)) return false;
      if (!search) return true;
      const order = salesOrdersById[task.sales_order_id];
      const customerName = customersById[order?.customer_id]?.name ?? '';
      return `${task.pick_number} ${task.sales_order_id} ${customerName} ${task.status}`.toLowerCase().includes(search.toLowerCase());
    });
  }, [customersById, dateRange, pickTasks, salesOrdersById, search, statusFilter, warehouseFilter]);
  const sortedTasks = useMemo(
    () =>
      sortRows(filteredTasks, sortState, {
        pick_number: { type: 'text', accessor: (task) => task.pick_number },
        sales_order: { type: 'text', accessor: (task) => salesOrdersById[task.sales_order_id]?.order_number ?? task.sales_order_id },
        customer: { type: 'text', accessor: (task) => customersById[salesOrdersById[task.sales_order_id]?.customer_id]?.name ?? '' },
        status: { type: 'text', accessor: (task) => task.status },
        warehouse: { type: 'text', accessor: (task) => warehousesById[task.items[0]?.warehouse_id]?.name ?? '' },
        items: { type: 'number', accessor: (task) => task.items.length },
        created_at: { type: 'date', accessor: (task) => task.created_at },
      }),
    [customersById, filteredTasks, salesOrdersById, sortState, warehousesById],
  );
  const activeFilters = [
    search ? { key: 'search', label: `Search: ${search}`, onRemove: () => setSearch('') } : null,
    statusFilter !== 'ALL' ? { key: 'status', label: `Status: ${statusFilter.replaceAll('_', ' ')}`, onRemove: () => setStatusFilter('ALL') } : null,
    warehouseFilter !== 'ALL'
      ? {
          key: 'warehouse',
          label: `Warehouse: ${warehousesById[Number(warehouseFilter)]?.name ?? warehouseFilter}`,
          onRemove: () => setWarehouseFilter('ALL'),
        }
      : null,
    dateRange.from || dateRange.to
      ? { key: 'date', label: `Date: ${getDateRangeLabel(dateRange)}`, onRemove: () => setDateRange({ from: '', to: '' }) }
      : null,
  ].filter(Boolean);
  const hasActiveFilters = activeFilters.length > 0;

  return (
    <div className="space-y-6">
      <PageHeader kicker="Picking" title="Pick tasks" description="Review the pick queue only. Task creation still begins from a specific confirmed sales order." />
      <TableShell
        description={`${sortedTasks.length} task(s) in this view`}
        emptyDescription={hasActiveFilters ? 'Try changing your search keyword or clearing filters.' : 'Picking tasks will appear when orders are ready to be prepared.'}
        emptyIllustration={hasActiveFilters ? emptyStateIllustrations.noResult : emptyStateIllustrations.picking}
        emptySecondaryActionLabel={hasActiveFilters ? 'Clear filters' : undefined}
        emptyTitle={hasActiveFilters ? 'No matching results found' : 'No picking tasks available'}
        error={error}
        isEmpty={sortedTasks.length === 0}
        isLoading={isLoading}
        onEmptySecondaryAction={hasActiveFilters ? () => { setSearch(''); setStatusFilter('ALL'); setWarehouseFilter('ALL'); setDateRange({ from: '', to: '' }); } : undefined}
        rowCount={sortedTasks.length}
        title="Warehouse work queue"
        toolbar={
          <ScreenToolbar
            activeFilters={activeFilters}
            dateRange={dateRange}
            onDateChange={setDateRange}
            onReset={
              hasActiveFilters
                ? () => {
                    setSearch('');
                    setStatusFilter('ALL');
                    setWarehouseFilter('ALL');
                    setDateRange({ from: '', to: '' });
                  }
                : undefined
            }
            onSearchChange={setSearch}
            searchPlaceholder="Search pick task, sales order, or customer"
            searchValue={search}
            tabs={statusTabs.map((status) => ({
              key: status,
              label: status === 'ALL' ? 'All' : status.replaceAll('_', ' '),
              active: statusFilter === status,
              count: status === 'ALL' ? pickTasks.length : pickTasks.filter((row) => row.status === status).length,
              onClick: () => setStatusFilter(status),
            }))}
          >
            <label className="block min-w-[180px]">
              <span className="mb-2 block text-sm font-medium text-warelyn-text">Warehouse</span>
              <select
                className="block w-full rounded-lg border border-warelyn-border bg-white px-3 py-2.5 text-sm text-warelyn-text shadow-sm outline-none transition focus:border-warelyn-primary focus:ring-4 focus:ring-blue-900/10"
                onChange={(event) => setWarehouseFilter(event.target.value)}
                value={warehouseFilter}
              >
                <option value="ALL">All warehouses</option>
                {Object.values(warehousesById)
                  .sort((left, right) => left.name.localeCompare(right.name))
                  .map((warehouse) => (
                    <option key={warehouse.id} value={warehouse.id}>
                      {warehouse.name}
                    </option>
                  ))}
              </select>
            </label>
          </ScreenToolbar>
        }
      >
        <table>
          <thead>
            <tr>
              <th><SortableHeader label="Pick task" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="pick_number" sortState={sortState} /></th>
              <th><SortableHeader label="Sales order" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="sales_order" sortState={sortState} /></th>
              <th><SortableHeader label="Customer" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="customer" sortState={sortState} /></th>
              <th><SortableHeader label="Status" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="status" sortState={sortState} /></th>
              <th><SortableHeader label="Warehouse" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="warehouse" sortState={sortState} /></th>
              <th className="text-right"><SortableHeader align="right" label="Items" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="items" sortState={sortState} /></th>
              <th><SortableHeader label="Created" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="created_at" sortState={sortState} /></th>
              <th />
            </tr>
          </thead>
          <tbody>
            {sortedTasks.map((task) => {
              const order = salesOrdersById[task.sales_order_id];
              const customerName = customersById[order?.customer_id]?.name ?? '-';
              const warehouseName = warehousesById[task.items[0]?.warehouse_id]?.name ?? '-';
              return (
              <tr key={task.id}>
                <td><Link className="font-semibold text-warelyn-primary" to={`/pick-tasks/${task.id}`}>{task.pick_number}</Link></td>
                <td><Link className="text-warelyn-primary" to={`/sales/${task.sales_order_id}`}>{order?.order_number ?? `#${task.sales_order_id}`}</Link></td>
                <td>{customerName}</td>
                <td><StatusBadge status={task.status}>{task.status}</StatusBadge></td>
                <td>{warehouseName}</td>
                <td className="number-cell">{task.items.length}</td>
                <td>{task.created_at ? formatDate(task.created_at) : '-'}</td>
                <td className="text-right">
                  <ActionMenu items={[
                    { label: 'View', icon: Eye, onClick: () => navigate(`/pick-tasks/${task.id}`) },
                    ...(task.status === 'PENDING' ? [{ label: 'Open picking', icon: PlayCircle, onClick: () => navigate(`/pick-tasks/${task.id}`) }] : []),
                  ]} />
                </td>
              </tr>
              );
            })}
          </tbody>
        </table>
      </TableShell>
    </div>
  );
}
