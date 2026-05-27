import { ClipboardCheck, Eye, Plus } from 'lucide-react';
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
import * as catalogService from '../services/catalogService.js';
import * as returnsService from '../services/returnsService.js';
import * as salesService from '../services/salesService.js';

const canWrite = new Set(['TENANT_ADMIN', 'INVENTORY_MANAGER', 'SALES_STAFF']);
const statusTabs = ['ALL', 'DRAFT', 'SUBMITTED', 'INSPECTION_PENDING', 'PARTIALLY_PROCESSED', 'PROCESSED', 'CANCELLED'];

export function ReturnsPage({ mode = 'all' }) {
  const { accessToken, user } = useAuth();
  const navigate = useNavigate();
  const [returns, setReturns] = useState([]);
  const [salesOrdersById, setSalesOrdersById] = useState({});
  const [customersById, setCustomersById] = useState({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [statusFilter, setStatusFilter] = useState(mode === 'qc' ? 'INSPECTION_PENDING' : 'ALL');
  const [dateRange, setDateRange] = useState({ from: '', to: '' });
  const [search, setSearch] = useState('');
  const [sortState, setSortState] = useState({ key: 'created_at', direction: 'desc' });
  const isQcMode = mode === 'qc';

  useEffect(() => {
    async function load() {
      setIsLoading(true);
      setError('');
      try {
        const [returnRows, orderRows, customerRows] = await Promise.all([
          returnsService.listSalesReturns(accessToken),
          salesService.listSalesOrders(accessToken),
          catalogService.listCustomers(accessToken),
        ]);
        setReturns(returnRows);
        setSalesOrdersById(Object.fromEntries(orderRows.map((order) => [order.id, order])));
        setCustomersById(Object.fromEntries(customerRows.map((customer) => [customer.id, customer])));
      } catch (loadError) {
        setError(loadError.message);
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, [accessToken]);

  const filteredReturns = useMemo(() => {
    return returns.filter((row) => {
      if (statusFilter !== 'ALL' && row.status !== statusFilter) return false;
      if ((dateRange.from || dateRange.to) && !isDateInRange(row.created_at, dateRange)) return false;
      if (!search) return true;
      const order = salesOrdersById[row.sales_order_id];
      const customerName = customersById[order?.customer_id]?.name ?? '';
      return `${row.return_number} ${row.sales_order_id} ${customerName} ${row.status}`.toLowerCase().includes(search.toLowerCase());
    });
  }, [customersById, dateRange, returns, salesOrdersById, search, statusFilter]);
  const sortedReturns = useMemo(
    () =>
      sortRows(filteredReturns, sortState, {
        return_number: { type: 'text', accessor: (row) => row.return_number },
        sales_order: { type: 'text', accessor: (row) => salesOrdersById[row.sales_order_id]?.order_number ?? row.sales_order_id },
        customer: { type: 'text', accessor: (row) => customersById[salesOrdersById[row.sales_order_id]?.customer_id]?.name ?? '' },
        status: { type: 'text', accessor: (row) => row.status },
        lines: { type: 'number', accessor: (row) => row.items.length },
        created_at: { type: 'date', accessor: (row) => row.created_at },
      }),
    [customersById, filteredReturns, salesOrdersById, sortState],
  );
  const activeFilters = [
    search ? { key: 'search', label: `Search: ${search}`, onRemove: () => setSearch('') } : null,
    statusFilter !== 'ALL' ? { key: 'status', label: `Status: ${statusFilter.replaceAll('_', ' ')}`, onRemove: () => setStatusFilter(isQcMode ? 'INSPECTION_PENDING' : 'ALL') } : null,
    dateRange.from || dateRange.to
      ? { key: 'date', label: `Date: ${getDateRangeLabel(dateRange)}`, onRemove: () => setDateRange({ from: '', to: '' }) }
      : null,
  ].filter(Boolean);
  const hasActiveFilters = activeFilters.length > 0;
  return (
    <div className="space-y-6">
      <PageHeader
        kicker={isQcMode ? 'Returns QC' : 'Returns'}
        title={isQcMode ? 'Returns QC queue' : 'Sales returns'}
        description={isQcMode ? 'Review returns waiting for inspection and open the dedicated QC workflow.' : 'Review return records only. Creation and QC processing stay on focused workflow pages.'}
        actions={!isQcMode && canWrite.has(user?.role) ? <Link to="/returns/new"><Button><Plus size={16} />Return</Button></Link> : null}
      />
      <TableShell
        description={`${sortedReturns.length} return(s) in view`}
        emptyAction={!isQcMode && !hasActiveFilters && canWrite.has(user?.role) ? <Link to="/returns/new"><Button>Create return</Button></Link> : null}
        emptyDescription={hasActiveFilters ? 'Try changing your search keyword or clearing filters.' : isQcMode ? 'Returns that need inspection will appear here.' : 'Returned items that need inspection will appear here.'}
        emptyIllustration={hasActiveFilters ? emptyStateIllustrations.noResult : emptyStateIllustrations.sales}
        emptySecondaryActionLabel={hasActiveFilters ? 'Clear filters' : undefined}
        emptyTitle={hasActiveFilters ? 'No matching results found' : isQcMode ? 'No returns waiting for QC' : 'No returns waiting'}
        error={error}
        isEmpty={sortedReturns.length === 0}
        isLoading={isLoading}
        onEmptySecondaryAction={hasActiveFilters ? () => { setSearch(''); setStatusFilter(isQcMode ? 'INSPECTION_PENDING' : 'ALL'); setDateRange({ from: '', to: '' }); } : undefined}
        rowCount={sortedReturns.length}
        title={isQcMode ? 'QC queue' : 'Return queue'}
        toolbar={
          <ScreenToolbar
            activeFilters={activeFilters}
            dateRange={dateRange}
            onDateChange={setDateRange}
            onReset={
              hasActiveFilters
                ? () => {
                    setSearch('');
                    setStatusFilter(isQcMode ? 'INSPECTION_PENDING' : 'ALL');
                    setDateRange({ from: '', to: '' });
                  }
                : undefined
            }
            onSearchChange={setSearch}
            searchPlaceholder="Search return number, sales order, or customer"
            searchValue={search}
            tabs={(isQcMode ? ['INSPECTION_PENDING', 'SUBMITTED', 'PARTIALLY_PROCESSED', 'PROCESSED'] : statusTabs).map((status) => ({
              key: status,
              label: status === 'ALL' ? 'All' : status.replaceAll('_', ' '),
              active: statusFilter === status,
              count: status === 'ALL' ? returns.length : returns.filter((row) => row.status === status).length,
              onClick: () => setStatusFilter(status),
            }))}
          />
        }
      >
        <table>
          <thead>
            <tr>
              <th><SortableHeader label="Return number" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="return_number" sortState={sortState} /></th>
              <th><SortableHeader label="Sales order" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="sales_order" sortState={sortState} /></th>
              <th><SortableHeader label="Customer" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="customer" sortState={sortState} /></th>
              <th><SortableHeader label="Status" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="status" sortState={sortState} /></th>
              <th className="text-right"><SortableHeader align="right" label="Lines" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="lines" sortState={sortState} /></th>
              <th><SortableHeader label="Created" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="created_at" sortState={sortState} /></th>
              <th />
            </tr>
          </thead>
          <tbody>
            {sortedReturns.map((row) => {
              const order = salesOrdersById[row.sales_order_id];
              const customerName = customersById[order?.customer_id]?.name ?? '-';
              return (
              <tr key={row.id}>
                <td><Link className="font-semibold text-warelyn-primary" to={`/returns/${row.id}`}>{row.return_number}</Link></td>
                <td><span className="mono-cell">{order?.order_number ?? `#${row.sales_order_id}`}</span></td>
                <td>{customerName}</td>
                <td><StatusBadge status={row.status}>{row.status}</StatusBadge></td>
                <td className="number-cell">{row.items.length}</td>
                <td>{formatDate(row.created_at)}</td>
                <td className="text-right">
                  <ActionMenu items={[
                    { label: 'View', icon: Eye, onClick: () => navigate(`/returns/${row.id}`) },
                    ...(canWrite.has(user?.role) && ['SUBMITTED', 'INSPECTION_PENDING'].includes(row.status) ? [{ label: 'Inspect', icon: ClipboardCheck, onClick: () => navigate(`/returns/${row.id}/inspect`) }] : []),
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
