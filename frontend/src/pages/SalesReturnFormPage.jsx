import { useEffect, useState } from 'react';
import { BackButton } from '../components/ui/BackButton.jsx';
import { useNavigate, useSearchParams } from 'react-router-dom';

import { PageHeader } from '../components/ui/PageHeader.jsx';
import { Button } from '../components/ui/Button.jsx';
import { Card, CardBody, CardHeader } from '../components/ui/Card.jsx';
import { ErrorState } from '../components/ui/ErrorState.jsx';
import { Input } from '../components/ui/Input.jsx';
import { LoadingState } from '../components/ui/LoadingState.jsx';
import { StockImpactPreview } from '../components/ui/StockImpactPreview.jsx';
import { formatDecimal } from '../utils/formatters.js';
import { useAuth } from '../context/AuthContext.jsx';
import * as catalogService from '../services/catalogService.js';
import * as returnsService from '../services/returnsService.js';
import * as salesService from '../services/salesService.js';
import * as warehouseService from '../services/warehouseService.js';

const selectClass = 'block w-full rounded-lg border border-warelyn-border bg-white px-3 py-2.5 text-sm text-warelyn-text shadow-sm outline-none transition focus:border-warelyn-primary focus:ring-4 focus:ring-blue-900/10';
const returnableStatuses = new Set(['PARTIALLY_FULFILLED', 'FULFILLED', 'CLOSED']);

export function SalesReturnFormPage() {
  const { accessToken } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [orders, setOrders] = useState([]);
  const [productsById, setProductsById] = useState({});
  const [warehouses, setWarehouses] = useState([]);
  const [locationsByWarehouse, setLocationsByWarehouse] = useState({});
  const [form, setForm] = useState({
    sales_order_id: searchParams.get('sales_order_id') || '',
    return_number: `RET-${Date.now()}`,
    reason: '',
    notes: '',
  });
  const [lines, setLines] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    async function load() {
      setIsLoading(true);
      setError('');
      try {
        const [orderRows, productRows, warehouseRows] = await Promise.all([
          salesService.listSalesOrders(accessToken),
          catalogService.listProducts(accessToken),
          warehouseService.listWarehouses(accessToken),
        ]);
        const locationPairs = await Promise.all(
          warehouseRows.map(async (warehouse) => [warehouse.id, await warehouseService.listWarehouseLocations(accessToken, warehouse.id)]),
        );
        setOrders(orderRows.filter((order) => returnableStatuses.has(order.status)));
        setProductsById(Object.fromEntries(productRows.map((product) => [product.id, product])));
        setWarehouses(warehouseRows);
        setLocationsByWarehouse(Object.fromEntries(locationPairs));
      } catch (loadError) {
        setError(loadError.message);
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, [accessToken]);

  const selectedOrder = orders.find((order) => String(order.id) === String(form.sales_order_id));

  useEffect(() => {
    if (!selectedOrder || lines.length) return;
    const firstWarehouse = warehouses[0]?.id ? String(warehouses[0].id) : '';
    const firstLocation =
      firstWarehouse && locationsByWarehouse[firstWarehouse]?.[0]?.id
        ? String(locationsByWarehouse[firstWarehouse][0].id)
        : '';
    setLines(
      selectedOrder.items
        .filter((item) => Number(item.fulfilled_quantity) > 0)
        .map((item) => ({
          sales_order_item_id: item.id,
          warehouse_id: firstWarehouse,
          location_id: firstLocation,
          returned_quantity: '1',
          batch_id: '',
          serial_id: '',
          include: true,
        })),
    );
  }, [selectedOrder, warehouses, locationsByWarehouse, lines.length]);

  function updateLine(index, key, value) {
    setLines((current) =>
      current.map((line, lineIndex) => {
        if (lineIndex !== index) return line;
        if (key === 'warehouse_id') {
          const firstLocation = locationsByWarehouse[value]?.[0]?.id ?? '';
          return { ...line, warehouse_id: value, location_id: firstLocation ? String(firstLocation) : '' };
        }
        return { ...line, [key]: value };
      }),
    );
  }

  async function submit(event) {
    event.preventDefault();
    setIsSaving(true);
    setError('');
    try {
      const payload = {
        ...form,
        sales_order_id: Number(form.sales_order_id),
        items: lines
          .filter((line) => line.include)
          .map((line) => ({
            sales_order_item_id: Number(line.sales_order_item_id),
            warehouse_id: Number(line.warehouse_id),
            location_id: Number(line.location_id),
            returned_quantity: line.returned_quantity,
            batch_id: line.batch_id ? Number(line.batch_id) : null,
            serial_id: line.serial_id ? Number(line.serial_id) : null,
          })),
      };
      const created = await returnsService.createSalesReturn(accessToken, payload);
      navigate(`/returns/${created.id}`);
    } catch (saveError) {
      setError(saveError.message);
    } finally {
      setIsSaving(false);
    }
  }

  if (isLoading) return <LoadingState />;

  const advisoryItems = lines
    .filter((line) => line.include)
    .map((line) => {
      const orderItem = selectedOrder?.items.find((item) => item.id === line.sales_order_item_id);
      const product = productsById[orderItem?.product_id];
      const warehouse = warehouses.find((item) => String(item.id) === String(line.warehouse_id));
      const location = (locationsByWarehouse[line.warehouse_id] ?? []).find(
        (item) => String(item.id) === String(line.location_id),
      );
      return {
        id: line.sales_order_item_id,
        product: product?.name ?? `Product #${orderItem?.product_id}`,
        meta: `${warehouse?.name ?? 'Warehouse'} • ${location?.name ?? 'Location'} • Fulfilled ${formatDecimal(orderItem?.fulfilled_quantity)}`,
        effect: `Return request for ${formatDecimal(line.returned_quantity)} units. Stock remains unchanged until QC processing.`,
        warning: product?.track_serial ? 'Serial-tracked products should reference the sold serial ID when available.' : null,
      };
    });

  return (
    <div className="space-y-6">
      <BackButton to="/returns" />
      <PageHeader
        backTo="/returns"
        description="Create a return request from a fulfilled sales order. Inspection later determines whether stock is restocked, blocked, or rejected."
        kicker="Returns"
        title="Create sales return"
      />
      {error ? <ErrorState description={error} /> : null}
      <form className="space-y-6" onSubmit={submit}>
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-warelyn-text">Return header</h2>
          </CardHeader>
          <CardBody className="grid gap-4 md:grid-cols-2">
            <Input label="Return number" required value={form.return_number} onChange={(event) => setForm({ ...form, return_number: event.target.value })} />
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-warelyn-text">Fulfilled sales order</span>
              <select
                className={selectClass}
                required
                value={form.sales_order_id}
                onChange={(event) => {
                  setForm({ ...form, sales_order_id: event.target.value });
                  setLines([]);
                }}
              >
                <option value="">Select order</option>
                {orders.map((order) => (
                  <option key={order.id} value={order.id}>
                    {order.order_number} ({order.status})
                  </option>
                ))}
              </select>
            </label>
            <Input label="Reason" value={form.reason} onChange={(event) => setForm({ ...form, reason: event.target.value })} />
            <Input label="Notes" value={form.notes} onChange={(event) => setForm({ ...form, notes: event.target.value })} />
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-warelyn-text">Return lines</h2>
          </CardHeader>
          <CardBody className="space-y-4">
            {lines.map((line, index) => {
              const orderItem = selectedOrder?.items.find((item) => item.id === line.sales_order_item_id);
              const product = productsById[orderItem?.product_id];
              return (
                <div className="grid gap-3 rounded-xl border border-warelyn-border p-4 lg:grid-cols-[minmax(0,1.2fr)_130px_1fr_1fr_140px_140px]" key={line.sales_order_item_id}>
                  <label className="flex items-start gap-3 text-sm font-semibold text-warelyn-text">
                    <input checked={line.include} type="checkbox" onChange={(event) => updateLine(index, 'include', event.target.checked)} />
                    <span>
                      <span className="block">{product?.name ?? `Product #${orderItem?.product_id}`}</span>
                      <span className="mt-1 block text-xs font-normal text-warelyn-muted">
                        SKU {product?.sku ?? '-'} • Fulfilled {formatDecimal(orderItem?.fulfilled_quantity)}
                      </span>
                    </span>
                  </label>
                  <Input
                    label="Return qty"
                    min="0.001"
                    step="0.001"
                    type="number"
                    value={line.returned_quantity}
                    onChange={(event) => updateLine(index, 'returned_quantity', event.target.value)}
                  />
                  <label className="block">
                    <span className="mb-2 block text-sm font-medium text-warelyn-text">Warehouse</span>
                    <select className={selectClass} value={line.warehouse_id} onChange={(event) => updateLine(index, 'warehouse_id', event.target.value)}>
                      {warehouses.map((warehouse) => (
                        <option key={warehouse.id} value={warehouse.id}>
                          {warehouse.name}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label className="block">
                    <span className="mb-2 block text-sm font-medium text-warelyn-text">Location</span>
                    <select className={selectClass} value={line.location_id} onChange={(event) => updateLine(index, 'location_id', event.target.value)}>
                      {(locationsByWarehouse[line.warehouse_id] ?? []).map((location) => (
                        <option key={location.id} value={location.id}>
                          {location.name}
                        </option>
                      ))}
                    </select>
                  </label>
                  <Input label="Batch ID" value={line.batch_id} onChange={(event) => updateLine(index, 'batch_id', event.target.value)} />
                  <Input label="Serial ID" value={line.serial_id} onChange={(event) => updateLine(index, 'serial_id', event.target.value)} />
                </div>
              );
            })}
          </CardBody>
        </Card>

        <StockImpactPreview items={advisoryItems} title="Return request preview" />

        <div className="sticky-form-footer">
          <div className="workflow-helper-panel max-w-xl">
            <h3>What happens next?</h3>
            <p>This creates the return document only. Inspection later decides whether returned quantity becomes sellable stock, blocked stock, or no stock movement at all.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button onClick={() => navigate('/returns')} type="button" variant="ghost">
              Cancel
            </Button>
            <Button disabled={isSaving} type="submit">
              {isSaving ? 'Creating...' : 'Create return'}
            </Button>
          </div>
        </div>
      </form>
    </div>
  );
}
