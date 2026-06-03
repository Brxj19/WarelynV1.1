import { Eye, Plus, ReceiptText } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { ActionMenu } from '../components/ui/ActionMenu.jsx';
import { PageHeader } from '../components/ui/PageHeader.jsx';
import { ScreenToolbar } from '../components/ui/ScreenToolbar.jsx';
import { StatusBadge } from '../components/ui/Badge.jsx';
import { Button } from '../components/ui/Button.jsx';
import { SortableHeader } from '../components/ui/SortableHeader.jsx';
import { TableShell } from '../components/ui/TableShell.jsx';
import { emptyStateIllustrations } from '../lib/emptyStates.js';
import { formatDate } from '../utils/formatters.js';
import { getDateRangeLabel, getNextSort, isDateInRange, sortRows } from '../utils/table.js';
import { useAuth } from '../context/AuthContext.jsx';
import * as documentService from '../services/documentService.js';
import * as catalogService from '../services/catalogService.js';
import * as purchasingService from '../services/purchasingService.js';

const canWrite = new Set(['TENANT_ADMIN', 'INVENTORY_MANAGER', 'PURCHASE_STAFF']);
const statusTabs = ['ALL', 'DRAFT', 'SUBMITTED', 'PARTIALLY_RECEIVED', 'RECEIVED', 'CANCELLED', 'CLOSED'];

export function PurchasesPage() {
  const { accessToken, user } = useAuth();
  const navigate = useNavigate();
  const [orders, setOrders] = useState([]);
  const [vendorsById, setVendorsById] = useState({});
  const [bills, setBills] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [vendorFilter, setVendorFilter] = useState('ALL');
  const [dateRange, setDateRange] = useState({ from: '', to: '' });
  const [search, setSearch] = useState('');
  const [sortState, setSortState] = useState({ key: 'order_date', direction: 'desc' });
  const mayWrite = canWrite.has(user?.role);

  useEffect(() => {
    async function load() {
      setIsLoading(true);
      setError('');
      try {
        const [orderRows, vendorRows, billRows] = await Promise.all([
          purchasingService.listPurchaseOrders(accessToken),
          catalogService.listVendors(accessToken),
          documentService.listBills(accessToken),
        ]);
        setOrders(orderRows);
        setVendorsById(Object.fromEntries(vendorRows.map((row) => [row.id, row])));
        setBills(billRows);
      } catch (loadError) {
        setError(loadError.message);
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, [accessToken]);

  const billByPurchaseOrderId = useMemo(
    () =>
      Object.fromEntries(
        bills
          .filter((bill) => bill.purchase_order_id && bill.status !== 'VOID')
          .map((bill) => [bill.purchase_order_id, bill]),
      ),
    [bills],
  );

  const filteredOrders = useMemo(() => {
    return orders.filter((order) => {
      if (statusFilter !== 'ALL' && order.status !== statusFilter) return false;
      if (vendorFilter !== 'ALL' && String(order.vendor_id) !== vendorFilter) return false;
      if ((dateRange.from || dateRange.to) && !isDateInRange(order.order_date, dateRange)) return false;
      if (!search) return true;
      const value = search.toLowerCase();
      const vendorName = vendorsById[order.vendor_id]?.name ?? '';
      return `${order.po_number} ${vendorName} ${order.status}`.toLowerCase().includes(value);
    });
  }, [dateRange, orders, search, statusFilter, vendorFilter, vendorsById]);
  const sortedOrders = useMemo(
    () =>
      sortRows(filteredOrders, sortState, {
        po_number: { type: 'text', accessor: (order) => order.po_number },
        vendor: { type: 'text', accessor: (order) => vendorsById[order.vendor_id]?.name ?? '' },
        status: { type: 'text', accessor: (order) => order.status },
        lines: { type: 'number', accessor: (order) => order.items.length },
        order_date: { type: 'date', accessor: (order) => order.order_date },
      }),
    [filteredOrders, sortState, vendorsById],
  );
  const activeFilters = [
    search ? { key: 'search', label: `Search: ${search}`, onRemove: () => setSearch('') } : null,
    statusFilter !== 'ALL' ? { key: 'status', label: `Status: ${statusFilter.replaceAll('_', ' ')}`, onRemove: () => setStatusFilter('ALL') } : null,
    vendorFilter !== 'ALL'
      ? {
          key: 'vendor',
          label: `Vendor: ${vendorsById[Number(vendorFilter)]?.name ?? vendorFilter}`,
          onRemove: () => setVendorFilter('ALL'),
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
        kicker="Purchasing"
        title="Purchase orders"
        description="Review purchase order records only. Create and receiving workflows stay on their own focused screens."
        actions={mayWrite ? <Link to="/purchases/new"><Button><Plus size={16} />Purchase Order</Button></Link> : null}
      />
      <TableShell
        description={`${sortedOrders.length} purchase order(s) in view`}
        emptyAction={!hasActiveFilters && mayWrite ? <Link to="/purchases/new"><Button>Create purchase order</Button></Link> : null}
        emptyDescription={hasActiveFilters ? 'Adjust your supplier, status, date, or search filters.' : 'Create a purchase order when buying stock from a supplier.'}
        emptyIllustration={hasActiveFilters ? emptyStateIllustrations.noResult : emptyStateIllustrations.billings}
        emptySecondaryActionLabel={hasActiveFilters ? 'Clear filters' : undefined}
        emptyTitle={hasActiveFilters ? 'No matching purchase orders found' : 'No purchase orders created yet'}
        error={error}
        isEmpty={sortedOrders.length === 0}
        isLoading={isLoading}
        onEmptySecondaryAction={hasActiveFilters ? () => { setSearch(''); setStatusFilter('ALL'); setVendorFilter('ALL'); setDateRange({ from: '', to: '' }); } : undefined}
        rowCount={sortedOrders.length}
        title="Orders"
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
                    setVendorFilter('ALL');
                    setDateRange({ from: '', to: '' });
                  }
                : undefined
            }
            onSearchChange={setSearch}
            searchPlaceholder="Search PO number or vendor"
            searchValue={search}
            tabs={statusTabs.map((status) => ({
              key: status,
              label: status === 'ALL' ? 'All' : status.replaceAll('_', ' '),
              active: statusFilter === status,
              count: status === 'ALL' ? orders.length : orders.filter((row) => row.status === status).length,
              onClick: () => setStatusFilter(status),
            }))}
          >
            <label className="block min-w-[180px]">
              <span className="mb-2 block text-sm font-medium text-warelyn-text">Vendor</span>
              <select
                className="block w-full rounded-lg border border-warelyn-border bg-white px-3 py-2.5 text-sm text-warelyn-text shadow-sm outline-none transition focus:border-warelyn-primary focus:ring-4 focus:ring-blue-900/10"
                onChange={(event) => setVendorFilter(event.target.value)}
                value={vendorFilter}
              >
                <option value="ALL">All vendors</option>
                {Object.values(vendorsById)
                  .sort((left, right) => left.name.localeCompare(right.name))
                  .map((vendor) => (
                    <option key={vendor.id} value={vendor.id}>
                      {vendor.name}
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
              <th><SortableHeader label="PO number" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="po_number" sortState={sortState} /></th>
              <th><SortableHeader label="Vendor" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="vendor" sortState={sortState} /></th>
              <th><SortableHeader label="Status" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="status" sortState={sortState} /></th>
              <th>Bill</th>
              <th className="text-right"><SortableHeader align="right" label="Lines" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="lines" sortState={sortState} /></th>
              <th><SortableHeader label="Date" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="order_date" sortState={sortState} /></th>
              <th />
            </tr>
          </thead>
          <tbody>
            {sortedOrders.map((order) => (
              <tr key={order.id}>
                <td><Link className="font-semibold text-warelyn-primary" to={`/purchases/${order.id}`}>{order.po_number}</Link></td>
                <td>{vendorsById[order.vendor_id]?.name ?? `Vendor #${order.vendor_id}`}</td>
                <td><StatusBadge status={order.status}>{order.status}</StatusBadge></td>
                <td>
                  {billByPurchaseOrderId[order.id] ? (
                    <Link className="inline-flex" to={`/bills/${billByPurchaseOrderId[order.id].id}`}>
                      <StatusBadge status="COMMITTED">Bill generated</StatusBadge>
                    </Link>
                  ) : (
                    <StatusBadge status="DRAFT">Not generated</StatusBadge>
                  )}
                </td>
                <td className="number-cell">{order.items.length}</td>
                <td>{formatDate(order.order_date)}</td>
                <td className="text-right">
                  <ActionMenu items={[
                    { label: 'View', icon: Eye, onClick: () => navigate(`/purchases/${order.id}`) },
                    ...(mayWrite && ['SUBMITTED', 'PARTIALLY_RECEIVED'].includes(order.status) ? [{ label: 'Receive', icon: ReceiptText, onClick: () => navigate(`/purchases/${order.id}/receive`) }] : []),
                  ]} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </TableShell>
    </div>
  );
}
