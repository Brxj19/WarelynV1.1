import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import { StatusBadge } from '../components/ui/Badge.jsx';
import { Button } from '../components/ui/Button.jsx';
import { Card, CardBody, CardHeader } from '../components/ui/Card.jsx';
import { ConfirmationModal } from '../components/ui/ConfirmationModal.jsx';
import { ErrorState } from '../components/ui/ErrorState.jsx';
import { LoadingState } from '../components/ui/LoadingState.jsx';
import { RecordDetailShell } from '../components/ui/RecordDetailShell.jsx';
import { TableShell } from '../components/ui/TableShell.jsx';
import { WorkflowProgress } from '../components/ui/WorkflowProgress.jsx';
import { formatDecimal } from '../utils/formatters.js';
import { useAuth } from '../context/AuthContext.jsx';
import * as catalogService from '../services/catalogService.js';
import * as fulfillmentService from '../services/fulfillmentService.js';

const canWrite = new Set(['TENANT_ADMIN', 'INVENTORY_MANAGER', 'SALES_STAFF']);
const packageSteps = [
  { key: 'DRAFT', label: 'Draft' },
  { key: 'PACKED', label: 'Packed' },
];

export function PackageDetailPage() {
  const { id } = useParams();
  const { accessToken, user } = useAuth();
  const [pkg, setPackage] = useState(null);
  const [productsById, setProductsById] = useState({});
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');
  const [pendingAction, setPendingAction] = useState(null);
  const mayWrite = canWrite.has(user?.role);

  async function load() {
    setIsLoading(true);
    setError('');
    try {
      const [packageRow, productRows] = await Promise.all([
        fulfillmentService.getPackage(accessToken, id),
        catalogService.listProducts(accessToken),
      ]);
      setPackage(packageRow);
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

  async function run(action) {
    setIsSaving(true);
    setError('');
    try {
      await action();
      setPendingAction(null);
      await load();
    } catch (actionError) {
      setError(actionError.message);
    } finally {
      setIsSaving(false);
    }
  }

  if (isLoading) return <LoadingState />;
  if (!pkg) return <ErrorState description={error || 'Package not found.'} />;

  const packedQty = pkg.items.reduce((sum, item) => sum + Number(item.quantity), 0);

  return (
    <div className="space-y-6">
      {error ? <ErrorState description={error} /> : null}
      <RecordDetailShell
        actions={
          <div className="flex flex-wrap gap-2">
            {mayWrite && pkg.status === 'DRAFT' ? (
              <Button
                disabled={isSaving}
                onClick={() =>
                  setPendingAction({
                    description: 'Pack this package record to lock it as an operational shipping unit.',
                    label: 'Pack package',
                    run: () => run(() => fulfillmentService.packPackage(accessToken, id)),
                    variant: 'accent',
                  })
                }
              >
                Pack
              </Button>
            ) : null}
            {mayWrite && pkg.status === 'DRAFT' ? (
              <Button
                disabled={isSaving}
                variant="danger"
                onClick={() =>
                  setPendingAction({
                    description: 'Cancel this package draft. Picked items remain operationally available for a new package.',
                    label: 'Cancel package',
                    run: () => run(() => fulfillmentService.cancelPackage(accessToken, id)),
                    variant: 'danger',
                  })
                }
              >
                Cancel
              </Button>
            ) : null}
          </div>
        }
        backTo="/packages"
        description={`Sales order #${pkg.sales_order_id}. Packing organizes picked items but does not create a stock ledger entry.`}
        kicker="Package"
        meta={[
          { label: 'Sales order', value: `#${pkg.sales_order_id}` },
          { label: 'Created', value: pkg.created_at ?? 'Package document' },
        ]}
        progress={<WorkflowProgress current={pkg.status} steps={packageSteps} />}
        sidePanel={
          <Card>
            <CardHeader>
              <h2 className="text-lg font-semibold text-warelyn-text">Related workflow</h2>
            </CardHeader>
            <CardBody className="space-y-3">
              <StatusBadge status={pkg.status}>{pkg.status}</StatusBadge>
              <p className="text-sm text-warelyn-muted">
                When this package is packed, it becomes a cleaner handoff point for fulfillment without mutating stock on its own.
              </p>
              <Link className="text-sm font-semibold text-warelyn-primary" to={`/sales/${pkg.sales_order_id}`}>
                Open sales order
              </Link>
            </CardBody>
          </Card>
        }
        status={<StatusBadge status={pkg.status}>{pkg.status}</StatusBadge>}
        summary={[
          { label: 'Items', value: pkg.items.length, helper: 'Lines in this package' },
          { label: 'Packed qty', value: formatDecimal(packedQty), helper: 'Operational quantity grouped here' },
        ]}
        title={pkg.package_number}
      >
        <TableShell
          description="Picked items grouped into this package."
          isEmpty={pkg.items.length === 0}
          rowCount={pkg.items.length}
          title="Package items"
        >
          <table>
            <thead>
              <tr>
                <th>Product</th>
                <th>Pick item</th>
                <th>Batch</th>
                <th>Serial</th>
                <th className="text-right">Quantity</th>
              </tr>
            </thead>
            <tbody>
              {pkg.items.map((item) => (
                <tr key={item.id}>
                  <td>
                    <div className="space-y-1">
                      <span className="font-semibold text-warelyn-text">{productsById[item.product_id]?.name ?? `Product #${item.product_id}`}</span>
                      <p className="text-xs text-warelyn-muted">SKU {productsById[item.product_id]?.sku ?? '-'}</p>
                    </div>
                  </td>
                  <td><span className="mono-cell">#{item.pick_task_item_id}</span></td>
                  <td><span className="mono-cell">{item.batch_id ?? '-'}</span></td>
                  <td><span className="mono-cell">{item.serial_id ?? '-'}</span></td>
                  <td className="number-cell">{formatDecimal(item.quantity)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </TableShell>
      </RecordDetailShell>

      <ConfirmationModal
        confirmLabel={pendingAction?.label}
        description={pendingAction?.description}
        isLoading={isSaving}
        onCancel={() => setPendingAction(null)}
        onConfirm={() => pendingAction?.run()}
        open={Boolean(pendingAction)}
        title="Confirm package action"
        variant={pendingAction?.variant}
      />
    </div>
  );
}
