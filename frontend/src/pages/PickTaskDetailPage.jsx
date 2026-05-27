import { useEffect, useState } from 'react';
import { BackButton } from '../components/ui/BackButton.jsx';
import { Link, useParams } from 'react-router-dom';
import { Boxes, ScanLine } from 'lucide-react';

import { BarcodeInput } from '../components/forms/BarcodeInput.jsx';
import { StatusBadge } from '../components/ui/Badge.jsx';
import { Button } from '../components/ui/Button.jsx';
import { Card, CardBody, CardHeader } from '../components/ui/Card.jsx';
import { ConfirmationModal } from '../components/ui/ConfirmationModal.jsx';
import { ErrorState } from '../components/ui/ErrorState.jsx';
import { Input } from '../components/ui/Input.jsx';
import { LoadingState } from '../components/ui/LoadingState.jsx';
import { RecordDetailShell } from '../components/ui/RecordDetailShell.jsx';
import { StockImpactPreview } from '../components/ui/StockImpactPreview.jsx';
import { WorkflowProgress } from '../components/ui/WorkflowProgress.jsx';
import { formatDecimal } from '../utils/formatters.js';
import { useAuth } from '../context/AuthContext.jsx';
import * as catalogService from '../services/catalogService.js';
import * as fulfillmentService from '../services/fulfillmentService.js';
import * as inventoryService from '../services/inventoryService.js';

const canWrite = new Set(['TENANT_ADMIN', 'INVENTORY_MANAGER', 'SALES_STAFF']);
const pickSteps = [
  { key: 'PENDING', label: 'Pending' },
  { key: 'IN_PROGRESS', label: 'In progress' },
  { key: 'PICKED', label: 'Picked' },
];
const selectClass = 'block w-full rounded-lg border border-warelyn-border bg-white px-3 py-2.5 text-sm text-warelyn-text shadow-sm outline-none transition focus:border-warelyn-primary focus:ring-4 focus:ring-blue-900/10';

export function PickTaskDetailPage() {
  const { id } = useParams();
  const { accessToken, user } = useAuth();
  const [task, setTask] = useState(null);
  const [productsById, setProductsById] = useState({});
  const [serials, setSerials] = useState([]);
  const [batches, setBatches] = useState([]);
  const [lines, setLines] = useState([]);
  const [scanQuery, setScanQuery] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');
  const [pendingAction, setPendingAction] = useState(null);
  const mayWrite = canWrite.has(user?.role);

  async function load() {
    setIsLoading(true);
    setError('');
    try {
      const [taskRow, products, serialRows, batchRows] = await Promise.all([
        fulfillmentService.getPickTask(accessToken, id),
        catalogService.listProducts(accessToken),
        inventoryService.listInventorySerials(accessToken),
        inventoryService.listInventoryBatches(accessToken),
      ]);
      setTask(taskRow);
      setProductsById(Object.fromEntries(products.map((product) => [product.id, product])));
      setSerials(serialRows);
      setBatches(batchRows);
      setLines(
        taskRow.items.map((item) => ({
          pick_task_item_id: item.id,
          picked_quantity: item.picked_quantity === '0.000' ? item.required_quantity : item.picked_quantity,
          batch_id: item.batch_id ?? '',
          serial_id: item.serial_id ?? '',
        })),
      );
    } catch (loadError) {
      setError(loadError.message);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [accessToken, id]);

  function updateLine(index, key, value) {
    setLines((current) =>
      current.map((line, lineIndex) => (lineIndex === index ? { ...line, [key]: value } : line)),
    );
  }

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

  async function submitPick() {
    await run(() =>
      fulfillmentService.pickPickTask(accessToken, id, {
        items: lines.map((line) => ({
          pick_task_item_id: Number(line.pick_task_item_id),
          picked_quantity: line.picked_quantity,
          batch_id: line.batch_id ? Number(line.batch_id) : null,
          serial_id: line.serial_id ? Number(line.serial_id) : null,
        })),
      }),
    );
  }

  if (isLoading) return <LoadingState />;
  if (!task) return <ErrorState description={error || 'Pick task not found.'} />;

  const requiredQty = task.items.reduce((sum, item) => sum + Number(item.required_quantity), 0);
  const pickedQty = lines.reduce((sum, line) => sum + Number(line.picked_quantity || 0), 0);
  const missingQty = Math.max(requiredQty - pickedQty, 0);
  const filteredLines = task.items.filter((item) => {
    if (!scanQuery) return true;
    const product = productsById[item.product_id];
    return `${product?.name ?? ''} ${product?.sku ?? ''} ${product?.barcode ?? ''}`.toLowerCase().includes(scanQuery.toLowerCase());
  });
  const advisoryItems = filteredLines.map((item) => {
    const lineIndex = task.items.findIndex((row) => row.id === item.id);
    const product = productsById[item.product_id];
    return {
      id: item.id,
      product: product?.name ?? `Product #${item.product_id}`,
      meta: `Reservation #${item.reservation_id} • Warehouse ${item.warehouse_id} • Location ${item.location_id}`,
      effect: `Picking ${formatDecimal(lines[lineIndex]?.picked_quantity)} of required ${formatDecimal(item.required_quantity)} against the reservation.`,
      warning: product?.track_serial ? 'Serial-tracked products need an explicit serial selection before completion.' : null,
    };
  });

  return (
    <div className="space-y-6">
      <BackButton to="/pick-tasks" />
      {error ? <ErrorState description={error} /> : null}
      <RecordDetailShell
        actions={
          <div className="flex flex-wrap gap-2">
            {mayWrite && task.status === 'PENDING' ? (
              <Button disabled={isSaving} onClick={() => run(() => fulfillmentService.startPickTask(accessToken, id))}>
                Start
              </Button>
            ) : null}
            {mayWrite && ['PENDING', 'IN_PROGRESS'].includes(task.status) ? (
              <Button
                disabled={isSaving}
                variant="danger"
                onClick={() =>
                  setPendingAction({
                    description: 'Cancel this pick task. The backend keeps reservation state separate from physical stock.',
                    label: 'Cancel pick task',
                    run: () => run(() => fulfillmentService.cancelPickTask(accessToken, id)),
                    variant: 'danger',
                  })
                }
              >
                Cancel
              </Button>
            ) : null}
            {mayWrite && ['PENDING', 'IN_PROGRESS'].includes(task.status) ? (
              <Button
                disabled={isSaving}
                variant="accent"
                onClick={() =>
                  setPendingAction({
                    description: 'Complete this picking step. The backend records picked allocation but does not deduct stock here.',
                    label: 'Save picked allocation',
                    run: submitPick,
                    variant: 'accent',
                  })
                }
              >
                Complete pick
              </Button>
            ) : null}
          </div>
        }
        backTo="/pick-tasks"
        description={`Sales order #${task.sales_order_id}. Picking records operational progress only; stock deduction still waits for fulfillment commit.`}
        kicker="Pick task"
        meta={[
          { label: 'Sales order', value: `#${task.sales_order_id}` },
          { label: 'Warehouse', value: task.items[0]?.warehouse_id ? `Warehouse #${task.items[0].warehouse_id}` : '-' },
          { label: 'Created', value: task.created_at ?? 'Active queue item' },
        ]}
        progress={<WorkflowProgress current={task.status} steps={pickSteps} />}
        sidePanel={
          <Card>
            <CardHeader>
              <h2 className="text-lg font-semibold text-warelyn-text">Picking notes</h2>
            </CardHeader>
            <CardBody className="space-y-4">
              <StatusBadge status={task.status}>{task.status}</StatusBadge>
              <div className="space-y-3 text-sm text-warelyn-muted">
                <div className="flex items-start gap-3">
                  <ScanLine className="mt-0.5 shrink-0 text-warelyn-primary" size={16} />
                  <p>Use SKU, barcode, serial, or batch inputs below to keep the workflow scanner-friendly.</p>
                </div>
                <div className="flex items-start gap-3">
                  <Boxes className="mt-0.5 shrink-0 text-warelyn-primary" size={16} />
                  <p>Picked quantities stay advisory until a fulfillment later commits the underlying reservation.</p>
                </div>
              </div>
            </CardBody>
          </Card>
        }
        status={<StatusBadge status={task.status}>{task.status}</StatusBadge>}
        summary={[
          { label: 'Pick lines', value: task.items.length, helper: 'Reservation lines in this task' },
          { label: 'Required qty', value: formatDecimal(requiredQty), helper: 'Total requested to pick' },
          { label: 'Picked qty', value: formatDecimal(pickedQty), helper: 'Current entered quantity' },
          { label: 'Missing qty', value: formatDecimal(missingQty), helper: 'Still needed before completion' },
        ]}
        title={task.pick_number}
      >
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-warelyn-text">Scanner filter</h2>
          </CardHeader>
          <CardBody>
            <BarcodeInput
              hint="Scan SKU or barcode to focus on matching pick lines."
              label="SKU / barcode"
              onChange={(event) => setScanQuery(event.target.value)}
              value={scanQuery}
            />
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-warelyn-text">Pick lines</h2>
          </CardHeader>
          <CardBody className="space-y-4">
            {filteredLines.length === 0 ? (
              <ErrorState description="No pick lines match the current scanner filter." title="No matching lines" />
            ) : (
              filteredLines.map((item) => {
                const index = task.items.findIndex((row) => row.id === item.id);
                const product = productsById[item.product_id];
                const availableSerials = serials.filter(
                  (serial) =>
                    serial.product_id === item.product_id &&
                    serial.warehouse_id === item.warehouse_id &&
                    serial.location_id === item.location_id &&
                    serial.status === 'IN_STOCK',
                );
                const availableBatches = batches.filter(
                  (batch) =>
                    batch.product_id === item.product_id &&
                    batch.warehouse_id === item.warehouse_id &&
                    batch.location_id === item.location_id &&
                    batch.status === 'ACTIVE',
                );
                return (
                  <div className="grid gap-3 rounded-xl border border-warelyn-border p-4 lg:grid-cols-[minmax(0,1.2fr)_140px_1fr_1fr_180px]" key={item.id}>
                    <div>
                      <span className="text-xs font-semibold uppercase tracking-wide text-warelyn-muted">Product</span>
                      <p className="mt-2 font-semibold text-warelyn-text">{product?.name ?? `Product #${item.product_id}`}</p>
                      <p className="mt-1 text-xs text-warelyn-muted">SKU {product?.sku ?? '-'} • Reservation #{item.reservation_id}</p>
                      <p className="mt-1 text-xs text-warelyn-muted">Warehouse {item.warehouse_id} • Location {item.location_id}</p>
                    </div>
                    <Input
                      label="Picked qty"
                      min="0"
                      step="0.001"
                      type="number"
                      value={lines[index]?.picked_quantity ?? ''}
                      onChange={(event) => updateLine(index, 'picked_quantity', event.target.value)}
                    />
                    <label className="block">
                      <span className="mb-2 block text-sm font-medium text-warelyn-text">Serial</span>
                      <select
                        className={selectClass}
                        value={lines[index]?.serial_id ?? ''}
                        onChange={(event) => updateLine(index, 'serial_id', event.target.value)}
                      >
                        <option value="">{product?.track_serial ? 'Select serial' : 'Not serial-tracked'}</option>
                        {availableSerials.map((serial) => (
                          <option key={serial.id} value={serial.id}>
                            {serial.serial_number}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label className="block">
                      <span className="mb-2 block text-sm font-medium text-warelyn-text">Batch</span>
                      <select
                        className={selectClass}
                        value={lines[index]?.batch_id ?? ''}
                        onChange={(event) => updateLine(index, 'batch_id', event.target.value)}
                      >
                        <option value="">Optional</option>
                        {availableBatches.map((batch) => (
                          <option key={batch.id} value={batch.id}>
                            {batch.batch_number}
                            {batch.expiry_date ? ` exp ${batch.expiry_date}` : ''}
                          </option>
                        ))}
                      </select>
                    </label>
                    <div className="space-y-2">
                      <span className="text-xs font-semibold uppercase tracking-wide text-warelyn-muted">Required</span>
                      <p className="text-lg font-semibold text-warelyn-text">{formatDecimal(item.required_quantity)}</p>
                      <StatusBadge status={item.status}>{item.status}</StatusBadge>
                    </div>
                  </div>
                );
              })
            )}
          </CardBody>
        </Card>

        <StockImpactPreview items={advisoryItems} title="Pick outcome preview" />
      </RecordDetailShell>

      <ConfirmationModal
        confirmLabel={pendingAction?.label}
        description={pendingAction?.description}
        isLoading={isSaving}
        onCancel={() => setPendingAction(null)}
        onConfirm={() => pendingAction?.run()}
        open={Boolean(pendingAction)}
        title="Confirm pick workflow action"
        variant={pendingAction?.variant}
      />
    </div>
  );
}
