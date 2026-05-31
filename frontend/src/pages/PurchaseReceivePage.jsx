import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { BarcodeInput } from '../components/forms/BarcodeInput.jsx';
import { PageHeader } from '../components/ui/PageHeader.jsx';
import { Button } from '../components/ui/Button.jsx';
import { Card, CardBody, CardHeader } from '../components/ui/Card.jsx';
import { ConfirmationModal } from '../components/ui/ConfirmationModal.jsx';
import { ErrorState } from '../components/ui/ErrorState.jsx';
import { Input } from '../components/ui/Input.jsx';
import { LoadingState } from '../components/ui/LoadingState.jsx';
import { StockImpactPreview } from '../components/ui/StockImpactPreview.jsx';
import { formatDecimal } from '../utils/formatters.js';
import { useAuth } from '../context/AuthContext.jsx';
import * as catalogService from '../services/catalogService.js';
import * as purchasingService from '../services/purchasingService.js';
import * as warehouseService from '../services/warehouseService.js';

const selectClass = 'block w-full rounded-lg border border-warelyn-border bg-white px-3 py-2.5 text-sm text-warelyn-text shadow-sm outline-none transition focus:border-warelyn-primary focus:ring-4 focus:ring-blue-900/10';

export function PurchaseReceivePage() {
  const { id } = useParams();
  const { accessToken } = useAuth();
  const navigate = useNavigate();
  const [order, setOrder] = useState(null);
  const [productsById, setProductsById] = useState({});
  const [warehouses, setWarehouses] = useState([]);
  const [locationsByWarehouse, setLocationsByWarehouse] = useState({});
  const [receiptNumber, setReceiptNumber] = useState(`GRN-${Date.now()}`);
  const [barcodeSearch, setBarcodeSearch] = useState('');
  const [lines, setLines] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');
  const [isConfirming, setIsConfirming] = useState(false);

  useEffect(() => {
    async function load() {
      setIsLoading(true);
      setError('');
      try {
        const [orderRow, warehouseRows, productRows] = await Promise.all([purchasingService.getPurchaseOrder(accessToken, id), warehouseService.listWarehouses(accessToken), catalogService.listProducts(accessToken)]);
        const locationPairs = await Promise.all(warehouseRows.map(async (warehouse) => [warehouse.id, await warehouseService.listWarehouseLocations(accessToken, warehouse.id)]));
        const locationMap = Object.fromEntries(locationPairs);
        const defaultWarehouse = warehouseRows[0]?.id ? String(warehouseRows[0].id) : '';
        const defaultLocation = defaultWarehouse && locationMap[defaultWarehouse]?.[0]?.id ? String(locationMap[defaultWarehouse][0].id) : '';
        setOrder(orderRow);
        setProductsById(Object.fromEntries(productRows.map((product) => [product.id, product])));
        setWarehouses(warehouseRows);
        setLocationsByWarehouse(locationMap);
        setLines(orderRow.items.map((item) => ({ purchase_order_item_id: item.id, product_id: item.product_id, warehouse_id: defaultWarehouse, location_id: defaultLocation, received_quantity: Math.max(0, Number(item.ordered_quantity) - Number(item.received_quantity)).toString(), unit_cost: item.unit_cost, batch_number: '', supplier_batch_number: '', manufacture_date: '', expiry_date: '', warranty_until: '', serial_numbers: '' })));
      } catch (loadError) {
        setError(loadError.message);
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, [accessToken, id]);

  function updateLine(index, key, value) {
    setLines((current) => current.map((line, lineIndex) => {
      if (lineIndex !== index) return line;
      if (key === 'warehouse_id') {
        const firstLocation = locationsByWarehouse[value]?.[0]?.id ?? '';
        return { ...line, warehouse_id: value, location_id: firstLocation ? String(firstLocation) : '' };
      }
      return { ...line, [key]: value };
    }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setIsConfirming(true);
  }

  async function createReceiptDraft() {
    setIsSaving(true);
    setError('');
    try {
      const items = lines
        .filter((line, index) => Number(line.received_quantity) > 0 && Number(line.received_quantity) <= Number(order.items[index].ordered_quantity) - Number(order.items[index].received_quantity))
        .map((line) => {
          const serialNumbers = line.serial_numbers.split(/[\n,]+/).map((value) => value.trim()).filter(Boolean);
          return {
            ...line,
            warehouse_id: Number(line.warehouse_id),
            location_id: Number(line.location_id),
            received_quantity: line.received_quantity,
            product_id: Number(line.product_id),
            purchase_order_item_id: Number(line.purchase_order_item_id),
            batch_number: line.batch_number || null,
            supplier_batch_number: line.supplier_batch_number || null,
            manufacture_date: line.manufacture_date || null,
            expiry_date: line.expiry_date || null,
            warranty_until: line.warranty_until || null,
            serial_numbers: serialNumbers.length ? serialNumbers : null,
          };
        });
      const receipt = await purchasingService.createPurchaseReceipt(accessToken, id, { receipt_number: receiptNumber, items });
      setIsConfirming(false);
      navigate(`/purchase-receipts/${receipt.id}`);
    } catch (saveError) {
      setError(saveError.message);
    } finally {
      setIsSaving(false);
    }
  }

  if (isLoading) return <LoadingState />;
  if (!order) return <ErrorState description={error || 'Purchase order not found.'} />;

  const advisoryImpact = lines
    .filter((line) => Number(line.received_quantity) > 0)
    .map((line, index) => {
      const product = productsById[line.product_id];
      const item = order.items[index];
      return {
        id: line.purchase_order_item_id,
        product: product?.name ?? `Product #${line.product_id}`,
        meta: `${line.warehouse_id ? `Warehouse ${line.warehouse_id}` : 'Warehouse'} • ${line.location_id ? `Location ${line.location_id}` : 'Location'} • Remaining ${formatDecimal(Number(item.ordered_quantity) - Number(item.received_quantity))}`,
        effect: `Accepted quantity ${formatDecimal(line.received_quantity)} is prepared for receipt draft creation.`,
        warning: product?.track_serial ? 'Serial-tracked items need matching serial count before commit.' : null,
      };
    });

  return (
    <div className="space-y-6">
      <PageHeader backTo="/purchases" description="Choose warehouse and location for each received line. The backend validates remaining quantities before stock changes." kicker="Receiving" title={`Receive ${order.po_number}`} />
      {error ? <ErrorState description={error} /> : null}
      <form className="space-y-6" onSubmit={handleSubmit}>
        <Card>
          <CardHeader><h2 className="text-lg font-semibold text-warelyn-text">Receipt</h2></CardHeader>
          <CardBody className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_280px]">
            <BarcodeInput hint="Use SKU or barcode to jump to a line while receiving." label="Product / barcode search" onChange={(event) => setBarcodeSearch(event.target.value)} value={barcodeSearch} />
            <Input label="Receipt number" required value={receiptNumber} onChange={(event) => setReceiptNumber(event.target.value)} />
          </CardBody>
        </Card>
        <Card>
          <CardHeader><h2 className="text-lg font-semibold text-warelyn-text">Receipt lines</h2></CardHeader>
          <CardBody className="space-y-4">
            {lines.map((line, index) => {
              const item = order.items[index];
              const product = productsById[line.product_id];
              const remaining = Number(item.ordered_quantity) - Number(item.received_quantity);
              const matchesSearch = !barcodeSearch || `${product?.name ?? ''} ${product?.sku ?? ''} ${product?.barcode ?? ''}`.toLowerCase().includes(barcodeSearch.toLowerCase());
              const isTracked = product?.track_batch || product?.track_expiry || product?.track_serial;
              if (!matchesSearch) return null;
              return (
                <div className="grid gap-3 rounded-xl border border-warelyn-border p-4 lg:grid-cols-[1fr_1fr_1fr_1fr]" key={line.purchase_order_item_id}>
                  <div><span className="text-xs font-semibold uppercase tracking-wide text-warelyn-muted">Product</span><p className="mt-2 font-semibold text-warelyn-text">{product?.name ?? `#${line.product_id}`}</p><p className="text-xs text-warelyn-muted">SKU {product?.sku ?? '-'}</p><p className="text-sm text-warelyn-muted">Remaining {remaining.toFixed(3)}</p>{isTracked ? <p className="mt-2 text-xs font-semibold text-warelyn-primary">Tracking: {[product.track_batch ? 'batch' : null, product.track_expiry ? 'expiry' : null, product.track_serial ? 'serial' : null].filter(Boolean).join(', ')}</p> : null}</div>
                  <Input label="Receive quantity" max={remaining} min="0" step="0.001" type="number" value={line.received_quantity} onChange={(event) => updateLine(index, 'received_quantity', event.target.value)} />
                  <label className="block"><span className="mb-2 block text-sm font-medium text-warelyn-text">Warehouse</span><select className={selectClass} required value={line.warehouse_id} onChange={(event) => updateLine(index, 'warehouse_id', event.target.value)}><option value="">Select warehouse</option>{warehouses.map((warehouse) => <option key={warehouse.id} value={warehouse.id}>{warehouse.name}</option>)}</select></label>
                  <label className="block"><span className="mb-2 block text-sm font-medium text-warelyn-text">Location</span><select className={selectClass} required value={line.location_id} onChange={(event) => updateLine(index, 'location_id', event.target.value)}><option value="">Select location</option>{(locationsByWarehouse[line.warehouse_id] ?? []).map((location) => <option key={location.id} value={location.id}>{location.name} ({location.location_type})</option>)}</select></label>
                  {isTracked ? <div className="grid gap-3 lg:col-span-4 lg:grid-cols-5"><Input label="Batch number" required={product?.track_batch || product?.track_expiry} value={line.batch_number} onChange={(event) => updateLine(index, 'batch_number', event.target.value)} /><Input label="Supplier batch" value={line.supplier_batch_number} onChange={(event) => updateLine(index, 'supplier_batch_number', event.target.value)} /><Input label="Manufacture date" type="date" value={line.manufacture_date} onChange={(event) => updateLine(index, 'manufacture_date', event.target.value)} /><Input label="Expiry date" required={product?.track_expiry} type="date" value={line.expiry_date} onChange={(event) => updateLine(index, 'expiry_date', event.target.value)} /><Input label="Warranty until" type="date" value={line.warranty_until} onChange={(event) => updateLine(index, 'warranty_until', event.target.value)} />{product?.track_serial ? <label className="block lg:col-span-5"><span className="mb-2 block text-sm font-medium text-warelyn-text">Serial numbers</span><textarea className={selectClass} placeholder="One per line or comma-separated" required rows="3" value={line.serial_numbers} onChange={(event) => updateLine(index, 'serial_numbers', event.target.value)} /></label> : null}</div> : null}
                </div>
              );
            })}
          </CardBody>
        </Card>
        <StockImpactPreview items={advisoryImpact} title="Receiving outcome preview" />
        <div className="sticky-form-footer">
          <div className="workflow-helper-panel max-w-xl">
            <h3>What happens next?</h3>
            <p>This creates a receipt draft only. Stock changes later when the receipt is committed by the backend through InventoryEngine.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button onClick={() => navigate('/purchases')} type="button" variant="ghost">Cancel</Button>
            <Button disabled={isSaving} type="submit">{isSaving ? 'Creating...' : 'Create receipt draft'}</Button>
          </div>
        </div>
      </form>
      <ConfirmationModal confirmLabel="Create receipt draft" description="This creates a receiving draft only. Stock changes later when the receipt is committed by the backend." isLoading={isSaving} onCancel={() => setIsConfirming(false)} onConfirm={createReceiptDraft} open={isConfirming} title="Confirm receiving draft" variant="accent" />
    </div>
  );
}
