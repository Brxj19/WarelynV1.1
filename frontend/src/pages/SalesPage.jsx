import { Eye, PackageCheck, Plus } from 'lucide-react';
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
import * as salesService from '../services/salesService.js';

const canWrite = new Set(['TENANT_ADMIN', 'INVENTORY_MANAGER', 'SALES_STAFF']);
const statusTabs = ['ALL', 'DRAFT', 'CONFIRMED', 'PARTIALLY_FULFILLED', 'FULFILLED', 'CANCELLED', 'CLOSED'];

export function SalesPage() {
  const { accessToken, user } = useAuth();
  const navigate = useNavigate();
  const [orders, setOrders] = useState([]);
  const [customersById, setCustomersById] = useState({});
  const [invoices, setInvoices] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [customerFilter, setCustomerFilter] = useState('ALL');
  const [dateRange, setDateRange] = useState({ from: '', to: '' });
  const [search, setSearch] = useState('');
  const [sortState, setSortState] = useState({ key: 'order_date', direction: 'desc' });
  const mayWrite = canWrite.has(user?.role);

  useEffect(() => {
    async function load() {
      setIsLoading(true);
      setError('');
      try {
        const [orderRows, customerRows, invoiceRows] = await Promise.all([
          salesService.listSalesOrders(accessToken),
          catalogService.listCustomers(accessToken),
          documentService.listInvoices(accessToken),
        ]);
        setOrders(orderRows);
        setCustomersById(Object.fromEntries(customerRows.map((row) => [row.id, row])));
        setInvoices(invoiceRows);
      } catch (loadError) {
        setError(loadError.message);
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, [accessToken]);

  const invoiceBySalesOrderId = useMemo(
    () =>
      Object.fromEntries(
        invoices
          .filter((invoice) => invoice.sales_order_id && invoice.status !== 'VOID')
          .map((invoice) => [invoice.sales_order_id, invoice]),
      ),
    [invoices],
  );

  const filteredOrders = useMemo(() => {
    return orders.filter((order) => {
      if (statusFilter !== 'ALL' && order.status !== statusFilter) return false;
      if (customerFilter !== 'ALL' && String(order.customer_id) !== customerFilter) return false;
      if ((dateRange.from || dateRange.to) && !isDateInRange(order.order_date, dateRange)) return false;
      if (!search) return true;
      const value = search.toLowerCase();
      const customerName = customersById[order.customer_id]?.name ?? '';
      return `${order.order_number} ${customerName} ${order.status}`.toLowerCase().includes(value);
    });
  }, [customerFilter, customersById, dateRange, orders, search, statusFilter]);
  const sortedOrders = useMemo(
    () =>
      sortRows(filteredOrders, sortState, {
        order_number: { type: 'text', accessor: (order) => order.order_number },
        customer: { type: 'text', accessor: (order) => customersById[order.customer_id]?.name ?? '' },
        status: { type: 'text', accessor: (order) => order.status },
        lines: { type: 'number', accessor: (order) => order.items.length },
        order_date: { type: 'date', accessor: (order) => order.order_date },
      }),
    [customersById, filteredOrders, sortState],
  );
  const activeFilters = [
    search ? { key: 'search', label: `Search: ${search}`, onRemove: () => setSearch('') } : null,
    statusFilter !== 'ALL' ? { key: 'status', label: `Status: ${statusFilter.replaceAll('_', ' ')}`, onRemove: () => setStatusFilter('ALL') } : null,
    customerFilter !== 'ALL'
      ? {
          key: 'customer',
          label: `Customer: ${customersById[Number(customerFilter)]?.name ?? customerFilter}`,
          onRemove: () => setCustomerFilter('ALL'),
        }
      : null,
    dateRange.from || dateRange.to
      ? { key: 'date', label: `Date: ${getDateRangeLabel(dateRange)}`, onRemove: () => setDateRange({ from: '', to: '' }) }
      : null,
  ].filter(Boolean);
  const hasActiveFilters = activeFilters.length > 0;

  return (
    <div className="space-y-6">
      <PageHeader kicker="Sales" title="Sales orders" description="Review sales order records only. Confirmation, picking, packing, fulfillment, and returns each stay on focused workflow pages." actions={mayWrite ? <Link to="/sales/new"><Button><Plus size={16} />Sales Order</Button></Link> : null} />
      <TableShell
        description={`${sortedOrders.length} sales order(s) in view`}
        emptyAction={!hasActiveFilters && mayWrite ? <Link to="/sales/new"><Button>Create sales order</Button></Link> : null}
        emptyDescription={hasActiveFilters ? 'Adjust your customer, status, date, or sales order number filters.' : 'Create a sales order when a customer places an order.'}
        emptyIllustration={hasActiveFilters ? emptyStateIllustrations.noResult : emptyStateIllustrations.sales}
        emptySecondaryActionLabel={hasActiveFilters ? 'Clear filters' : undefined}
        emptyTitle={hasActiveFilters ? 'No matching sales orders found' : 'No sales orders created yet'}
        error={error}
        isEmpty={sortedOrders.length === 0}
        isLoading={isLoading}
        onEmptySecondaryAction={hasActiveFilters ? () => { setSearch(''); setStatusFilter('ALL'); setCustomerFilter('ALL'); setDateRange({ from: '', to: '' }); } : undefined}
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
                    setCustomerFilter('ALL');
                    setDateRange({ from: '', to: '' });
                  }
                : undefined
            }
            onSearchChange={setSearch}
            searchPlaceholder="Search order number or customer"
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
              <span className="mb-2 block text-sm font-medium text-warelyn-text">Customer</span>
              <select
                className="block w-full rounded-lg border border-warelyn-border bg-white px-3 py-2.5 text-sm text-warelyn-text shadow-sm outline-none transition focus:border-warelyn-primary focus:ring-4 focus:ring-blue-900/10"
                onChange={(event) => setCustomerFilter(event.target.value)}
                value={customerFilter}
              >
                <option value="ALL">All customers</option>
                {Object.values(customersById)
                  .sort((left, right) => left.name.localeCompare(right.name))
                  .map((customer) => (
                    <option key={customer.id} value={customer.id}>
                      {customer.name}
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
              <th><SortableHeader label="SO number" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="order_number" sortState={sortState} /></th>
              <th><SortableHeader label="Customer" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="customer" sortState={sortState} /></th>
              <th><SortableHeader label="Status" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="status" sortState={sortState} /></th>
              <th>Invoice</th>
              <th className="text-right"><SortableHeader align="right" label="Lines" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="lines" sortState={sortState} /></th>
              <th><SortableHeader label="Date" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="order_date" sortState={sortState} /></th>
              <th />
            </tr>
          </thead>
          <tbody>
            {sortedOrders.map((order) => (
              <tr key={order.id}>
                <td><Link className="font-semibold text-warelyn-primary" to={`/sales/${order.id}`}>{order.order_number}</Link></td>
                <td>{customersById[order.customer_id]?.name ?? `Customer #${order.customer_id}`}</td>
                <td><StatusBadge status={order.status}>{order.status}</StatusBadge></td>
                <td>
                  {invoiceBySalesOrderId[order.id] ? (
                    <Link className="inline-flex" to={`/invoices/${invoiceBySalesOrderId[order.id].id}`}>
                      <StatusBadge status="COMMITTED">Invoice generated</StatusBadge>
                    </Link>
                  ) : (
                    <StatusBadge status="DRAFT">Not generated</StatusBadge>
                  )}
                </td>
                <td className="number-cell">{order.items.length}</td>
                <td>{formatDate(order.order_date)}</td>
                <td className="text-right">
                  <ActionMenu items={[
                    { label: 'View', icon: Eye, onClick: () => navigate(`/sales/${order.id}`) },
                    ...(mayWrite && ['CONFIRMED', 'PARTIALLY_FULFILLED'].includes(order.status) ? [{ label: 'Pick workflow', icon: PackageCheck, onClick: () => navigate(`/sales/${order.id}/pick`) }] : []),
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
