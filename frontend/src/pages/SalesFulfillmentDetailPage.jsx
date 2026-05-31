import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';

import { StatusBadge } from '../components/ui/Badge.jsx';
import { Button } from '../components/ui/Button.jsx';
import { Card, CardBody, CardHeader } from '../components/ui/Card.jsx';
import { ConfirmationModal } from '../components/ui/ConfirmationModal.jsx';
import { ErrorState } from '../components/ui/ErrorState.jsx';
import { Input } from '../components/ui/Input.jsx';
import { LoadingState } from '../components/ui/LoadingState.jsx';
import { RecordDetailShell } from '../components/ui/RecordDetailShell.jsx';
import { StockImpactPreview } from '../components/ui/StockImpactPreview.jsx';
import { TableShell } from '../components/ui/TableShell.jsx';
import { WorkflowProgress } from '../components/ui/WorkflowProgress.jsx';
import { formatDecimal } from '../utils/formatters.js';
import { useAuth } from '../context/AuthContext.jsx';
import * as catalogService from '../services/catalogService.js';
import * as documentService from '../services/documentService.js';
import * as salesService from '../services/salesService.js';

const canWrite = new Set(['TENANT_ADMIN', 'INVENTORY_MANAGER', 'SALES_STAFF']);
const fulfillmentSteps = [
  { key: 'DRAFT', label: 'Draft' },
  { key: 'COMMITTED', label: 'Committed' },
];

export function SalesFulfillmentDetailPage() {
  const { id } = useParams();
  const { accessToken, user } = useAuth();
  const navigate = useNavigate();
  const [fulfillment, setFulfillment] = useState(null);
  const [productsById, setProductsById] = useState({});
  const [summary, setSummary] = useState(null);
  const [idempotencyKey, setIdempotencyKey] = useState(`sales-fulfillment-${id}-${Date.now()}`);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');
  const [pendingAction, setPendingAction] = useState(null);
  const mayWrite = canWrite.has(user?.role);

  async function load() {
    setIsLoading(true);
    setError('');
    try {
      const [fulfillmentRow, productRows] = await Promise.all([
        salesService.getSalesFulfillment(accessToken, id),
        catalogService.listProducts(accessToken),
      ]);
      setFulfillment(fulfillmentRow);
      setProductsById(Object.fromEntries(productRows.map((product) => [product.id, product])));
    } catch (loadError) {
      setError(loadError.message);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [accessToken, id]);

  async function commit() {
    setIsSaving(true);
    setError('');
    try {
      const result = await salesService.commitSalesFulfillment(accessToken, id, { idempotency_key: idempotencyKey });
      setSummary(result);
      setFulfillment(result.fulfillment);
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
      setFulfillment(await salesService.cancelSalesFulfillment(accessToken, id));
      setPendingAction(null);
    } catch (cancelError) {
      setError(cancelError.message);
    } finally {
      setIsSaving(false);
    }
  }

  async function generateInvoiceFromFulfillment() {
    setIsSaving(true);
    setError('');
    try {
      const invoice = await documentService.createInvoice(accessToken, { fulfillment_id: Number(id) });
      navigate(`/invoices/${invoice.id}`);
    } catch (commitError) {
      setError(commitError.message);
    } finally {
      setIsSaving(false);
    }
  }

  if (isLoading) return <LoadingState />;
  if (!fulfillment) return <ErrorState description={error || 'Sales fulfillment not found.'} />;

  const totalQty = fulfillment.items.reduce((sum, item) => sum + Number(item.fulfilled_quantity), 0);

  return (
    <div className="space-y-6">
      {error ? <ErrorState description={error} /> : null}
      <RecordDetailShell
        actions={
          mayWrite && fulfillment.status === 'DRAFT' ? (
            <div className="flex flex-wrap gap-2">
              <Button
                disabled={isSaving}
                variant="accent"
                onClick={() =>
                  setPendingAction({
                    description:
                      'Committing converts active reservations into physical stock deduction through backend inventory workflows.',
                    label: 'Commit fulfillment',
                    run: commit,
                    variant: 'accent',
                  })
                }
              >
                Commit
              </Button>
              <Button
                disabled={isSaving}
                variant="danger"
                onClick={() =>
                  setPendingAction({
                    description: 'Cancel this fulfillment draft. Stock stays untouched because only committed fulfillments deduct inventory.',
                    label: 'Cancel fulfillment',
                    run: cancel,
                    variant: 'danger',
                  })
                }
              >
                Cancel
              </Button>
              <Button disabled={isSaving} variant="secondary" onClick={generateInvoiceFromFulfillment}>Generate invoice</Button>
            </div>
          ) : null
        }
        backTo="/sales-fulfillments"
        description={`Fulfillment for sales order #${fulfillment.sales_order_id}. This is the stock-changing step in the outbound workflow once committed.`}
        kicker="Sales fulfillment"
        meta={[
          { label: 'Sales order', value: `#${fulfillment.sales_order_id}` },
          { label: 'Created', value: fulfillment.created_at ?? 'Draft document' },
        ]}
        progress={<WorkflowProgress current={fulfillment.status} steps={fulfillmentSteps} />}
        sidePanel={
          <Card>
            <CardHeader>
              <h2 className="text-lg font-semibold text-warelyn-text">Commit controls</h2>
            </CardHeader>
            <CardBody className="space-y-4">
              <StatusBadge status={fulfillment.status}>{fulfillment.status}</StatusBadge>
              {fulfillment.status === 'DRAFT' ? (
                <Input label="Idempotency key" required value={idempotencyKey} onChange={(event) => setIdempotencyKey(event.target.value)} />
              ) : null}
              <p className="text-sm text-warelyn-muted">
                This is the point where reserved stock becomes a committed outbound movement. Review reservation IDs and quantities before confirming.
              </p>
              <Link className="text-sm font-semibold text-warelyn-primary" to={`/sales/${fulfillment.sales_order_id}`}>
                Open sales order
              </Link>
            </CardBody>
          </Card>
        }
        status={<StatusBadge status={fulfillment.status}>{fulfillment.status}</StatusBadge>}
        summary={[
          { label: 'Lines', value: fulfillment.items.length, helper: 'Fulfillment lines on this document' },
          { label: 'Fulfilled qty', value: formatDecimal(totalQty), helper: 'Quantity to deduct on commit' },
        ]}
        title={fulfillment.fulfillment_number}
      >
        <TableShell
          description="Items that will be committed against active reservations."
          isEmpty={fulfillment.items.length === 0}
          rowCount={fulfillment.items.length}
          title="Fulfillment items"
        >
          <table>
            <thead>
              <tr>
                <th>Product</th>
                <th>Warehouse</th>
                <th>Location</th>
                <th>Reservation</th>
                <th className="text-right">Quantity</th>
              </tr>
            </thead>
            <tbody>
              {fulfillment.items.map((item) => (
                <tr key={item.id}>
                  <td>
                    <div className="space-y-1">
                      <span className="font-semibold text-warelyn-text">{productsById[item.product_id]?.name ?? `Product #${item.product_id}`}</span>
                      <p className="text-xs text-warelyn-muted">SKU {productsById[item.product_id]?.sku ?? '-'}</p>
                    </div>
                  </td>
                  <td><span className="mono-cell">#{item.warehouse_id}</span></td>
                  <td><span className="mono-cell">#{item.location_id}</span></td>
                  <td><span className="mono-cell">#{item.reservation_id}</span></td>
                  <td className="number-cell">{formatDecimal(item.fulfilled_quantity)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </TableShell>

        {summary ? (
          <StockImpactPreview
            items={summary.stock_results.map((result, index) => ({
              id: index,
              product: productsById[result.stock.product_id]?.name ?? `Product #${result.stock.product_id}`,
              meta: `Reservation committed through backend workflow`,
              effect: `On hand ${formatDecimal(result.stock.quantity_on_hand)} • Reserved ${formatDecimal(result.stock.quantity_reserved)} • Available ${formatDecimal(result.stock.quantity_available)}`,
              warning: 'This reflects the backend commit result, not a frontend simulation.',
            }))}
            title="Committed stock impact"
          />
        ) : null}
      </RecordDetailShell>

      <ConfirmationModal
        confirmLabel={pendingAction?.label}
        description={pendingAction?.description}
        isLoading={isSaving}
        onCancel={() => setPendingAction(null)}
        onConfirm={() => pendingAction?.run()}
        open={Boolean(pendingAction)}
        title="Confirm fulfillment action"
        variant={pendingAction?.variant}
      />
    </div>
  );
}
