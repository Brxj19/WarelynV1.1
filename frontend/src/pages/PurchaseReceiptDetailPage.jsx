import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import { StatusBadge } from '../components/ui/Badge.jsx';
import { Button } from '../components/ui/Button.jsx';
import { Card, CardBody, CardHeader } from '../components/ui/Card.jsx';
import { ConfirmationModal } from '../components/ui/ConfirmationModal.jsx';
import { ErrorState } from '../components/ui/ErrorState.jsx';
import { Input } from '../components/ui/Input.jsx';
import { LoadingState } from '../components/ui/LoadingState.jsx';
import { PageHeader } from '../components/ui/PageHeader.jsx';
import { StockImpactPreview } from '../components/ui/StockImpactPreview.jsx';
import { formatDecimal, formatMoney } from '../utils/formatters.js';
import { useAuth } from '../context/AuthContext.jsx';
import { useTenantSettings } from '../context/TenantSettingsContext.jsx';
import * as purchasingService from '../services/purchasingService.js';

const canWrite = new Set(['TENANT_ADMIN', 'INVENTORY_MANAGER', 'PURCHASE_STAFF']);

export function PurchaseReceiptDetailPage() {
  const { id } = useParams();
  const { accessToken, user } = useAuth();
  const { currency } = useTenantSettings();
  const [receipt, setReceipt] = useState(null);
  const [summary, setSummary] = useState(null);
  const [idempotencyKey, setIdempotencyKey] = useState(`receipt-${id}-${Date.now()}`);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');
  const [pendingAction, setPendingAction] = useState(null);
  const mayWrite = canWrite.has(user?.role);

  async function load() {
    setIsLoading(true);
    setError('');
    try {
      setReceipt(await purchasingService.getPurchaseReceipt(accessToken, id));
    } catch (loadError) {
      setError(loadError.message);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => { load(); }, [accessToken, id]);

  async function commit() {
    setIsSaving(true);
    setError('');
    try {
      const result = await purchasingService.commitPurchaseReceipt(accessToken, id, { idempotency_key: idempotencyKey });
      setSummary(result);
      setReceipt(result.receipt);
      setPendingAction(null);
    } catch (commitError) {
      setError(commitError.message);
    } finally {
      setIsSaving(false);
    }
  }

  async function cancel() {
    setIsSaving(true);
    setError('');
    try {
      setReceipt(await purchasingService.cancelPurchaseReceipt(accessToken, id));
      setPendingAction(null);
    } catch (cancelError) {
      setError(cancelError.message);
    } finally {
      setIsSaving(false);
    }
  }

  if (isLoading) return <LoadingState />;
  if (!receipt) return <ErrorState description={error || 'Purchase receipt not found.'} />;

  return (
    <div className="space-y-6">
      <PageHeader
        backTo="/purchase-receipts"
        description={
          <>
            Receipt for{' '}
            <Link className="font-semibold text-warelyn-primary" to={`/purchases/${receipt.purchase_order_id}`}>
              purchase order #{receipt.purchase_order_id}
            </Link>
            . Stock remains backend-controlled and only changes when this draft is committed.
          </>
        }
        kicker="Purchase receipt"
        actions={
          receipt.grn_number ? <span className="inline-flex items-center rounded-lg bg-green-50 px-3 py-1.5 text-sm font-semibold text-green-700">GRN: {receipt.grn_number}</span> : null
        }
        status={<StatusBadge status={receipt.status}>{receipt.status}</StatusBadge>}
        title={receipt.receipt_number}
      />
      {error ? <ErrorState description={error} /> : null}
      <Card>
        <CardHeader><h2 className="text-lg font-semibold text-warelyn-text">Receipt lines</h2></CardHeader>
        <CardBody>
          <div className="overflow-hidden rounded-xl border border-warelyn-border">
            <table className="min-w-full divide-y divide-warelyn-border text-sm">
              <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-warelyn-muted"><tr><th className="px-4 py-3">Product</th><th className="px-4 py-3">Warehouse</th><th className="px-4 py-3">Location</th><th className="px-4 py-3">Quantity</th><th className="px-4 py-3">Unit Cost</th><th className="px-4 py-3">Tracking</th></tr></thead>
              <tbody className="divide-y divide-warelyn-border bg-white">{receipt.items.map((item) => <tr key={item.id}><td className="px-4 py-3">#{item.product_id}</td><td className="px-4 py-3">#{item.warehouse_id}</td><td className="px-4 py-3">#{item.location_id}</td><td className="px-4 py-3 font-semibold text-warelyn-text">{formatDecimal(item.received_quantity)}</td><td className="px-4 py-3">{formatMoney(item.unit_cost, currency)}</td><td className="px-4 py-3 text-xs text-warelyn-muted">{item.batch_number ? <span className="block font-semibold text-warelyn-text">Batch {item.batch_number}</span> : null}{item.expiry_date ? <span className="block">Expires {item.expiry_date}</span> : null}{item.warranty_until ? <span className="block">Warranty {item.warranty_until}</span> : null}{item.serial_numbers?.length ? <span className="block">Serials {item.serial_numbers.join(', ')}</span> : null}{!item.batch_number && !item.serial_numbers?.length ? 'Untracked' : null}</td></tr>)}</tbody>
            </table>
          </div>
        </CardBody>
      </Card>
      {mayWrite && receipt.status === 'DRAFT' ? (
        <Card>
          <CardHeader><h2 className="text-lg font-semibold text-warelyn-text">Commit receipt</h2></CardHeader>
          <CardBody className="space-y-4">
            <p className="text-sm text-warelyn-muted">Committing this receipt posts stock through InventoryEngine and writes purchase-referenced ledger entries.</p>
            <Input label="Idempotency key" required value={idempotencyKey} onChange={(event) => setIdempotencyKey(event.target.value)} />
            <StockImpactPreview items={receipt.items.map((item) => ({ effect: 'Expected effect: on-hand and available stock increase after backend commit.', id: item.id, meta: `Warehouse #${item.warehouse_id} / Location #${item.location_id}; quantity ${item.received_quantity}`, product: `Product #${item.product_id}` }))} />
            <div className="flex flex-wrap gap-2"><Button disabled={isSaving} variant="accent" onClick={() => setPendingAction('commit')}>{isSaving ? 'Committing...' : 'Commit receipt'}</Button><Button disabled={isSaving} variant="danger" onClick={() => setPendingAction('cancel')}>Cancel receipt</Button></div>
          </CardBody>
        </Card>
      ) : null}
      {summary ? (
        <Card>
          <CardHeader><h2 className="text-lg font-semibold text-warelyn-text">Stock impact after commit</h2></CardHeader>
          <CardBody><div className="grid gap-3 md:grid-cols-2">{summary.stock_results.map((result, index) => <div className="rounded-xl border border-warelyn-border p-4" key={index}><p className="font-semibold text-warelyn-text">Product #{result.stock.product_id}</p><p className="text-sm text-warelyn-muted">On hand: {formatDecimal(result.stock.quantity_on_hand)}</p><p className="text-sm text-warelyn-muted">Available: {formatDecimal(result.stock.quantity_available)}</p></div>)}</div></CardBody>
        </Card>
      ) : null}
      <ConfirmationModal confirmLabel={pendingAction === 'cancel' ? 'Cancel receipt' : 'Commit receipt'} description={pendingAction === 'cancel' ? 'Cancel this receipt draft. No stock will be posted.' : 'Commit this receipt through the backend InventoryEngine and write purchase-referenced stock ledger entries.'} isLoading={isSaving} onCancel={() => setPendingAction(null)} onConfirm={pendingAction === 'cancel' ? cancel : commit} open={Boolean(pendingAction)} title={pendingAction === 'cancel' ? 'Confirm receipt cancellation' : 'Confirm receipt commit'} variant={pendingAction === 'cancel' ? 'danger' : 'accent'} />
    </div>
  );
}
