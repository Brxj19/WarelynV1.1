import { Printer, QrCode } from 'lucide-react';
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
      className="grid rounded-xl border border-warelyn-border bg-white p-3 shadow-sm"
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

function CompactField({ label, value }) {
  return (
    <div className="grid grid-cols-[92px_minmax(0,1fr)] gap-2">
      <dt className="font-semibold text-warelyn-muted">{label}</dt>
      <dd className="break-words text-warelyn-text">{value ?? '—'}</dd>
    </div>
  );
}

function BarcodeSvg({ value }) {
  const normalized = String(value ?? '').toUpperCase().replace(/[^0-9A-Z\-\.\ \$\/\+\%]/g, '');
  if (!normalized) {
    return null;
  }
  const patterns = {
    0: 'nnnwwnwnn',
    1: 'wnnwnnnnw',
    2: 'nnwwnnnnw',
    3: 'wnwwnnnnn',
    4: 'nnnwwnnnw',
    5: 'wnnwwnnnn',
    6: 'nnwwwnnnn',
    7: 'nnnwnnwnw',
    8: 'wnnwnnwnn',
    9: 'nnwwnnwnn',
    A: 'wnnnnwnnw',
    B: 'nnwnnwnnw',
    C: 'wnwnnwnnn',
    D: 'nnnnwwnnw',
    E: 'wnnnwwnnn',
    F: 'nnwnwwnnn',
    G: 'nnnnnwwnw',
    H: 'wnnnnwwnn',
    I: 'nnwnnwwnn',
    J: 'nnnnwwwnn',
    K: 'wnnnnnnww',
    L: 'nnwnnnnww',
    M: 'wnwnnnnwn',
    N: 'nnnnwnnww',
    O: 'wnnnwnnwn',
    P: 'nnwnwnnwn',
    Q: 'nnnnnnwww',
    R: 'wnnnnnwwn',
    S: 'nnwnnnwwn',
    T: 'nnnnwnwwn',
    U: 'wwnnnnnnw',
    V: 'nwwnnnnnw',
    W: 'wwwnnnnnn',
    X: 'nwnnwnnnw',
    Y: 'wwnnwnnnn',
    Z: 'nwwnwnnnn',
    '-': 'nwnnnnwnw',
    '.': 'wwnnnnwnn',
    ' ': 'nwwnnnwnn',
    '$': 'nwnwnwnnn',
    '/': 'nwnwnnnwn',
    '+': 'nwnnnwnwn',
    '%': 'nnnwnwnwn',
    '*': 'nwnnwnwnn',
  };

  const encoded = `*${normalized}*`;
  let x = 6;
  const bars = [];
  for (const char of encoded) {
    const pattern = patterns[char];
    if (!pattern) continue;
    pattern.split('').forEach((symbol, index) => {
      const width = symbol === 'w' ? 5 : 2;
      if (index % 2 === 0) {
        bars.push(<rect key={`${char}-${index}-${x}`} x={x} y="0" width={width} height="36" fill="#111827" rx="0.5" />);
      }
      x += width;
    });
    x += 2;
  }
  const width = x + 8;

  return (
    <svg className="w-full max-w-[240px]" viewBox={`0 0 ${width} 48`} role="img" aria-label={`Barcode for ${value}`}>
      <rect width="100%" height="100%" fill="white" />
      {bars}
      <text x={width / 2} y="46" textAnchor="middle" fontFamily="monospace" fontSize="9" fill="#111827">
        {value}
      </text>
    </svg>
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
  const qrSummary = useMemo(
    () => [
      ['ID', activeQr?.id],
      ['Type', activeQr?.type ?? 'product'],
      ['Name', activeQr?.name ?? product?.name],
      ['SKU', activeQr?.sku ?? product?.sku],
      ['Barcode', activeQr?.barcode ?? product?.barcode ?? '—'],
      ['Tracked', [product?.track_batch ? 'Batch' : null, product?.track_expiry ? 'Expiry' : null, product?.track_serial ? 'Serial' : null].filter(Boolean).join(', ') || 'Standard'],
    ],
    [activeQr, product],
  );

  async function downloadLabels() {
    if (!product) return;
    const blob = await catalogService.downloadProductLabelsForProductPdf(accessToken, product.id, {
      batchId: selectedBatchId ? Number(selectedBatchId) : undefined,
    });
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
  const barcodeValue = activeQr?.barcode ?? product.barcode ?? '—';

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
            <div className="rounded-2xl border border-warelyn-border bg-white p-3">
              <p className="text-[11px] font-semibold uppercase tracking-wide text-warelyn-muted">Barcode</p>
              <div className="mt-1 text-[10px] font-medium text-warelyn-text">{barcodeValue}</div>
              <div className="mt-2">
                <BarcodeSvg value={barcodeValue} />
              </div>
            </div>
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
              <QrCode size={16} className="text-warelyn-primary" />
              {qrTitle}
            </h2>
          </CardHeader>
          <CardBody className="space-y-4">
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-[148px_minmax(0,1fr)] sm:items-start">
              <div className="rounded-2xl border border-warelyn-border bg-white p-1.5 shadow-sm">
                <QrMatrix matrix={activeQr?.qr_matrix} />
              </div>
              <div className="space-y-2">
                <p className="text-[10px] text-warelyn-muted">
                  QR updates with the selected batch or serial.
                </p>
                <div className="rounded-xl border border-warelyn-border bg-slate-50 px-2 py-1.5 text-[10px] text-warelyn-muted">
                  Compact tracking view for the selected item.
                </div>
              </div>
            </div>

            <div className="grid gap-2 rounded-xl border border-warelyn-border bg-white p-2.5 text-[11px] leading-5">
              <p className="text-[11px] font-semibold uppercase tracking-wide text-warelyn-muted">QR data</p>
              <dl className="grid gap-1.5 md:grid-cols-2 md:gap-x-4">
                {qrSummary.map(([label, value]) => (
                  <CompactField key={label} label={label} value={value} />
                ))}
              </dl>
              {selectedBatch ? (
                <div className="rounded-lg bg-slate-50 p-2">
                  <p className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-warelyn-muted">Batch</p>
                  <dl className="grid gap-1.5">
                    <CompactField label="Batch #" value={selectedBatch.batch_number} />
                    <CompactField label="Expiry" value={selectedBatch.expiry_date ?? '—'} />
                    <CompactField label="Status" value={selectedBatch.status} />
                  </dl>
                </div>
              ) : null}
              {selectedSerial ? (
                <div className="rounded-lg bg-slate-50 p-2">
                  <p className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-warelyn-muted">Serial</p>
                  <dl className="grid gap-1.5">
                    <CompactField label="Serial #" value={selectedSerial.serial_number} />
                    <CompactField label="Batch #" value={selectedSerial.batch_number ?? '—'} />
                    <CompactField label="Status" value={selectedSerial.status} />
                  </dl>
                </div>
              ) : null}
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
