import { useEffect, useState } from 'react';
import { BackButton } from '../components/ui/BackButton.jsx';
import { Link, useNavigate, useParams } from 'react-router-dom';

import { RecordDetailShell } from '../components/ui/RecordDetailShell.jsx';
import { StatusBadge } from '../components/ui/Badge.jsx';
import { Button } from '../components/ui/Button.jsx';
import { Card, CardBody, CardHeader } from '../components/ui/Card.jsx';
import { ConfirmationModal } from '../components/ui/ConfirmationModal.jsx';
import { EmptyState } from '../components/ui/EmptyState.jsx';
import { ErrorState } from '../components/ui/ErrorState.jsx';
import { LoadingState } from '../components/ui/LoadingState.jsx';
import { TableShell } from '../components/ui/TableShell.jsx';
import { WorkflowProgress } from '../components/ui/WorkflowProgress.jsx';
import { formatDate, formatDecimal, formatMoney } from '../utils/formatters.js';
import { useAuth } from '../context/AuthContext.jsx';
import { useTenantSettings } from '../context/TenantSettingsContext.jsx';
import * as purchasingService from '../services/purchasingService.js';
import * as documentService from '../services/documentService.js';

const canWrite = new Set(['TENANT_ADMIN', 'INVENTORY_MANAGER', 'PURCHASE_STAFF']);
const receivableStatuses = new Set(['SUBMITTED', 'PARTIALLY_RECEIVED']);
const statusTone = { DRAFT: 'neutral', SUBMITTED: 'primary', PARTIALLY_RECEIVED: 'warning', RECEIVED: 'success', CANCELLED: 'danger', CLOSED: 'neutral' };
const purchaseSteps = [{ key: 'DRAFT', label: 'Draft' }, { key: 'SUBMITTED', label: 'Submitted' }, { key: 'PARTIALLY_RECEIVED', label: 'Receiving' }, { key: 'RECEIVED', label: 'Received / Closed', matches: ['RECEIVED', 'CLOSED'] }];

export function PurchaseOrderDetailPage() {
  const { id } = useParams();
  const { accessToken, user } = useAuth();
  const { currency } = useTenantSettings();
  const navigate = useNavigate();
  const [order, setOrder] = useState(null);
  const [receipts, setReceipts] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');
  const [pendingAction, setPendingAction] = useState(null);
  const mayWrite = canWrite.has(user?.role);

  async function load() {
    setIsLoading(true);
    setError('');
    try {
      const [orderRow, receiptRows] = await Promise.all([purchasingService.getPurchaseOrder(accessToken, id), purchasingService.listPurchaseReceipts(accessToken, id)]);
      setOrder(orderRow);
      setReceipts(receiptRows);
    } catch (loadError) {
      setError(loadError.message);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => { load(); }, [accessToken, id]);

  async function runAction(action = pendingAction?.action) {
    if (!action) return;
    setIsSaving(true);
    setError('');
    try {
      await action(accessToken, id);
      setPendingAction(null);
      await load();
    } catch (actionError) {
      setError(actionError.message);
    } finally {
      setIsSaving(false);
    }
  }

  async function generateBillFromOrder() {
    setIsSaving(true);
    setError('');
    try {
      const bill = await documentService.createBill(accessToken, { purchase_order_id: Number(id) });
      navigate(`/bills/${bill.id}`);
    } catch (actionError) {
      setError(actionError.message);
    } finally {
      setIsSaving(false);
    }
  }

  if (isLoading) return <LoadingState />;
  if (!order) return <ErrorState description={error || 'Purchase order not found.'} />;

  const orderedQty = order.items.reduce((sum, item) => sum + Number(item.ordered_quantity), 0);
  const receivedQty = order.items.reduce((sum, item) => sum + Number(item.received_quantity), 0);
  const pendingQty = orderedQty - receivedQty;

  return (
    <div className="space-y-6">
      <BackButton to="/purchases" />
      {error ? <ErrorState description={error} /> : null}
      <RecordDetailShell
        actions={
          <div className="flex flex-wrap gap-2">
            {mayWrite && order.status === 'DRAFT' ? <Button disabled={isSaving} onClick={() => setPendingAction({ action: purchasingService.submitPurchaseOrder, description: 'Submit this purchase order for receiving. Stock will not change until a receipt is committed.', label: 'Submit order', variant: 'primary' })}>Submit</Button> : null}
            {mayWrite && ['DRAFT', 'SUBMITTED'].includes(order.status) ? <Button disabled={isSaving} variant="danger" onClick={() => setPendingAction({ action: purchasingService.cancelPurchaseOrder, description: 'Cancel this purchase order. Existing committed receipts are not reversed by this action.', label: 'Cancel order', variant: 'danger' })}>Cancel</Button> : null}
            {mayWrite && ['SUBMITTED', 'PARTIALLY_RECEIVED'].includes(order.status) ? <Button disabled={isSaving} variant="secondary" onClick={() => setPendingAction({ action: purchasingService.closePurchaseOrder, description: 'Close this purchase order to stop further receiving against it.', label: 'Close order', variant: 'secondary' })}>Close</Button> : null}
            {mayWrite && receivableStatuses.has(order.status) ? <Link to={`/purchases/${order.id}/receive`}><Button variant="accent">Receive</Button></Link> : null}
            {mayWrite ? <Button disabled={isSaving} variant="secondary" onClick={generateBillFromOrder}>Generate bill</Button> : null}
          </div>
        }
        backTo="/purchases"
        description={`Order date ${formatDate(order.order_date)}. Stock changes only through committed purchase receipts.`}
        kicker="Purchase order"
        meta={[
          { label: 'Vendor', value: order.vendor_id ? `Vendor #${order.vendor_id}` : '-' },
          { label: 'Expected', value: order.expected_date ? formatDate(order.expected_date) : 'Not set' },
          { label: 'Created', value: order.created_at ? formatDate(order.created_at) : 'Draft record' },
        ]}
        progress={<WorkflowProgress current={order.status} steps={purchaseSteps} />}
        sidePanel={
          <Card>
            <CardHeader><h2 className="text-lg font-semibold text-warelyn-text">Actions</h2></CardHeader>
            <CardBody className="space-y-3">
              <p className="text-sm text-warelyn-muted">Use document actions to advance the purchase workflow. Receiving stays separate until stock is committed through a receipt.</p>
              <div className="space-y-2">
                <StatusBadge status={order.status}>{order.status}</StatusBadge>
                <p className="text-xs text-warelyn-muted">Committed receipts remain immutable reference points for stock ledger history.</p>
              </div>
            </CardBody>
          </Card>
        }
        status={<StatusBadge status={order.status}>{order.status}</StatusBadge>}
        summary={[
          { label: 'Total lines', value: order.items.length, helper: 'Document line count' },
          { label: 'Ordered qty', value: formatDecimal(orderedQty), helper: 'Requested from vendor' },
          { label: 'Received qty', value: formatDecimal(receivedQty), helper: 'Committed + draft receipts' },
          { label: 'Pending qty', value: formatDecimal(pendingQty), helper: 'Still available to receive' },
        ]}
        title={order.po_number}
      >
        <TableShell description="Ordered versus received progress by line." isEmpty={order.items.length === 0} rowCount={order.items.length} title="Line items">
          <table>
            <thead>
              <tr>
                <th>Product</th>
                <th className="text-right">Ordered</th>
                <th className="text-right">Received</th>
                <th className="text-right">Pending</th>
                <th className="text-right">Unit cost</th>
              </tr>
            </thead>
            <tbody>
              {order.items.map((item) => {
                const remaining = Number(item.ordered_quantity) - Number(item.received_quantity);
                return (
                  <tr key={item.id}>
                    <td><span className="mono-cell">Product #{item.product_id}</span></td>
                    <td className="number-cell">{formatDecimal(item.ordered_quantity)}</td>
                    <td className="number-cell">{formatDecimal(item.received_quantity)}</td>
                    <td className="number-cell">{formatDecimal(remaining)}</td>
                    <td className="number-cell">{formatMoney(item.unit_cost, currency)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </TableShell>

        <Card>
          <CardHeader><h2 className="text-lg font-semibold text-warelyn-text">Receipts</h2></CardHeader>
          <CardBody>
            {receipts.length === 0 ? <EmptyState title="No receipts yet" description="Create a receipt when goods arrive at the warehouse." /> : (
              <div className="grid gap-3 md:grid-cols-2">
                {receipts.map((receipt) => (
                  <Link className="rounded-xl border border-warelyn-border p-4 transition hover:border-warelyn-primary" key={receipt.id} to={`/purchase-receipts/${receipt.id}`}>
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-warelyn-text">{receipt.receipt_number}</span>
                      <StatusBadge status={receipt.status}>{receipt.status}</StatusBadge>
                    </div>
                    <p className="mt-2 text-sm text-warelyn-muted">{receipt.items.length} line(s)</p>
                  </Link>
                ))}
              </div>
            )}
          </CardBody>
        </Card>
      </RecordDetailShell>
      <ConfirmationModal confirmLabel={pendingAction?.label} description={pendingAction?.description} isLoading={isSaving} onCancel={() => setPendingAction(null)} onConfirm={() => runAction()} open={Boolean(pendingAction)} title="Confirm purchase workflow action" variant={pendingAction?.variant} />
    </div>
  );
}
