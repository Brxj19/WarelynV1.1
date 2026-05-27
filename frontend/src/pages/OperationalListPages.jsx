import { ArrowRight, Eye } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { ActionMenu } from '../components/ui/ActionMenu.jsx';
import { PageHeader } from '../components/ui/PageHeader.jsx';
import { ScreenToolbar } from '../components/ui/ScreenToolbar.jsx';
import { StatusBadge } from '../components/ui/Badge.jsx';
import { Button } from '../components/ui/Button.jsx';
import { ErrorState } from '../components/ui/ErrorState.jsx';
import { SortableHeader } from '../components/ui/SortableHeader.jsx';
import { TableShell } from '../components/ui/TableShell.jsx';
import { emptyStateIllustrations } from '../lib/emptyStates.js';
import { formatDate, formatDecimal } from '../utils/formatters.js';
import { getDateRangeLabel, getNextSort, isDateInRange, sortRows } from '../utils/table.js';
import { useAuth } from '../context/AuthContext.jsx';
import * as catalogService from '../services/catalogService.js';
import * as fulfillmentService from '../services/fulfillmentService.js';
import * as purchasingService from '../services/purchasingService.js';
import * as salesService from '../services/salesService.js';
import * as warehouseService from '../services/warehouseService.js';

const canPurchaseWrite = new Set(['TENANT_ADMIN', 'INVENTORY_MANAGER', 'PURCHASE_STAFF']);

export function PurchaseReceiptsPage() {
  const { accessToken, user } = useAuth();
  const navigate = useNavigate();
  const [receipts, setReceipts] = useState([]);
  const [vendorsById, setVendorsById] = useState({});
  const [warehousesById, setWarehousesById] = useState({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [warehouseFilter, setWarehouseFilter] = useState('ALL');
  const [dateRange, setDateRange] = useState({ from: '', to: '' });
  const [search, setSearch] = useState('');
  const [sortState, setSortState] = useState({ key: 'created_at', direction: 'desc' });
  const mayWrite = canPurchaseWrite.has(user?.role);

  useEffect(() => {
    async function load() {
      setIsLoading(true);
      setError('');
      try {
        const [orders, vendorRows] = await Promise.all([
          purchasingService.listPurchaseOrders(accessToken),
          catalogService.listVendors(accessToken),
        ]);
        const warehouseRows = await warehouseService.listWarehouses(accessToken);
        const receiptGroups = await Promise.all(
          orders.map(async (order) => ({
            order,
            receipts: await purchasingService.listPurchaseReceipts(accessToken, order.id),
          })),
        );
        setVendorsById(Object.fromEntries(vendorRows.map((row) => [row.id, row])));
        setWarehousesById(Object.fromEntries(warehouseRows.map((row) => [row.id, row])));
        setReceipts(
          receiptGroups.flatMap(({ order, receipts: orderReceipts }) =>
            orderReceipts.map((receipt) => ({
              ...receipt,
              po_number: order.po_number,
              vendor_id: order.vendor_id,
              warehouse_ids: Array.from(new Set((receipt.items ?? []).map((item) => item.warehouse_id).filter(Boolean))),
            })),
          ),
        );
      } catch (loadError) {
        setError(loadError.message);
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, [accessToken]);

  const filteredReceipts = useMemo(() => {
    return receipts.filter((receipt) => {
      if (statusFilter !== 'ALL' && receipt.status !== statusFilter) return false;
      if (warehouseFilter !== 'ALL' && !(receipt.warehouse_ids ?? []).some((id) => String(id) === warehouseFilter)) return false;
      if ((dateRange.from || dateRange.to) && !isDateInRange(receipt.created_at, dateRange)) return false;
      if (!search) return true;
      const value = search.toLowerCase();
      return `${receipt.receipt_number} ${receipt.po_number} ${vendorsById[receipt.vendor_id]?.name ?? ''} ${receipt.status}`
        .toLowerCase()
        .includes(value);
    });
  }, [dateRange, receipts, search, statusFilter, vendorsById, warehouseFilter]);
  const sortedReceipts = useMemo(
    () =>
      sortRows(filteredReceipts, sortState, {
        receipt_number: { type: 'text', accessor: (receipt) => receipt.receipt_number },
        po_number: { type: 'text', accessor: (receipt) => receipt.po_number },
        vendor: { type: 'text', accessor: (receipt) => vendorsById[receipt.vendor_id]?.name ?? '' },
        warehouse: {
          type: 'text',
          accessor: (receipt) =>
            (receipt.warehouse_ids ?? [])
              .map((warehouseId) => warehousesById[warehouseId]?.name)
              .filter(Boolean)
              .join(', '),
        },
        status: { type: 'text', accessor: (receipt) => receipt.status },
        lines: { type: 'number', accessor: (receipt) => receipt.items.length },
        created_at: { type: 'date', accessor: (receipt) => receipt.created_at },
      }),
    [filteredReceipts, sortState, vendorsById, warehousesById],
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
      <PageHeader
        actions={
          mayWrite ? (
            <Link to="/purchase-receipts/new">
              <Button>Receive / Create Receipt</Button>
            </Link>
          ) : null
        }
        kicker="Purchases"
        title="Purchase receipts"
        description="Review receipt drafts and committed inbound stock documents without mixing them into purchase order list pages."
      />
      <TableShell
        description={`${sortedReceipts.length} receipt(s) in view`}
        emptyAction={
          !hasActiveFilters && mayWrite ? (
            <Link to="/purchase-receipts/new">
              <Button>Create receipt</Button>
            </Link>
          ) : null
        }
        emptyDescription={hasActiveFilters ? 'Adjust your supplier, status, date, or search filters.' : 'Open a receivable purchase order to create the first receipt.'}
        emptyIllustration={hasActiveFilters ? emptyStateIllustrations.noResult : emptyStateIllustrations.billings}
        emptySecondaryActionLabel={hasActiveFilters ? 'Clear filters' : undefined}
        emptyTitle={hasActiveFilters ? 'No matching purchase orders found' : 'No purchase receipts yet'}
        error={error}
        isEmpty={sortedReceipts.length === 0}
        isLoading={isLoading}
        onEmptySecondaryAction={hasActiveFilters ? () => { setSearch(''); setStatusFilter('ALL'); setWarehouseFilter('ALL'); setDateRange({ from: '', to: '' }); } : undefined}
        rowCount={sortedReceipts.length}
        title="Receipts"
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
            searchPlaceholder="Search receipt number, PO, or vendor"
            searchValue={search}
          >
            <div className="flex flex-wrap gap-2">
              <label className="block min-w-[160px]">
                <span className="mb-2 block text-sm font-medium text-warelyn-text">Status</span>
                <select
                  className="block w-full rounded-lg border border-warelyn-border bg-white px-3 py-2.5 text-sm text-warelyn-text shadow-sm outline-none transition focus:border-warelyn-primary focus:ring-4 focus:ring-blue-900/10"
                  onChange={(event) => setStatusFilter(event.target.value)}
                  value={statusFilter}
                >
                  <option value="ALL">All statuses</option>
                  {Array.from(new Set(receipts.map((receipt) => receipt.status).filter(Boolean))).sort().map((status) => (
                    <option key={status} value={status}>
                      {status}
                    </option>
                  ))}
                </select>
              </label>
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
            </div>
          </ScreenToolbar>
        }
      >
        <table>
          <thead>
            <tr>
              <th><SortableHeader label="Receipt number" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="receipt_number" sortState={sortState} /></th>
              <th><SortableHeader label="Purchase order" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="po_number" sortState={sortState} /></th>
              <th><SortableHeader label="Vendor" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="vendor" sortState={sortState} /></th>
              <th><SortableHeader label="Warehouse" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="warehouse" sortState={sortState} /></th>
              <th><SortableHeader label="Status" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="status" sortState={sortState} /></th>
              <th className="text-right"><SortableHeader align="right" label="Lines" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="lines" sortState={sortState} /></th>
              <th><SortableHeader label="Created" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="created_at" sortState={sortState} /></th>
              <th />
            </tr>
          </thead>
          <tbody>
            {sortedReceipts.map((receipt) => (
              <tr key={receipt.id}>
                <td>
                  <Link className="font-semibold text-warelyn-primary" to={`/purchase-receipts/${receipt.id}`}>
                    {receipt.receipt_number}
                  </Link>
                </td>
                <td><span className="mono-cell">{receipt.po_number}</span></td>
                <td>{vendorsById[receipt.vendor_id]?.name ?? `Vendor #${receipt.vendor_id}`}</td>
                <td>{(receipt.warehouse_ids ?? []).map((warehouseId) => warehousesById[warehouseId]?.name).filter(Boolean).join(', ') || '-'}</td>
                <td><StatusBadge status={receipt.status}>{receipt.status}</StatusBadge></td>
                <td className="number-cell">{receipt.items.length}</td>
                <td>{receipt.created_at ? formatDate(receipt.created_at) : '-'}</td>
                <td className="text-right">
                  <ActionMenu items={[{ label: 'View', icon: Eye, onClick: () => navigate(`/purchase-receipts/${receipt.id}`) }]} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </TableShell>
    </div>
  );
}

export function PurchaseReceiptStartPage() {
  const { accessToken } = useAuth();
  const navigate = useNavigate();
  const [orders, setOrders] = useState([]);
  const [vendorsById, setVendorsById] = useState({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [sortState, setSortState] = useState({ key: 'po_number', direction: 'asc' });

  useEffect(() => {
    async function load() {
      setIsLoading(true);
      setError('');
      try {
        const [orderRows, vendorRows] = await Promise.all([
          purchasingService.listPurchaseOrders(accessToken),
          catalogService.listVendors(accessToken),
        ]);
        setOrders(orderRows.filter((order) => ['SUBMITTED', 'PARTIALLY_RECEIVED'].includes(order.status)));
        setVendorsById(Object.fromEntries(vendorRows.map((row) => [row.id, row])));
      } catch (loadError) {
        setError(loadError.message);
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, [accessToken]);

  const filteredOrders = useMemo(() => {
    if (!search) return orders;
    const value = search.toLowerCase();
    return orders.filter((order) =>
      `${order.po_number} ${vendorsById[order.vendor_id]?.name ?? ''} ${order.status}`.toLowerCase().includes(value),
    );
  }, [orders, search, vendorsById]);
  const sortedOrders = useMemo(
    () =>
      sortRows(filteredOrders, sortState, {
        po_number: { type: 'text', accessor: (order) => order.po_number },
        vendor: { type: 'text', accessor: (order) => vendorsById[order.vendor_id]?.name ?? '' },
        status: { type: 'text', accessor: (order) => order.status },
        lines: { type: 'number', accessor: (order) => order.items.length },
      }),
    [filteredOrders, sortState, vendorsById],
  );
  const activeFilters = search ? [{ key: 'search', label: `Search: ${search}`, onRemove: () => setSearch('') }] : [];

  return (
    <div className="space-y-6">
      <PageHeader
        backTo="/purchase-receipts"
        kicker="Purchases"
        title="Start receipt workflow"
        description="Choose a submitted purchase order to open the focused receiving workflow."
      />
      {error ? <ErrorState description={error} /> : null}
      <TableShell
        description={`${sortedOrders.length} receivable purchase order(s) in view`}
        emptyDescription={activeFilters.length ? 'Reset filters to review all receivable purchase orders.' : 'Purchase orders must be submitted before goods can be received.'}
        emptyTitle={activeFilters.length ? 'No records match your filters' : 'No receivable purchase orders'}
        error={error}
        isEmpty={sortedOrders.length === 0}
        isLoading={isLoading}
        rowCount={sortedOrders.length}
        title="Select purchase order"
        toolbar={
          <ScreenToolbar
            activeFilters={activeFilters}
            onReset={activeFilters.length ? () => setSearch('') : undefined}
            onSearchChange={setSearch}
            searchPlaceholder="Search purchase order or vendor"
            searchValue={search}
          />
        }
      >
        <table>
          <thead>
            <tr>
              <th><SortableHeader label="PO number" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="po_number" sortState={sortState} /></th>
              <th><SortableHeader label="Vendor" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="vendor" sortState={sortState} /></th>
              <th><SortableHeader label="Status" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="status" sortState={sortState} /></th>
              <th className="text-right"><SortableHeader align="right" label="Lines" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="lines" sortState={sortState} /></th>
              <th />
            </tr>
          </thead>
          <tbody>
            {sortedOrders.map((order) => (
              <tr key={order.id}>
                <td><span className="font-semibold text-warelyn-text">{order.po_number}</span></td>
                <td>{vendorsById[order.vendor_id]?.name ?? `Vendor #${order.vendor_id}`}</td>
                <td><StatusBadge status={order.status}>{order.status}</StatusBadge></td>
                <td className="number-cell">{order.items.length}</td>
                <td className="text-right">
                  <Button onClick={() => navigate(`/purchases/${order.id}/receive`)} type="button" variant="secondary">
                    Open receive workflow
                    <ArrowRight size={15} />
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </TableShell>
    </div>
  );
}

export function PackagesPage() {
  const { accessToken } = useAuth();
  const navigate = useNavigate();
  const [packages, setPackages] = useState([]);
  const [salesOrdersById, setSalesOrdersById] = useState({});
  const [customersById, setCustomersById] = useState({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [dateRange, setDateRange] = useState({ from: '', to: '' });
  const [search, setSearch] = useState('');
  const [sortState, setSortState] = useState({ key: 'created_at', direction: 'desc' });

  useEffect(() => {
    async function load() {
      setIsLoading(true);
      setError('');
      try {
        const [orders, customerRows] = await Promise.all([
          salesService.listSalesOrders(accessToken),
          catalogService.listCustomers(accessToken),
        ]);
        const customerMap = Object.fromEntries(customerRows.map((row) => [row.id, row]));
        const packageGroups = await Promise.all(
          orders.map(async (order) => ({
            order,
            packages: await fulfillmentService.listPackagesForOrder(accessToken, order.id),
          })),
        );
        setSalesOrdersById(Object.fromEntries(orders.map((row) => [row.id, row])));
        setCustomersById(customerMap);
        setPackages(
          packageGroups.flatMap(({ order, packages: orderPackages }) =>
            orderPackages.map((pkg) => ({
              ...pkg,
              order_number: order.order_number,
              customer_name: customerMap[order.customer_id]?.name ?? '',
            })),
          ),
        );
      } catch (loadError) {
        setError(loadError.message);
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, [accessToken]);

  const filteredPackages = useMemo(() => {
    return packages.filter((pkg) => {
      if (statusFilter !== 'ALL' && pkg.status !== statusFilter) return false;
      if ((dateRange.from || dateRange.to) && !isDateInRange(pkg.created_at, dateRange)) return false;
      if (!search) return true;
      const value = search.toLowerCase();
      const customerName = customersById[salesOrdersById[pkg.sales_order_id]?.customer_id]?.name ?? '';
      return `${pkg.package_number} ${pkg.order_number} ${customerName} ${pkg.status}`.toLowerCase().includes(value);
    });
  }, [customersById, dateRange, packages, salesOrdersById, search, statusFilter]);
  const sortedPackages = useMemo(
    () =>
      sortRows(filteredPackages, sortState, {
        package_number: { type: 'text', accessor: (pkg) => pkg.package_number },
        order_number: { type: 'text', accessor: (pkg) => pkg.order_number },
        customer: { type: 'text', accessor: (pkg) => customersById[salesOrdersById[pkg.sales_order_id]?.customer_id]?.name ?? '' },
        status: { type: 'text', accessor: (pkg) => pkg.status },
        items: { type: 'number', accessor: (pkg) => pkg.items.length },
        created_at: { type: 'date', accessor: (pkg) => pkg.created_at },
      }),
    [customersById, filteredPackages, salesOrdersById, sortState],
  );
  const packageFilters = [
    search ? { key: 'search', label: `Search: ${search}`, onRemove: () => setSearch('') } : null,
    statusFilter !== 'ALL' ? { key: 'status', label: `Status: ${statusFilter.replaceAll('_', ' ')}`, onRemove: () => setStatusFilter('ALL') } : null,
    dateRange.from || dateRange.to
      ? { key: 'date', label: `Date: ${getDateRangeLabel(dateRange)}`, onRemove: () => setDateRange({ from: '', to: '' }) }
      : null,
  ].filter(Boolean);

  return (
    <div className="space-y-6">
      <PageHeader
        actions={
          <Link to="/sales">
            <Button variant="secondary">Start from sales orders</Button>
          </Link>
        }
        kicker="Operations"
        title="Packages"
        description="Review package records separately from the focused package creation workflow."
      />
      <TableShell
        description={`${sortedPackages.length} package record(s) in view`}
        emptyDescription={packageFilters.length ? 'Try changing your search keyword or clearing filters.' : 'Packing tasks will appear when picked orders are ready for shipment.'}
        emptyIllustration={packageFilters.length ? emptyStateIllustrations.noResult : emptyStateIllustrations.packing}
        emptySecondaryActionLabel={packageFilters.length ? 'Clear filters' : undefined}
        emptyTitle={packageFilters.length ? 'No matching results found' : 'No packing tasks available'}
        error={error}
        isEmpty={sortedPackages.length === 0}
        isLoading={isLoading}
        onEmptySecondaryAction={packageFilters.length ? () => { setSearch(''); setStatusFilter('ALL'); setDateRange({ from: '', to: '' }); } : undefined}
        rowCount={sortedPackages.length}
        title="Package records"
        toolbar={
          <ScreenToolbar
            activeFilters={packageFilters}
            dateRange={dateRange}
            onDateChange={setDateRange}
            onReset={
              packageFilters.length
                ? () => {
                    setSearch('');
                    setStatusFilter('ALL');
                    setDateRange({ from: '', to: '' });
                  }
                : undefined
            }
            onSearchChange={setSearch}
            searchPlaceholder="Search package number, sales order, or customer"
            searchValue={search}
          >
            <label className="block min-w-[160px]">
              <span className="mb-2 block text-sm font-medium text-warelyn-text">Status</span>
              <select
                className="block w-full rounded-lg border border-warelyn-border bg-white px-3 py-2.5 text-sm text-warelyn-text shadow-sm outline-none transition focus:border-warelyn-primary focus:ring-4 focus:ring-blue-900/10"
                onChange={(event) => setStatusFilter(event.target.value)}
                value={statusFilter}
              >
                <option value="ALL">All statuses</option>
                {Array.from(new Set(packages.map((pkg) => pkg.status).filter(Boolean))).sort().map((status) => (
                  <option key={status} value={status}>
                    {status}
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
              <th><SortableHeader label="Package number" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="package_number" sortState={sortState} /></th>
              <th><SortableHeader label="Sales order" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="order_number" sortState={sortState} /></th>
              <th><SortableHeader label="Customer" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="customer" sortState={sortState} /></th>
              <th><SortableHeader label="Status" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="status" sortState={sortState} /></th>
              <th className="text-right"><SortableHeader align="right" label="Items" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="items" sortState={sortState} /></th>
              <th><SortableHeader label="Created" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="created_at" sortState={sortState} /></th>
              <th />
            </tr>
          </thead>
          <tbody>
            {sortedPackages.map((pkg) => {
              const customerName = customersById[salesOrdersById[pkg.sales_order_id]?.customer_id]?.name ?? '-';
              return (
              <tr key={pkg.id}>
                <td>
                  <Link className="font-semibold text-warelyn-primary" to={`/packages/${pkg.id}`}>
                    {pkg.package_number}
                  </Link>
                </td>
                <td><Link className="text-warelyn-primary" to={`/sales/${pkg.sales_order_id}`}>{pkg.order_number}</Link></td>
                <td>{customerName}</td>
                <td><StatusBadge status={pkg.status}>{pkg.status}</StatusBadge></td>
                <td className="number-cell">{pkg.items.length}</td>
                <td>{pkg.created_at ? formatDate(pkg.created_at) : '-'}</td>
                <td className="text-right">
                  <ActionMenu items={[{ label: 'View', icon: Eye, onClick: () => navigate(`/packages/${pkg.id}`) }]} />
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

export function SalesFulfillmentsPage() {
  const { accessToken } = useAuth();
  const navigate = useNavigate();
  const [fulfillments, setFulfillments] = useState([]);
  const [salesOrdersById, setSalesOrdersById] = useState({});
  const [customersById, setCustomersById] = useState({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [dateRange, setDateRange] = useState({ from: '', to: '' });
  const [search, setSearch] = useState('');
  const [sortState, setSortState] = useState({ key: 'created_at', direction: 'desc' });

  useEffect(() => {
    async function load() {
      setIsLoading(true);
      setError('');
      try {
        const [orders, customerRows] = await Promise.all([
          salesService.listSalesOrders(accessToken),
          catalogService.listCustomers(accessToken),
        ]);
        const fulfillmentGroups = await Promise.all(
          orders.map(async (order) => ({
            order,
            fulfillments: await salesService.listSalesFulfillments(accessToken, order.id),
          })),
        );
        setSalesOrdersById(Object.fromEntries(orders.map((row) => [row.id, row])));
        setCustomersById(Object.fromEntries(customerRows.map((row) => [row.id, row])));
        setFulfillments(
          fulfillmentGroups.flatMap(({ order, fulfillments: orderFulfillments }) =>
            orderFulfillments.map((fulfillment) => ({
              ...fulfillment,
              order_number: order.order_number,
            })),
          ),
        );
      } catch (loadError) {
        setError(loadError.message);
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, [accessToken]);

  const filteredFulfillments = useMemo(() => {
    return fulfillments.filter((row) => {
      if (statusFilter !== 'ALL' && row.status !== statusFilter) return false;
      if ((dateRange.from || dateRange.to) && !isDateInRange(row.created_at, dateRange)) return false;
      if (!search) return true;
      const value = search.toLowerCase();
      const customerName = customersById[salesOrdersById[row.sales_order_id]?.customer_id]?.name ?? '';
      return `${row.fulfillment_number} ${row.order_number} ${customerName} ${row.status}`.toLowerCase().includes(value);
    });
  }, [customersById, dateRange, fulfillments, salesOrdersById, search, statusFilter]);
  const sortedFulfillments = useMemo(
    () =>
      sortRows(filteredFulfillments, sortState, {
        fulfillment_number: { type: 'text', accessor: (row) => row.fulfillment_number },
        order_number: { type: 'text', accessor: (row) => row.order_number },
        customer: { type: 'text', accessor: (row) => customersById[salesOrdersById[row.sales_order_id]?.customer_id]?.name ?? '' },
        status: { type: 'text', accessor: (row) => row.status },
        lines: { type: 'number', accessor: (row) => row.items.length },
        created_at: { type: 'date', accessor: (row) => row.created_at },
      }),
    [customersById, filteredFulfillments, salesOrdersById, sortState],
  );
  const fulfillmentFilters = [
    search ? { key: 'search', label: `Search: ${search}`, onRemove: () => setSearch('') } : null,
    statusFilter !== 'ALL' ? { key: 'status', label: `Status: ${statusFilter.replaceAll('_', ' ')}`, onRemove: () => setStatusFilter('ALL') } : null,
    dateRange.from || dateRange.to
      ? { key: 'date', label: `Date: ${getDateRangeLabel(dateRange)}`, onRemove: () => setDateRange({ from: '', to: '' }) }
      : null,
  ].filter(Boolean);

  return (
    <div className="space-y-6">
      <PageHeader
        actions={
          <Link to="/sales">
            <Button variant="secondary">Start from sales orders</Button>
          </Link>
        }
        kicker="Operations"
        title="Fulfillments"
        description="Review fulfillment drafts and committed outbound stock documents separately from sales order list screens."
      />
      <TableShell
        description={`${sortedFulfillments.length} fulfillment record(s) in view`}
        emptyDescription={fulfillmentFilters.length ? 'Try changing your search keyword or clearing filters.' : 'Create fulfillments from sales orders with active reservations.'}
        emptyIllustration={fulfillmentFilters.length ? emptyStateIllustrations.noResult : emptyStateIllustrations.packing}
        emptySecondaryActionLabel={fulfillmentFilters.length ? 'Clear filters' : undefined}
        emptyTitle={fulfillmentFilters.length ? 'No matching results found' : 'No fulfillments yet'}
        error={error}
        isEmpty={sortedFulfillments.length === 0}
        isLoading={isLoading}
        onEmptySecondaryAction={fulfillmentFilters.length ? () => { setSearch(''); setStatusFilter('ALL'); setDateRange({ from: '', to: '' }); } : undefined}
        rowCount={sortedFulfillments.length}
        title="Fulfillment records"
        toolbar={
          <ScreenToolbar
            activeFilters={fulfillmentFilters}
            dateRange={dateRange}
            onDateChange={setDateRange}
            onReset={
              fulfillmentFilters.length
                ? () => {
                    setSearch('');
                    setStatusFilter('ALL');
                    setDateRange({ from: '', to: '' });
                  }
                : undefined
            }
            onSearchChange={setSearch}
            searchPlaceholder="Search fulfillment number, sales order, or customer"
            searchValue={search}
          >
            <label className="block min-w-[160px]">
              <span className="mb-2 block text-sm font-medium text-warelyn-text">Status</span>
              <select
                className="block w-full rounded-lg border border-warelyn-border bg-white px-3 py-2.5 text-sm text-warelyn-text shadow-sm outline-none transition focus:border-warelyn-primary focus:ring-4 focus:ring-blue-900/10"
                onChange={(event) => setStatusFilter(event.target.value)}
                value={statusFilter}
              >
                <option value="ALL">All statuses</option>
                {Array.from(new Set(fulfillments.map((row) => row.status).filter(Boolean))).sort().map((status) => (
                  <option key={status} value={status}>
                    {status}
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
              <th><SortableHeader label="Fulfillment number" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="fulfillment_number" sortState={sortState} /></th>
              <th><SortableHeader label="Sales order" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="order_number" sortState={sortState} /></th>
              <th><SortableHeader label="Customer" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="customer" sortState={sortState} /></th>
              <th><SortableHeader label="Status" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="status" sortState={sortState} /></th>
              <th className="text-right"><SortableHeader align="right" label="Lines" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="lines" sortState={sortState} /></th>
              <th><SortableHeader label="Created" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="created_at" sortState={sortState} /></th>
              <th />
            </tr>
          </thead>
          <tbody>
            {sortedFulfillments.map((fulfillment) => {
              const customerName = customersById[salesOrdersById[fulfillment.sales_order_id]?.customer_id]?.name ?? '-';
              return (
              <tr key={fulfillment.id}>
                <td>
                  <Link className="font-semibold text-warelyn-primary" to={`/sales-fulfillments/${fulfillment.id}`}>
                    {fulfillment.fulfillment_number}
                  </Link>
                </td>
                <td><Link className="text-warelyn-primary" to={`/sales/${fulfillment.sales_order_id}`}>{fulfillment.order_number}</Link></td>
                <td>{customerName}</td>
                <td><StatusBadge status={fulfillment.status}>{fulfillment.status}</StatusBadge></td>
                <td className="number-cell">{fulfillment.items.length}</td>
                <td>{fulfillment.created_at ? formatDate(fulfillment.created_at) : '-'}</td>
                <td className="text-right">
                  <ActionMenu items={[{ label: 'View', icon: Eye, onClick: () => navigate(`/sales-fulfillments/${fulfillment.id}`) }]} />
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
