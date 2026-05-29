import { useEffect, useState } from 'react';
import { BackButton } from '../components/ui/BackButton.jsx';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { Boxes, ListChecks, PackageCheck, Truck, Undo2 } from 'lucide-react';

import { StatusBadge } from '../components/ui/Badge.jsx';
import { Button } from '../components/ui/Button.jsx';
import { Card, CardBody, CardHeader } from '../components/ui/Card.jsx';
import { ConfirmationModal } from '../components/ui/ConfirmationModal.jsx';
import { EmptyState } from '../components/ui/EmptyState.jsx';
import { ErrorState } from '../components/ui/ErrorState.jsx';
import { Input } from '../components/ui/Input.jsx';
import { LoadingState } from '../components/ui/LoadingState.jsx';
import { RecordDetailShell } from '../components/ui/RecordDetailShell.jsx';
import { StockImpactPreview } from '../components/ui/StockImpactPreview.jsx';
import { TableShell } from '../components/ui/TableShell.jsx';
import { WorkflowProgress } from '../components/ui/WorkflowProgress.jsx';
import { formatDate, formatDecimal, formatMoney } from '../utils/formatters.js';
import { useAuth } from '../context/AuthContext.jsx';
import { useTenantSettings } from '../context/TenantSettingsContext.jsx';
import * as catalogService from '../services/catalogService.js';
import * as fulfillmentService from '../services/fulfillmentService.js';
import * as inventoryService from '../services/inventoryService.js';
import * as salesService from '../services/salesService.js';
import * as warehouseService from '../services/warehouseService.js';
import * as documentService from '../services/documentService.js';

const canWrite = new Set(['TENANT_ADMIN', 'INVENTORY_MANAGER', 'SALES_STAFF']);
const fulfillableStatuses = new Set(['CONFIRMED', 'PARTIALLY_FULFILLED']);
const salesSteps = [
  { key: 'DRAFT', label: 'Draft' },
  { key: 'CONFIRMED', label: 'Confirmed / Picking' },
  { key: 'PARTIALLY_FULFILLED', label: 'Partially Fulfilled' },
  { key: 'FULFILLED', label: 'Fulfilled / Closed', matches: ['FULFILLED', 'CLOSED'] },
];
const selectClass = 'block w-full rounded-lg border border-warelyn-border bg-white px-3 py-2.5 text-sm text-warelyn-text shadow-sm outline-none transition focus:border-warelyn-primary focus:ring-4 focus:ring-blue-900/10';

export function SalesOrderDetailPage() {
  const { id } = useParams();
  const { accessToken, user } = useAuth();
  const { currency } = useTenantSettings();
  const navigate = useNavigate();
  const [order, setOrder] = useState(null);
  const [fulfillments, setFulfillments] = useState([]);
  const [pickTasks, setPickTasks] = useState([]);
  const [packages, setPackages] = useState([]);
  const [hasInvoice, setHasInvoice] = useState(false);
  const [invoiceData, setInvoiceData] = useState(null);
  const [productsById, setProductsById] = useState({});
  const [warehouses, setWarehouses] = useState([]);
  const [locationsByWarehouse, setLocationsByWarehouse] = useState({});
  const [allocations, setAllocations] = useState([]);
  const [idempotencyKey, setIdempotencyKey] = useState(`sales-confirm-${id}-${Date.now()}`);
  const [summary, setSummary] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');
  const [pendingAction, setPendingAction] = useState(null);
  const mayWrite = canWrite.has(user?.role);

  async function load() {
    setIsLoading(true);
    setError('');
    try {
      const [orderRow, fulfillmentRows, pickRows, packageRows, productRows, warehouseRows, invoices, stockRows] = await Promise.all([
        salesService.getSalesOrder(accessToken, id),
        salesService.listSalesFulfillments(accessToken, id),
        fulfillmentService.listPickTasksForOrder(accessToken, id),
        fulfillmentService.listPackagesForOrder(accessToken, id),
        catalogService.listProducts(accessToken),
        warehouseService.listWarehouses(accessToken),
        documentService.listInvoices(accessToken),
        inventoryService.listStock(accessToken),
      ]);
      const locationPairs = await Promise.all(
        warehouseRows.map(async (warehouse) => [warehouse.id, await warehouseService.listWarehouseLocations(accessToken, warehouse.id)]),
      );
      const locationMap = Object.fromEntries(locationPairs);
      setOrder(orderRow);
      setFulfillments(fulfillmentRows);
      setPickTasks(pickRows);
      setPackages(packageRows);
      const matchedInvoice = invoices.find((inv) => inv.sales_order_id === Number(id) && inv.status !== 'VOID');
      setHasInvoice(Boolean(matchedInvoice));
      setInvoiceData(matchedInvoice || null);
      setProductsById(Object.fromEntries(productRows.map((product) => [product.id, product])));
      setWarehouses(warehouseRows);
      setLocationsByWarehouse(locationMap);
      setAllocations(buildAllocationsFromStock(orderRow.items, stockRows));
    } catch (loadError) {
      setError(loadError.message);
    } finally {
      setIsLoading(false);
    }
  }

  function buildAllocationsFromStock(orderItems, stockRows) {
    const availableStock = stockRows
      .filter((s) => Number(s.quantity_available) > 0)
      .map((s) => ({ ...s, remaining: Number(s.quantity_available) }));

    return orderItems.map((item) => {
      const needed = Number(item.ordered_quantity);
      const match = availableStock.find((s) => s.product_id === item.product_id && s.remaining >= needed);
      if (match) {
        match.remaining -= needed;
        return {
          sales_order_item_id: item.id,
          warehouse_id: String(match.warehouse_id),
          location_id: String(match.location_id),
          quantity: item.ordered_quantity,
        };
      }
      const partialMatch = availableStock.find((s) => s.product_id === item.product_id && s.remaining > 0);
      if (partialMatch) {
        partialMatch.remaining -= needed;
        return {
          sales_order_item_id: item.id,
          warehouse_id: String(partialMatch.warehouse_id),
          location_id: String(partialMatch.location_id),
          quantity: item.ordered_quantity,
        };
      }
      return {
        sales_order_item_id: item.id,
        warehouse_id: '',
        location_id: '',
        quantity: item.ordered_quantity,
      };
    });
  }

  useEffect(() => {
    load();
  }, [accessToken, id]);

  function updateAllocation(index, key, value) {
    setAllocations((current) =>
      current.map((allocation, allocationIndex) => {
        if (allocationIndex !== index) return allocation;
        if (key === 'warehouse_id') {
          const firstLocation = locationsByWarehouse[value]?.[0]?.id ?? '';
          return { ...allocation, warehouse_id: value, location_id: firstLocation ? String(firstLocation) : '' };
        }
        return { ...allocation, [key]: value };
      }),
    );
  }

  async function confirm() {
    setIsSaving(true);
    setError('');
    try {
      const result = await salesService.confirmSalesOrder(accessToken, id, {
        idempotency_key: idempotencyKey,
        allocations: allocations.map((allocation) => ({
          ...allocation,
          warehouse_id: Number(allocation.warehouse_id),
          location_id: Number(allocation.location_id),
          sales_order_item_id: Number(allocation.sales_order_item_id),
        })),
      });
      setSummary(result);
      await load();
    } catch (confirmError) {
      setError(confirmError.message);
    } finally {
      setIsSaving(false);
    }
  }

  async function runAction(action) {
    setIsSaving(true);
    setError('');
    try {
      await action(accessToken, id);
      await load();
    } catch (actionError) {
      setError(actionError.message);
    } finally {
      setIsSaving(false);
    }
  }



  if (isLoading) return <LoadingState />;
  if (!order) return <ErrorState description={error || 'Sales order not found.'} />;

  const orderedQty = order.items.reduce((sum, item) => sum + Number(item.ordered_quantity), 0);
  const reservedQty = order.items.reduce((sum, item) => sum + Number(item.reserved_quantity), 0);
  const fulfilledQty = order.items.reduce((sum, item) => sum + Number(item.fulfilled_quantity), 0);
  const pendingQty = orderedQty - fulfilledQty;
  const allocationPreview = allocations
    .filter((allocation) => Number(allocation.quantity) > 0)
    .map((allocation, index) => {
      const product = productsById[order.items[index]?.product_id];
      const warehouse = warehouses.find((item) => String(item.id) === String(allocation.warehouse_id));
      const location = (locationsByWarehouse[allocation.warehouse_id] ?? []).find(
        (item) => String(item.id) === String(allocation.location_id),
      );
      return {
        id: allocation.sales_order_item_id,
        product: product?.name ?? `Product #${order.items[index]?.product_id}`,
        meta: `${warehouse?.name ?? 'Warehouse'} • ${location?.name ?? 'Location'} • SKU ${product?.sku ?? '-'}`,
        effect: `Backend reservation request for ${formatDecimal(allocation.quantity)} units on confirmation.`,
        warning: product?.track_serial ? 'Serial-tracked items should reserve one unit per serial-aware line.' : null,
      };
    });

  return (
    <div className="space-y-6">
      <BackButton to="/sales" />
      {error ? <ErrorState description={error} /> : null}
      <RecordDetailShell
        actions={
          <div className="flex flex-wrap gap-2">
            {mayWrite && order.status === 'DRAFT' ? (
              <Button
                disabled={isSaving}
                onClick={() =>
                  setPendingAction({
                    description:
                      'Confirming reserves backend stock using the allocation lines below. No frontend stock calculation is used.',
                    label: 'Confirm order',
                    run: confirm,
                    variant: 'primary',
                  })
                }
              >
                Confirm
              </Button>
            ) : null}
            {mayWrite && ['DRAFT', 'CONFIRMED', 'PARTIALLY_FULFILLED'].includes(order.status) ? (
              <Button
                disabled={isSaving}
                variant="danger"
                onClick={() =>
                  setPendingAction({
                    description: 'Cancel this sales order and let the backend release any active reservations.',
                    label: 'Cancel order',
                    run: () => runAction(salesService.cancelSalesOrder),
                    variant: 'danger',
                  })
                }
              >
                Cancel
              </Button>
            ) : null}
            {mayWrite && fulfillableStatuses.has(order.status) ? (
              <Button
                disabled={isSaving}
                variant="secondary"
                onClick={() =>
                  setPendingAction({
                    description: 'Close this sales order to stop further workflow activity.',
                    label: 'Close order',
                    run: () => runAction(salesService.closeSalesOrder),
                    variant: 'secondary',
                  })
                }
              >
                Close
              </Button>
            ) : null}
            {mayWrite && fulfillableStatuses.has(order.status) ? (
              <Link to={`/sales/${order.id}/pick`}>
                <Button variant="secondary">Pick</Button>
              </Link>
            ) : null}
            {mayWrite && pickTasks.some((task) => task.status === 'PICKED') ? (
              <Link to={`/sales/${order.id}/package`}>
                <Button variant="secondary">
                  <PackageCheck className="mr-1.5" size={14} /> Package
                </Button>
              </Link>
            ) : null}
            {mayWrite && fulfillableStatuses.has(order.status) && packages.some((pkg) => pkg.status === 'PACKED') ? (
              <Link to={`/sales/${order.id}/fulfill`}>
                <Button variant="secondary">
                  <Truck className="mr-1.5" size={14} /> Fulfill
                </Button>
              </Link>
            ) : null}
            {mayWrite && ['PARTIALLY_FULFILLED', 'FULFILLED', 'CLOSED'].includes(order.status) ? (
              <Link to={`/returns/new?sales_order_id=${order.id}`}>
                <Button variant="secondary">Create return</Button>
              </Link>
            ) : null}
            {mayWrite && order.status === 'DRAFT' ? <Link to={`/sales/${order.id}/edit`}><Button variant="secondary">Edit</Button></Link> : null}
            {hasInvoice && invoiceData ? <Link to={`/invoices/${invoiceData.id}`}><span className="inline-flex items-center rounded-lg bg-green-50 px-3 py-1.5 text-sm font-medium text-green-700 hover:bg-green-100 transition">{invoiceData.invoice_number} — {invoiceData.status}</span></Link> : null}
          </div>
        }
        backTo="/sales"
        description="Confirmation reserves stock, picking records allocation work, packaging stays operational, and fulfillment commits the deduction through backend inventory workflows."
        kicker="Sales order"
        meta={[
          { label: 'Customer', value: order.customer_id ? `Customer #${order.customer_id}` : '-' },
          { label: 'Order date', value: formatDate(order.order_date) },
          { label: 'Expected ship', value: order.expected_ship_date ? formatDate(order.expected_ship_date) : 'Not scheduled' },
        ]}
        progress={<WorkflowProgress current={order.status} steps={salesSteps} />}
        sidePanel={
          <Card>
            <CardHeader>
              <h2 className="text-lg font-semibold text-warelyn-text">Workflow actions</h2>
            </CardHeader>
            <CardBody className="space-y-4">
              <StatusBadge status={order.status}>{order.status}</StatusBadge>
              <div className="space-y-3 text-sm text-warelyn-muted">
                <div className="flex items-start gap-3">
                  <Boxes className="mt-0.5 shrink-0 text-warelyn-primary" size={16} />
                  <p>Reservation happens only when this document is confirmed with valid location allocations.</p>
                </div>
                <div className="flex items-start gap-3">
                  <ListChecks className="mt-0.5 shrink-0 text-warelyn-primary" size={16} />
                  <p>Pick tasks and packages stay operational until fulfillment is explicitly committed.</p>
                </div>
                <div className="flex items-start gap-3">
                  <Undo2 className="mt-0.5 shrink-0 text-warelyn-primary" size={16} />
                  <p>Returns become available only after the order has shipped or been closed.</p>
                </div>
              </div>
            </CardBody>
          </Card>
        }
        status={<StatusBadge status={order.status}>{order.status}</StatusBadge>}
        summary={[
          { label: 'Line items', value: order.items.length, helper: 'Products on this order' },
          { label: 'Ordered qty', value: formatDecimal(orderedQty), helper: 'Requested by customer' },
          { label: 'Reserved qty', value: formatDecimal(reservedQty), helper: 'Backend reservation state' },
          { label: 'Pending qty', value: formatDecimal(pendingQty), helper: `Fulfilled ${formatDecimal(fulfilledQty)}` },
        ]}
        title={order.order_number}
      >
        <TableShell
          description="Ordered, reserved, picked, and fulfilled quantities by line."
          isEmpty={order.items.length === 0}
          rowCount={order.items.length}
          title="Order items"
        >
          <table>
            <thead>
              <tr>
                <th>Product</th>
                <th>SKU</th>
                <th className="text-right">Ordered</th>
                <th className="text-right">Reserved</th>
                <th className="text-right">Fulfilled</th>
                <th className="text-right">Remaining</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {order.items.map((item) => {
                const product = productsById[item.product_id];
                const remaining = Number(item.ordered_quantity) - Number(item.fulfilled_quantity);
                return (
                  <tr key={item.id}>
                    <td>
                      <div className="space-y-1">
                        <span className="font-semibold text-warelyn-text">{product?.name ?? `Product #${item.product_id}`}</span>
                        <p className="text-xs text-warelyn-muted">
                          {[product?.track_serial ? 'Serial' : null, product?.track_batch ? 'Batch' : null, product?.track_expiry ? 'Expiry' : null]
                            .filter(Boolean)
                            .join(' • ') || 'Standard tracking'}
                        </p>
                      </div>
                    </td>
                    <td><span className="mono-cell">{product?.sku ?? '-'}</span></td>
                    <td className="number-cell">{formatDecimal(item.ordered_quantity)}</td>
                    <td className="number-cell">{formatDecimal(item.reserved_quantity)}</td>
                    <td className="number-cell">{formatDecimal(item.fulfilled_quantity)}</td>
                    <td className="number-cell">{formatDecimal(remaining)}</td>
                    <td>
                      <StatusBadge status={remaining > 0 ? 'PENDING' : 'FULFILLED'}>
                        {remaining > 0 ? 'OPEN' : 'FULFILLED'}
                      </StatusBadge>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </TableShell>

        {mayWrite && order.status === 'DRAFT' ? (
          <Card>
            <CardHeader>
              <h2 className="text-lg font-semibold text-warelyn-text">Location allocation</h2>
            </CardHeader>
            <CardBody className="space-y-4">
              <Input
                label="Idempotency key"
                required
                value={idempotencyKey}
                onChange={(event) => setIdempotencyKey(event.target.value)}
              />
              {allocations.map((allocation, index) => {
                const item = order.items[index];
                const product = productsById[item?.product_id];
                return (
                  <div className="grid gap-3 rounded-xl border border-warelyn-border p-4 md:grid-cols-4" key={allocation.sales_order_item_id}>
                    <div>
                      <span className="text-xs font-semibold uppercase tracking-wide text-warelyn-muted">Product</span>
                      <p className="mt-2 font-semibold text-warelyn-text">{product?.name ?? `#${item?.product_id}`}</p>
                      <p className="mt-1 text-xs text-warelyn-muted">SKU {product?.sku ?? '-'}</p>
                    </div>
                    <Input
                      label="Quantity"
                      min="0.001"
                      required
                      step="0.001"
                      type="number"
                      value={allocation.quantity}
                      onChange={(event) => updateAllocation(index, 'quantity', event.target.value)}
                    />
                    <label className="block">
                      <span className="mb-2 block text-sm font-medium text-warelyn-text">Warehouse</span>
                      <select
                        className={selectClass}
                        required
                        value={allocation.warehouse_id}
                        onChange={(event) => updateAllocation(index, 'warehouse_id', event.target.value)}
                      >
                        <option value="">Select warehouse</option>
                        {warehouses.map((warehouse) => (
                          <option key={warehouse.id} value={warehouse.id}>
                            {warehouse.name}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label className="block">
                      <span className="mb-2 block text-sm font-medium text-warelyn-text">Location</span>
                      <select
                        className={selectClass}
                        required
                        value={allocation.location_id}
                        onChange={(event) => updateAllocation(index, 'location_id', event.target.value)}
                      >
                        <option value="">Select location</option>
                        {(locationsByWarehouse[allocation.warehouse_id] ?? []).map((location) => (
                          <option key={location.id} value={location.id}>
                            {location.name} ({location.location_type})
                          </option>
                        ))}
                      </select>
                    </label>
                  </div>
                );
              })}
              <StockImpactPreview items={allocationPreview} title="Reservation impact preview" />
            </CardBody>
          </Card>
        ) : null}

        {summary?.stock_results?.length ? (
          <StockImpactPreview
            items={summary.stock_results.map((result, index) => ({
              id: result.reservation?.id ?? index,
              product: productsById[result.stock.product_id]?.name ?? `Product #${result.stock.product_id}`,
              meta: `Reservation #${result.reservation?.id ?? '-'} • Warehouse stock state`,
              effect: `Reserved ${formatDecimal(result.stock.quantity_reserved)} • Available ${formatDecimal(result.stock.quantity_available)}`,
            }))}
            title="Reservation results"
          />
        ) : null}

        <div className="grid gap-6 xl:grid-cols-3">
          <Card>
            <CardHeader>
              <h2 className="text-lg font-semibold text-warelyn-text">Pick tasks</h2>
            </CardHeader>
            <CardBody>
              {pickTasks.length === 0 ? (
                <EmptyState title="No pick tasks" description="Create a pick task after this order is confirmed." />
              ) : (
                <div className="space-y-3">
                  {pickTasks.map((task) => (
                    <Link className="block rounded-xl border border-warelyn-border p-4 transition hover:border-warelyn-primary" key={task.id} to={`/pick-tasks/${task.id}`}>
                      <div className="flex items-center justify-between gap-3">
                        <span className="font-semibold text-warelyn-text">{task.pick_number}</span>
                        <StatusBadge status={task.status}>{task.status}</StatusBadge>
                      </div>
                      <p className="mt-2 text-sm text-warelyn-muted">{task.items.length} line(s)</p>
                    </Link>
                  ))}
                </div>
              )}
            </CardBody>
          </Card>

          <Card>
            <CardHeader>
              <h2 className="text-lg font-semibold text-warelyn-text">Packages</h2>
            </CardHeader>
            <CardBody>
              {packages.length === 0 ? (
                <EmptyState title="No packages" description="Packed bundles will appear here after picked items are grouped." />
              ) : (
                <div className="space-y-3">
                  {packages.map((pkg) => (
                    <Link className="block rounded-xl border border-warelyn-border p-4 transition hover:border-warelyn-primary" key={pkg.id} to={`/packages/${pkg.id}`}>
                      <div className="flex items-center justify-between gap-3">
                        <span className="font-semibold text-warelyn-text">{pkg.package_number}</span>
                        <StatusBadge status={pkg.status}>{pkg.status}</StatusBadge>
                      </div>
                      <p className="mt-2 text-sm text-warelyn-muted">{pkg.items.length} item(s)</p>
                    </Link>
                  ))}
                </div>
              )}
            </CardBody>
          </Card>

          <Card>
            <CardHeader>
              <h2 className="text-lg font-semibold text-warelyn-text">Fulfillments</h2>
            </CardHeader>
            <CardBody>
              {fulfillments.length === 0 ? (
                <EmptyState title="No fulfillments" description="Committed shipment records will appear once stock is fulfilled." />
              ) : (
                <div className="space-y-3">
                  {fulfillments.map((fulfillment) => (
                    <Link className="block rounded-xl border border-warelyn-border p-4 transition hover:border-warelyn-primary" key={fulfillment.id} to={`/sales-fulfillments/${fulfillment.id}`}>
                      <div className="flex items-center justify-between gap-3">
                        <span className="font-semibold text-warelyn-text">{fulfillment.fulfillment_number}</span>
                        <StatusBadge status={fulfillment.status}>{fulfillment.status}</StatusBadge>
                      </div>
                      <p className="mt-2 text-sm text-warelyn-muted">{fulfillment.items.length} line(s)</p>
                    </Link>
                  ))}
                </div>
              )}
            </CardBody>
          </Card>
        </div>
      </RecordDetailShell>

      <ConfirmationModal
        confirmLabel={pendingAction?.label}
        description={pendingAction?.description}
        isLoading={isSaving}
        onCancel={() => setPendingAction(null)}
        onConfirm={async () => {
          await pendingAction?.run();
          setPendingAction(null);
        }}
        open={Boolean(pendingAction)}
        title="Confirm sales workflow action"
        variant={pendingAction?.variant}
      />
    </div>
  );
}
