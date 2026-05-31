import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

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
import * as inventoryService from '../services/inventoryService.js';
import * as salesService from '../services/salesService.js';
import * as warehouseService from '../services/warehouseService.js';

const selectClass = 'block w-full rounded-lg border border-warelyn-border bg-white px-3 py-2.5 text-sm text-warelyn-text shadow-sm outline-none transition focus:border-warelyn-primary focus:ring-4 focus:ring-blue-900/10';

export function SalesFulfillPage() {
  const { id } = useParams();
  const { accessToken } = useAuth();
  const navigate = useNavigate();
  const [order, setOrder] = useState(null);
  const [productsById, setProductsById] = useState({});
  const [warehouses, setWarehouses] = useState([]);
  const [locationsByWarehouse, setLocationsByWarehouse] = useState({});
  const [reservations, setReservations] = useState([]);
  const [fulfillmentNumber, setFulfillmentNumber] = useState(`FUL-${Date.now()}`);
  const [lines, setLines] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    async function load() {
      setIsLoading(true);
      setError('');
      try {
        const [orderRow, warehouseRows, productRows, reservationRows] = await Promise.all([
          salesService.getSalesOrder(accessToken, id),
          warehouseService.listWarehouses(accessToken),
          catalogService.listProducts(accessToken),
          inventoryService.listReservations(accessToken),
        ]);
        const locationPairs = await Promise.all(
          warehouseRows.map(async (warehouse) => [warehouse.id, await warehouseService.listWarehouseLocations(accessToken, warehouse.id)]),
        );
        const locationMap = Object.fromEntries(locationPairs);
        const orderReservations = reservationRows.filter(
          (reservation) =>
            reservation.reference_type === 'SALES_ORDER'
            && reservation.reference_id === orderRow.order_number
            && reservation.status === 'ACTIVE',
        );
        const orderItemByProductId = Object.fromEntries(orderRow.items.map((item) => [item.product_id, item]));
        setOrder(orderRow);
        setProductsById(Object.fromEntries(productRows.map((product) => [product.id, product])));
        setWarehouses(warehouseRows);
        setLocationsByWarehouse(locationMap);
        setReservations(orderReservations);
        setLines(
          orderReservations
            .map((reservation) => ({
              sales_order_item_id: orderItemByProductId[reservation.product_id]?.id ?? null,
              product_id: reservation.product_id,
              warehouse_id: String(reservation.warehouse_id),
              location_id: String(reservation.location_id),
              reservation_id: String(reservation.id),
              fulfilled_quantity: reservation.quantity,
            }))
            .filter((line) => line.sales_order_item_id != null),
        );
      } catch (loadError) {
        setError(loadError.message);
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, [accessToken, id]);

  function updateLine(index, key, value) {
    setLines((current) =>
      current.map((line, lineIndex) => {
        if (lineIndex !== index) return line;
        if (key === 'reservation_id') {
          const selectedReservation = reservations.find((reservation) => String(reservation.id) === String(value));
          if (selectedReservation) {
            return {
              ...line,
              reservation_id: value,
              warehouse_id: String(selectedReservation.warehouse_id),
              location_id: String(selectedReservation.location_id),
              fulfilled_quantity: selectedReservation.quantity,
            };
          }
        }
        if (key === 'warehouse_id') {
          const firstLocation = locationsByWarehouse[value]?.[0]?.id ?? '';
          return { ...line, warehouse_id: value, location_id: firstLocation ? String(firstLocation) : '' };
        }
        return { ...line, [key]: value };
      }),
    );
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setIsSaving(true);
    setError('');
    try {
      const items = lines
        .filter((line) => line.reservation_id && Number(line.fulfilled_quantity) > 0)
        .map((line) => ({
          ...line,
          sales_order_item_id: Number(line.sales_order_item_id),
          product_id: Number(line.product_id),
          warehouse_id: Number(line.warehouse_id),
          location_id: Number(line.location_id),
          reservation_id: Number(line.reservation_id),
        }));
      const fulfillment = await salesService.createSalesFulfillment(accessToken, id, {
        fulfillment_number: fulfillmentNumber,
        items,
      });
      navigate(`/sales-fulfillments/${fulfillment.id}`);
    } catch (saveError) {
      setError(saveError.message);
    } finally {
      setIsSaving(false);
    }
  }

  if (isLoading) return <LoadingState />;
  if (!order) return <ErrorState description={error || 'Sales order not found.'} />;

  const advisoryImpact = lines
    .filter((line) => Number(line.fulfilled_quantity) > 0)
    .map((line) => {
      const product = productsById[line.product_id];
      const warehouse = warehouses.find((item) => String(item.id) === String(line.warehouse_id));
      const location = (locationsByWarehouse[line.warehouse_id] ?? []).find(
        (item) => String(item.id) === String(line.location_id),
      );
      return {
        id: line.sales_order_item_id,
        product: product?.name ?? `Product #${line.product_id}`,
        meta: `${warehouse?.name ?? 'Warehouse'} • ${location?.name ?? 'Location'} • Reservation ${line.reservation_id || 'required'}`,
        effect: `Draft fulfillment prepared for ${formatDecimal(line.fulfilled_quantity)} units.`,
        warning: 'Committing the fulfillment later will deduct reserved stock through backend inventory workflows.',
      };
    });

  return (
    <div className="space-y-6">
      <PageHeader
        backTo="/sales"
        description="Fulfillment drafts can be auto-prepared after picking. Validate lines and commit manually to deduct reserved stock."
        kicker="Fulfillment"
        title={`Fulfill ${order.order_number}`}
      />
      {error ? <ErrorState description={error} /> : null}
      <form className="space-y-6" onSubmit={handleSubmit}>
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-warelyn-text">Fulfillment header</h2>
          </CardHeader>
          <CardBody className="grid gap-4 md:grid-cols-[minmax(0,1fr)_320px]">
            <div className="workflow-helper-panel">
              <h3>Commit warning</h3>
              <p>
                This screen maintains the draft only. Stock deduction happens only when the fulfillment is committed, so each line must stay aligned with an active reservation.
              </p>
            </div>
            <Input label="Fulfillment number" required value={fulfillmentNumber} onChange={(event) => setFulfillmentNumber(event.target.value)} />
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-warelyn-text">Fulfillment lines</h2>
          </CardHeader>
          <CardBody className="space-y-4">
            {lines.length === 0 ? (
              <p className="rounded-xl border border-dashed border-warelyn-border bg-slate-50 px-4 py-5 text-sm text-warelyn-muted">
                No active reservations were found for this order. Confirm the order with valid allocations before creating a fulfillment draft.
              </p>
            ) : null}
            {lines.map((line, index) => {
              const product = productsById[line.product_id];
              const reservationOptions = reservations.filter((reservation) => reservation.product_id === line.product_id);
              return (
                <div className="grid gap-3 rounded-xl border border-warelyn-border p-4 lg:grid-cols-[minmax(0,1.2fr)_180px_160px_1fr_1fr]" key={line.reservation_id || line.sales_order_item_id}>
                  <div>
                    <span className="text-xs font-semibold uppercase tracking-wide text-warelyn-muted">Product</span>
                    <p className="mt-2 font-semibold text-warelyn-text">{product?.name ?? `Product #${line.product_id}`}</p>
                    <p className="mt-1 text-xs text-warelyn-muted">SKU {product?.sku ?? '-'}</p>
                  </div>
                  <label className="block">
                    <span className="mb-2 block text-sm font-medium text-warelyn-text">Reservation</span>
                    <select
                      className={selectClass}
                      required
                      value={line.reservation_id}
                      onChange={(event) => updateLine(index, 'reservation_id', event.target.value)}
                    >
                      <option value="">Select reservation</option>
                      {reservationOptions.map((reservation) => {
                        const warehouseName = warehouses.find((warehouse) => warehouse.id === reservation.warehouse_id)?.name ?? `Warehouse #${reservation.warehouse_id}`;
                        const locationName = (locationsByWarehouse[String(reservation.warehouse_id)] ?? []).find(
                          (location) => location.id === reservation.location_id,
                        )?.name ?? `Location #${reservation.location_id}`;
                        return (
                          <option key={reservation.id} value={reservation.id}>
                            {`Res #${reservation.id} — ${formatDecimal(reservation.quantity)} units @ ${warehouseName} / ${locationName}`}
                          </option>
                        );
                      })}
                    </select>
                  </label>
                  <Input
                    label="Fulfill qty"
                    min="0.001"
                    required
                    step="0.001"
                    type="number"
                    value={line.fulfilled_quantity}
                    onChange={(event) => updateLine(index, 'fulfilled_quantity', event.target.value)}
                  />
                  <label className="block">
                    <span className="mb-2 block text-sm font-medium text-warelyn-text">Warehouse</span>
                    <select
                      className={selectClass}
                      required
                      value={line.warehouse_id}
                      onChange={(event) => updateLine(index, 'warehouse_id', event.target.value)}
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
                      value={line.location_id}
                      onChange={(event) => updateLine(index, 'location_id', event.target.value)}
                    >
                      <option value="">Select location</option>
                      {(locationsByWarehouse[line.warehouse_id] ?? []).map((location) => (
                        <option key={location.id} value={location.id}>
                          {location.name} ({location.location_type})
                        </option>
                      ))}
                    </select>
                  </label>
                </div>
              );
            })}
          </CardBody>
        </Card>

        <StockImpactPreview items={advisoryImpact} title="Fulfillment draft preview" />

        <div className="sticky-form-footer">
          <div className="workflow-helper-panel max-w-xl">
            <h3>What happens next?</h3>
            <p>The draft opens in the fulfillment detail screen. Committing there deducts reserved stock through backend inventory workflows and cannot be simulated on the frontend.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button onClick={() => navigate('/sales')} type="button" variant="ghost">
              Cancel
            </Button>
            <Button disabled={isSaving || lines.length === 0} type="submit">
              {isSaving ? 'Creating...' : 'Create fulfillment draft'}
            </Button>
          </div>
        </div>
      </form>
    </div>
  );
}
