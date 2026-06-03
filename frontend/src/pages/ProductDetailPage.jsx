import { Download, Printer, QrCode } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { useParams } from 'react-router-dom';

import { ErrorState } from '../components/ui/ErrorState.jsx';
import { Button } from '../components/ui/Button.jsx';
import { Card, CardBody, CardHeader } from '../components/ui/Card.jsx';
import { LoadingState } from '../components/ui/LoadingState.jsx';
import { PageHeader } from '../components/ui/PageHeader.jsx';
import { StatusBadge } from '../components/ui/Badge.jsx';
import { formatMoney } from '../utils/formatters.js';
import { useAuth } from '../context/AuthContext.jsx';
import { useTenantSettings } from '../context/TenantSettingsContext.jsx';
import * as catalogService from '../services/catalogService.js';

function QrMatrix({ matrix }) {
  if (!matrix?.length) {
    return null;
  }
  const columns = matrix[0]?.length ?? 0;
  return (
    <div
      aria-label="QR code"
      className="grid rounded-2xl border border-warelyn-border bg-white p-3 shadow-sm"
      style={{ gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))` }}
    >
      {matrix.flatMap((row, rowIndex) =>
        row.map((cell, colIndex) => (
          <span
            key={`${rowIndex}-${colIndex}`}
            className={cell ? 'aspect-square rounded-[2px] bg-slate-900' : 'aspect-square rounded-[2px] bg-white'}
          />
        )),
      )}
    </div>
  );
}

function DetailList({ items }) {
  return (
    <dl className="grid gap-4 md:grid-cols-2">
      {items.map(([label, value]) => (
        <div key={label} className="rounded-xl border border-warelyn-border bg-slate-50 p-3">
          <dt className="text-xs font-semibold uppercase tracking-wide text-warelyn-muted">{label}</dt>
          <dd className="mt-1 text-sm font-medium text-warelyn-text">{value ?? '—'}</dd>
        </div>
      ))}
    </dl>
  );
}

export function ProductDetailPage() {
  const { id } = useParams();
  const { accessToken } = useAuth();
  const { currency } = useTenantSettings();
  const [product, setProduct] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedBatchId, setSelectedBatchId] = useState('');
  const [selectedSerialId, setSelectedSerialId] = useState('');

  useEffect(() => {
    async function load() {
      setIsLoading(true);
      setError('');
      try {
        const detail = await catalogService.getProductDetail(accessToken, id);
        setProduct(detail);
        setSelectedBatchId(detail.batches?.[0]?.id?.toString() || '');
        setSelectedSerialId(detail.batches?.length ? '' : detail.serials?.[0]?.id?.toString() || '');
      } catch (loadError) {
        setError(loadError.message);
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, [accessToken, id]);

  const selectedBatch = useMemo(
    () => product?.batches?.find((batch) => String(batch.id) === String(selectedBatchId)) ?? null,
    [product?.batches, selectedBatchId],
  );
  const selectedSerial = useMemo(
    () => product?.serials?.find((serial) => String(serial.id) === String(selectedSerialId)) ?? null,
    [product?.serials, selectedSerialId],
  );
  const activeQr = selectedBatch ?? selectedSerial ?? product;
  const availableQuantity = Number(product?.available_quantity ?? 0);

  async function downloadLabels() {
    if (!product) return;
    const blob = await catalogService.downloadProductLabelsForProductPdf(accessToken, product.id);
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `${product.sku ?? `product-${product.id}`}-labels.pdf`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  if (isLoading) {
    return <LoadingState />;
  }

  if (error) {
    return <ErrorState description={error} />;
  }

  if (!product) {
    return <ErrorState description="Product details were not found." />;
  }

  const qrTitle = selectedBatch
    ? `Batch QR · ${selectedBatch.batch_number}`
    : selectedSerial
      ? `Serial QR · ${selectedSerial.serial_number}`
      : 'Product QR';

  return (
    <div className="space-y-6">
      <PageHeader
        backTo="/catalog/products"
        kicker="Catalog"
        title={product.name}
        description={product.description || 'Detailed product view with tracking, batch, serial, and barcode context.'}
        status={<StatusBadge status={product.status ?? 'ACTIVE'}>{product.status ?? 'ACTIVE'}</StatusBadge>}
        actions={
          <div className="flex flex-wrap gap-2">
            <Button className="h-10" disabled={availableQuantity <= 0} variant="secondary" onClick={downloadLabels}>
              <Printer size={16} />
              Download labels
            </Button>
          </div>
        }
      />

      <div className="grid gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader>
            <h2 className="text-lg font-semibold text-warelyn-text">Product overview</h2>
          </CardHeader>
          <CardBody className="space-y-6">
            <DetailList
              items={[
                ['SKU', product.sku],
                ['Barcode', product.barcode ?? 'Auto-generated on save'],
                ['Category', product.category_name ?? '—'],
                ['Brand', product.brand_name ?? '—'],
                ['Unit', product.unit],
                ['Cost price', formatMoney(product.cost_price, currency)],
                ['Selling price', formatMoney(product.selling_price, currency)],
                ['Reorder level', product.reorder_level ?? '—'],
                ['Available quantity', availableQuantity.toLocaleString()],
                ['Tracking', [product.track_batch ? 'Batch' : null, product.track_expiry ? 'Expiry' : null, product.track_serial ? 'Serial' : null].filter(Boolean).join(', ') || 'Standard'],
              ]}
            />
            <div className="overflow-hidden rounded-2xl border border-warelyn-border">
              <div className="border-b border-warelyn-border bg-slate-50 px-4 py-3">
                <h3 className="text-sm font-semibold text-warelyn-text">Stock by warehouse</h3>
              </div>
              <table className="min-w-full text-sm">
                <thead className="bg-white">
                  <tr className="border-b border-warelyn-border text-left text-xs uppercase tracking-wide text-warelyn-muted">
                    <th className="px-4 py-3">Warehouse</th>
                    <th className="px-4 py-3">Location</th>
                    <th className="px-4 py-3 text-right">On hand</th>
                    <th className="px-4 py-3 text-right">Reserved</th>
                    <th className="px-4 py-3 text-right">Available</th>
                  </tr>
                </thead>
                <tbody>
                  {product.stock_rows?.length ? product.stock_rows.map((row) => (
                    <tr key={`${row.warehouse_id}-${row.location_id}`} className="border-b border-warelyn-border/70 last:border-0">
                      <td className="px-4 py-3 text-warelyn-text">{row.warehouse_name}</td>
                      <td className="px-4 py-3 text-warelyn-text">{row.location_name}</td>
                      <td className="px-4 py-3 text-right text-warelyn-text">{Number(row.quantity_on_hand ?? 0).toLocaleString()}</td>
                      <td className="px-4 py-3 text-right text-warelyn-text">{Number(row.quantity_reserved ?? 0).toLocaleString()}</td>
                      <td className="px-4 py-3 text-right font-semibold text-warelyn-text">{Number(row.quantity_available ?? 0).toLocaleString()}</td>
                    </tr>
                  )) : (
                    <tr>
                      <td className="px-4 py-6 text-center text-sm text-warelyn-muted" colSpan={5}>
                        No stock rows are available for this product yet.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-warelyn-text flex items-center gap-2">
              <QrCode size={18} className="text-warelyn-primary" />
              {qrTitle}
            </h2>
          </CardHeader>
          <CardBody className="space-y-4">
            <QrMatrix matrix={activeQr?.qr_matrix} />
            <p className="text-xs text-warelyn-muted">
              QR payload changes with the selected batch or serial so the tracking context stays printable and scannable.
            </p>
            <div className="rounded-xl border border-warelyn-border bg-slate-50 p-3 text-xs text-warelyn-muted break-words">
              {activeQr?.qr_payload ?? 'No QR payload available.'}
            </div>
          </CardBody>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-warelyn-text">Batch details</h2>
          </CardHeader>
          <CardBody className="space-y-4">
            {product.batches?.length ? (
              <>
                <label className="block">
                  <span className="mb-2 block text-sm font-medium text-warelyn-text">Select batch</span>
                  <select
                    className="block w-full rounded-lg border border-warelyn-border bg-white px-3 py-2.5 text-sm text-warelyn-text shadow-sm outline-none transition focus:border-warelyn-primary focus:ring-4 focus:ring-blue-900/10"
                    onChange={(event) => setSelectedBatchId(event.target.value)}
                    value={selectedBatchId}
                  >
                    {product.batches.map((batch) => (
                      <option key={batch.id} value={batch.id}>
                        {batch.batch_number} · {batch.expiry_date || 'No expiry'}
                      </option>
                    ))}
                  </select>
                </label>
                {selectedBatch ? (
                  <DetailList
                    items={[
                      ['Batch number', selectedBatch.batch_number],
                      ['Supplier batch', selectedBatch.supplier_batch_number ?? '—'],
                      ['Manufacture date', selectedBatch.manufacture_date ?? '—'],
                      ['Expiry date', selectedBatch.expiry_date ?? '—'],
                      ['Warranty until', selectedBatch.warranty_until ?? '—'],
                      ['Warehouse', selectedBatch.warehouse_name],
                      ['Location', selectedBatch.location_name],
                      ['On hand', Number(selectedBatch.quantity_on_hand ?? 0).toLocaleString()],
                      ['Reserved', Number(selectedBatch.quantity_reserved ?? 0).toLocaleString()],
                      ['Available', Number(selectedBatch.quantity_available ?? 0).toLocaleString()],
                      ['Status', selectedBatch.status],
                    ]}
                  />
                ) : null}
              </>
            ) : (
              <p className="text-sm text-warelyn-muted">No batch-tracked inventory exists for this product.</p>
            )}
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-warelyn-text">Serial details</h2>
          </CardHeader>
          <CardBody className="space-y-4">
            {product.serials?.length ? (
              <>
                {product.batches?.length ? null : (
                  <label className="block">
                    <span className="mb-2 block text-sm font-medium text-warelyn-text">Select serial</span>
                    <select
                      className="block w-full rounded-lg border border-warelyn-border bg-white px-3 py-2.5 text-sm text-warelyn-text shadow-sm outline-none transition focus:border-warelyn-primary focus:ring-4 focus:ring-blue-900/10"
                      onChange={(event) => setSelectedSerialId(event.target.value)}
                      value={selectedSerialId}
                    >
                      {product.serials.map((serial) => (
                        <option key={serial.id} value={serial.id}>
                          {serial.serial_number}
                        </option>
                      ))}
                    </select>
                  </label>
                )}
                <div className="max-h-[24rem] overflow-auto rounded-2xl border border-warelyn-border">
                  <table className="min-w-full text-sm">
                    <thead className="bg-slate-50">
                      <tr className="border-b border-warelyn-border text-left text-xs uppercase tracking-wide text-warelyn-muted">
                        <th className="px-4 py-3">Serial</th>
                        <th className="px-4 py-3">Batch</th>
                        <th className="px-4 py-3">Warehouse</th>
                        <th className="px-4 py-3">Location</th>
                        <th className="px-4 py-3">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {product.serials.map((serial) => (
                        <tr
                          key={serial.id}
                          className={`border-b border-warelyn-border/70 last:border-0 ${String(serial.id) === String(selectedSerialId) ? 'bg-blue-50/50' : ''}`}
                          onClick={() => setSelectedSerialId(String(serial.id))}
                        >
                          <td className="px-4 py-3 font-medium text-warelyn-text">{serial.serial_number}</td>
                          <td className="px-4 py-3 text-warelyn-text">{serial.batch_number ?? '—'}</td>
                          <td className="px-4 py-3 text-warelyn-text">{serial.warehouse_name}</td>
                          <td className="px-4 py-3 text-warelyn-text">{serial.location_name}</td>
                          <td className="px-4 py-3 text-warelyn-text">{serial.status}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            ) : (
              <p className="text-sm text-warelyn-muted">No serial-tracked inventory exists for this product.</p>
            )}
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
