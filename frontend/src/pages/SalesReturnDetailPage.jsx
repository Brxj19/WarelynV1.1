import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import { StatusBadge } from '../components/ui/Badge.jsx';
import { Button } from '../components/ui/Button.jsx';
import { Card, CardBody, CardHeader } from '../components/ui/Card.jsx';
import { ConfirmationModal } from '../components/ui/ConfirmationModal.jsx';
import { EmptyState } from '../components/ui/EmptyState.jsx';
import { ErrorState } from '../components/ui/ErrorState.jsx';
import { LoadingState } from '../components/ui/LoadingState.jsx';
import { RecordDetailShell } from '../components/ui/RecordDetailShell.jsx';
import { TableShell } from '../components/ui/TableShell.jsx';
import { WorkflowProgress } from '../components/ui/WorkflowProgress.jsx';
import { formatDecimal } from '../utils/formatters.js';
import { useAuth } from '../context/AuthContext.jsx';
import * as catalogService from '../services/catalogService.js';
import * as returnsService from '../services/returnsService.js';

const canWrite = new Set(['TENANT_ADMIN', 'INVENTORY_MANAGER', 'SALES_STAFF']);
const canQC = new Set(['TENANT_ADMIN', 'INVENTORY_MANAGER']);
const returnSteps = [
  { key: 'DRAFT', label: 'Draft' },
  { key: 'SUBMITTED', label: 'Submitted' },
  { key: 'INSPECTION_PENDING', label: 'Inspection' },
  { key: 'PROCESSED', label: 'Processed' },
];
const qcLabels = {
  ACCEPTED_BLOCKED: 'Blocked',
  ACCEPTED_RESTOCK: 'Restock',
  DAMAGED: 'Damaged',
  PENDING: 'Pending',
  REJECTED: 'Rejected',
  SCRAPPED: 'Scrapped',
};

export function SalesReturnDetailPage() {
  const { id } = useParams();
  const { accessToken, user } = useAuth();
  const [salesReturn, setSalesReturn] = useState(null);
  const [productsById, setProductsById] = useState({});
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');
  const [pendingAction, setPendingAction] = useState(null);

  async function load() {
    setIsLoading(true);
    setError('');
    try {
      const [row, products] = await Promise.all([
        returnsService.getSalesReturn(accessToken, id),
        catalogService.listProducts(accessToken),
      ]);
      setSalesReturn(row);
      setProductsById(Object.fromEntries(products.map((product) => [product.id, product])));
    } catch (loadError) {
      setError(loadError.message);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [accessToken, id]);

  async function run(action) {
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
  if (!salesReturn) return <ErrorState description={error || 'Sales return not found.'} />;

  const returnedQty = salesReturn.items.reduce((sum, item) => sum + Number(item.returned_quantity), 0);
  const acceptedQty = salesReturn.items.reduce((sum, item) => sum + Number(item.accepted_quantity), 0);
  const rejectedQty = salesReturn.items.reduce((sum, item) => sum + Number(item.rejected_quantity), 0);
  const blockedQty = salesReturn.blocked_stock.reduce((sum, item) => sum + Number(item.quantity), 0);

  return (
    <div className="space-y-6">
      {error ? <ErrorState description={error} /> : null}
      <RecordDetailShell
        actions={
          <div className="flex flex-wrap gap-2">
            {canWrite.has(user?.role) && salesReturn.status === 'DRAFT' ? (
              <Link to={`/returns/${salesReturn.id}/edit`}>
                <Button variant="secondary">Edit</Button>
              </Link>
            ) : null}
            {canWrite.has(user?.role) && salesReturn.status === 'DRAFT' ? (
              <Button
                disabled={isSaving}
                onClick={() =>
                  setPendingAction({
                    label: 'Submit return',
                    description: 'Submit this return for QC inspection.',
                    variant: 'primary',
                    action: returnsService.submitSalesReturn,
                  })}
              >
                Submit
              </Button>
            ) : null}
            {canWrite.has(user?.role) && ['DRAFT', 'SUBMITTED', 'INSPECTION_PENDING'].includes(salesReturn.status) ? (
              <Button
                disabled={isSaving}
                variant="danger"
                onClick={() =>
                  setPendingAction({
                    label: 'Cancel return',
                    description: 'Cancel this return. QC processing will no longer be allowed.',
                    variant: 'danger',
                    action: returnsService.cancelSalesReturn,
                  })}
              >
                Cancel
              </Button>
            ) : null}
            {canQC.has(user?.role) && ['SUBMITTED', 'INSPECTION_PENDING'].includes(salesReturn.status) ? (
              <Link to={`/returns/${salesReturn.id}/inspect`}>
                <Button variant="accent">Inspect / process</Button>
              </Link>
            ) : null}
          </div>
        }
        backTo="/returns"
        description={`Return for sales order #${salesReturn.sales_order_id}. QC outcomes decide whether quantities restock, stay blocked, or remain rejected.`}
        kicker="Sales return"
        meta={[
          { label: 'Sales order', value: `#${salesReturn.sales_order_id}` },
          { label: 'Reason', value: salesReturn.reason || 'Not specified' },
          { label: 'Created', value: salesReturn.created_at ?? 'Return document' },
        ]}
        progress={<WorkflowProgress current={salesReturn.status} steps={returnSteps} />}
        sidePanel={
          <Card>
            <CardHeader>
              <h2 className="text-lg font-semibold text-warelyn-text">QC workflow</h2>
            </CardHeader>
            <CardBody className="space-y-3">
              <StatusBadge status={salesReturn.status}>{salesReturn.status}</StatusBadge>
              <p className="text-sm text-warelyn-muted">
                Submitted returns move into inspection. Only processing applies the final backend stock outcome for accepted, blocked, damaged, or scrapped quantities.
              </p>
            </CardBody>
          </Card>
        }
        status={<StatusBadge status={salesReturn.status}>{salesReturn.status}</StatusBadge>}
        summary={[
          { label: 'Returned qty', value: formatDecimal(returnedQty), helper: 'Quantity requested by customer' },
          { label: 'Accepted qty', value: formatDecimal(acceptedQty), helper: 'Restock or blocked decisions' },
          { label: 'Rejected qty', value: formatDecimal(rejectedQty), helper: 'No stock change' },
          { label: 'Blocked qty', value: formatDecimal(blockedQty), helper: 'Non-sellable return stock' },
        ]}
        title={salesReturn.return_number}
      >
        <TableShell
          description="Returned lines with QC progress and tracking references."
          isEmpty={salesReturn.items.length === 0}
          rowCount={salesReturn.items.length}
          title="Return items"
        >
          <table>
            <thead>
              <tr>
                <th>Product</th>
                <th className="text-right">Returned</th>
                <th className="text-right">Accepted</th>
                <th className="text-right">Rejected</th>
                <th>QC outcome</th>
                <th>Tracking</th>
              </tr>
            </thead>
            <tbody>
              {salesReturn.items.map((item) => (
                <tr key={item.id}>
                  <td>
                    <div className="space-y-1">
                      <span className="font-semibold text-warelyn-text">{productsById[item.product_id]?.name ?? `Product #${item.product_id}`}</span>
                      <p className="text-xs text-warelyn-muted">SKU {productsById[item.product_id]?.sku ?? '-'}</p>
                    </div>
                  </td>
                  <td className="number-cell">{formatDecimal(item.returned_quantity)}</td>
                  <td className="number-cell">{formatDecimal(item.accepted_quantity)}</td>
                  <td className="number-cell">{formatDecimal(item.rejected_quantity)}</td>
                  <td>
                    <StatusBadge status={item.qc_status}>{qcLabels[item.qc_status] ?? item.qc_status}</StatusBadge>
                  </td>
                  <td>
                    <span className="mono-cell">Batch {item.batch_id ?? '-'} / Serial {item.serial_id ?? '-'}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </TableShell>

        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-warelyn-text">Blocked stock outcome</h2>
          </CardHeader>
          <CardBody>
            {salesReturn.blocked_stock.length === 0 ? (
              <EmptyState title="No blocked stock" description="Rejected returns and sellable restocks do not create blocked stock records." />
            ) : (
              <div className="grid gap-3 md:grid-cols-2">
                {salesReturn.blocked_stock.map((row) => (
                  <div className="rounded-xl border border-warelyn-border p-4" key={row.id}>
                    <div className="flex items-center justify-between gap-3">
                      <span className="font-semibold text-warelyn-text">{productsById[row.product_id]?.name ?? `Product #${row.product_id}`}</span>
                      <StatusBadge status={row.status}>{row.status}</StatusBadge>
                    </div>
                    <p className="mt-2 text-sm text-warelyn-muted">
                      Quantity {formatDecimal(row.quantity)}. Non-sellable and excluded from available warehouse stock.
                    </p>
                  </div>
                ))}
              </div>
            )}
          </CardBody>
        </Card>
      </RecordDetailShell>
      <ConfirmationModal
        open={Boolean(pendingAction)}
        title="Confirm return action"
        description={pendingAction?.description}
        confirmLabel={pendingAction?.label}
        variant={pendingAction?.variant ?? 'primary'}
        isLoading={isSaving}
        onCancel={() => setPendingAction(null)}
        onConfirm={async () => {
          const action = pendingAction?.action;
          setPendingAction(null);
          if (action) await run(action);
        }}
      />
    </div>
  );
}
