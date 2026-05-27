import { useEffect, useState } from 'react';
import { BackButton } from '../components/ui/BackButton.jsx';
import { useNavigate, useParams } from 'react-router-dom';

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
import * as returnsService from '../services/returnsService.js';

const selectClass = 'block w-full rounded-lg border border-warelyn-border bg-white px-3 py-2.5 text-sm text-warelyn-text shadow-sm outline-none transition focus:border-warelyn-primary focus:ring-4 focus:ring-blue-900/10';
const outcomes = [
  ['ACCEPTED_RESTOCK', 'Sellable restock', 'Adds returned quantity to on-hand and available stock through backend inventory workflows.'],
  ['ACCEPTED_BLOCKED', 'QC hold', 'Creates blocked return stock only. It is not sellable.'],
  ['DAMAGED', 'Damaged', 'Creates damaged blocked return stock only.'],
  ['SCRAPPED', 'Scrapped', 'Creates scrapped blocked return stock only.'],
  ['REJECTED', 'Rejected', 'No stock movement or blocked stock record.'],
];

export function SalesReturnInspectPage() {
  const { id } = useParams();
  const { accessToken } = useAuth();
  const navigate = useNavigate();
  const [salesReturn, setSalesReturn] = useState(null);
  const [productsById, setProductsById] = useState({});
  const [items, setItems] = useState([]);
  const [idempotencyKey, setIdempotencyKey] = useState(`return-process-${id}-${Date.now()}`);
  const [note, setNote] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');
  const [isConfirming, setIsConfirming] = useState(false);

  useEffect(() => {
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
        setItems(
          row.items.map((item) => ({
            sales_return_item_id: item.id,
            qc_status: item.qc_status === 'PENDING' ? 'ACCEPTED_RESTOCK' : item.qc_status,
            accepted_quantity: item.accepted_quantity === '0.000' ? item.returned_quantity : item.accepted_quantity,
            rejected_quantity: item.rejected_quantity,
            reason: item.reason ?? '',
            notes: item.notes ?? '',
            returned_quantity: item.returned_quantity,
            product_id: item.product_id,
          })),
        );
      } catch (loadError) {
        setError(loadError.message);
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, [accessToken, id]);

  function updateItem(index, key, value) {
    setItems((current) =>
      current.map((item, itemIndex) => {
        if (itemIndex !== index) return item;
        if (key === 'qc_status' && value === 'REJECTED') {
          return { ...item, qc_status: value, accepted_quantity: '0', rejected_quantity: item.returned_quantity };
        }
        if (key === 'qc_status') {
          return { ...item, qc_status: value, accepted_quantity: item.returned_quantity, rejected_quantity: '0' };
        }
        return { ...item, [key]: value };
      }),
    );
  }

  async function inspectAndProcess(event) {
    event.preventDefault();
    setIsConfirming(true);
  }

  async function processInspection() {
    setIsSaving(true);
    setError('');
    try {
      const inspectionPayload = { notes: note, items: items.map(({ returned_quantity, product_id, ...item }) => item) };
      await returnsService.inspectSalesReturn(accessToken, id, inspectionPayload);
      await returnsService.processSalesReturn(accessToken, id, { idempotency_key: idempotencyKey, note });
      setIsConfirming(false);
      navigate(`/returns/${id}`);
    } catch (saveError) {
      setError(saveError.message);
    } finally {
      setIsSaving(false);
    }
  }

  if (isLoading) return <LoadingState />;
  if (!salesReturn) return <ErrorState description={error || 'Sales return not found.'} />;

  const advisoryItems = items.map((item) => {
    const outcome = outcomes.find(([value]) => value === item.qc_status);
    return {
      id: item.sales_return_item_id,
      product: productsById[item.product_id]?.name ?? `Product #${item.product_id}`,
      meta: `Returned ${formatDecimal(item.returned_quantity)} • Accepted ${formatDecimal(item.accepted_quantity)} • Rejected ${formatDecimal(item.rejected_quantity)}`,
      effect: outcome?.[1] ?? item.qc_status,
      warning: outcome?.[2] ?? null,
    };
  });

  return (
    <div className="space-y-6">
      <BackButton to="/returns/qc" />
      <PageHeader
        backTo="/returns"
        description="Choose the final QC decision for each returned line. The preview below mirrors backend outcomes and does not calculate authoritative stock on the frontend."
        kicker="QC inspection"
        title={`Inspect ${salesReturn.return_number}`}
      />
      {error ? <ErrorState description={error} /> : null}
      <form className="space-y-6" onSubmit={inspectAndProcess}>
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-warelyn-text">Inspection outcomes</h2>
          </CardHeader>
          <CardBody className="space-y-4">
            {items.map((item, index) => {
              const outcome = outcomes.find(([value]) => value === item.qc_status);
              return (
                <div className="grid gap-3 rounded-xl border border-warelyn-border p-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)_140px_140px]" key={item.sales_return_item_id}>
                  <div>
                    <span className="text-xs font-semibold uppercase tracking-wide text-warelyn-muted">Product</span>
                    <p className="mt-2 font-semibold text-warelyn-text">{productsById[item.product_id]?.name ?? `Product #${item.product_id}`}</p>
                    <p className="mt-1 text-xs text-warelyn-muted">Returned {formatDecimal(item.returned_quantity)}</p>
                  </div>
                  <label className="block">
                    <span className="mb-2 block text-sm font-medium text-warelyn-text">QC outcome</span>
                    <select className={selectClass} value={item.qc_status} onChange={(event) => updateItem(index, 'qc_status', event.target.value)}>
                      {outcomes.map(([value, label]) => (
                        <option key={value} value={value}>
                          {label}
                        </option>
                      ))}
                    </select>
                    <p className="mt-2 text-xs text-warelyn-muted">{outcome?.[2]}</p>
                  </label>
                  <Input
                    label="Accepted"
                    min="0"
                    step="0.001"
                    type="number"
                    value={item.accepted_quantity}
                    onChange={(event) => updateItem(index, 'accepted_quantity', event.target.value)}
                  />
                  <Input
                    label="Rejected"
                    min="0"
                    step="0.001"
                    type="number"
                    value={item.rejected_quantity}
                    onChange={(event) => updateItem(index, 'rejected_quantity', event.target.value)}
                  />
                  <Input className="lg:col-span-2" label="Reason" value={item.reason} onChange={(event) => updateItem(index, 'reason', event.target.value)} />
                  <Input className="lg:col-span-2" label="Line notes" value={item.notes} onChange={(event) => updateItem(index, 'notes', event.target.value)} />
                </div>
              );
            })}
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-warelyn-text">Processing controls</h2>
          </CardHeader>
          <CardBody className="grid gap-4 md:grid-cols-2">
            <Input label="Idempotency key" required value={idempotencyKey} onChange={(event) => setIdempotencyKey(event.target.value)} />
            <Input label="QC note" value={note} onChange={(event) => setNote(event.target.value)} />
          </CardBody>
        </Card>

        <StockImpactPreview items={advisoryItems} title="QC stock outcome preview" />

        <div className="sticky-form-footer">
          <div className="workflow-helper-panel max-w-xl">
            <h3>What happens next?</h3>
            <p>Processing applies the final backend stock decision per line. Restock increases sellable stock, blocked and damaged outcomes remain non-sellable, and rejected lines do not mutate stock.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button onClick={() => navigate(`/returns/${id}`)} type="button" variant="ghost">
              Cancel
            </Button>
            <Button disabled={isSaving} type="submit" variant="accent">
              Inspect and process
            </Button>
          </div>
        </div>
      </form>

      <ConfirmationModal
        confirmLabel="Inspect and process"
        description="The backend will apply each QC outcome. Sellable restock uses backend inventory workflows; blocked, damaged, and scrapped outcomes remain non-sellable."
        isLoading={isSaving}
        onCancel={() => setIsConfirming(false)}
        onConfirm={processInspection}
        open={isConfirming}
        title="Confirm return QC outcome"
        variant="accent"
      />
    </div>
  );
}
