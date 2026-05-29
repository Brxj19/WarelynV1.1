import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';

import { BackButton } from '../components/ui/BackButton.jsx';
import { Button } from '../components/ui/Button.jsx';
import { Card, CardBody, CardHeader } from '../components/ui/Card.jsx';
import { ConfirmationModal } from '../components/ui/ConfirmationModal.jsx';
import { EmptyState } from '../components/ui/EmptyState.jsx';
import { ErrorState } from '../components/ui/ErrorState.jsx';
import { Input } from '../components/ui/Input.jsx';
import { LoadingState } from '../components/ui/LoadingState.jsx';
import { PageHeader } from '../components/ui/PageHeader.jsx';
import { RecordDetailShell } from '../components/ui/RecordDetailShell.jsx';
import { ScreenToolbar } from '../components/ui/ScreenToolbar.jsx';
import { StatusBadge } from '../components/ui/Badge.jsx';
import { TableShell } from '../components/ui/TableShell.jsx';
import { WorkflowProgress } from '../components/ui/WorkflowProgress.jsx';
import { emptyStateIllustrations } from '../lib/emptyStates.js';
import { formatDate, formatDecimal } from '../utils/formatters.js';
import { useAuth } from '../context/AuthContext.jsx';
import * as catalogService from '../services/catalogService.js';
import * as cycleCountService from '../services/cycleCountService.js';
import * as warehouseService from '../services/warehouseService.js';

const selectClass = 'block w-full rounded-lg border border-warelyn-border bg-white px-3 py-2.5 text-sm text-warelyn-text shadow-sm outline-none transition focus:border-warelyn-primary focus:ring-4 focus:ring-blue-900/10';
const countSteps = [
  { key: 'DRAFT', label: 'Draft' },
  { key: 'SUBMITTED', label: 'Submitted' },
  { key: 'RECONCILED', label: 'Reconciled' },
];

export function CycleCountsPage() {
  const { accessToken } = useAuth();
  const [sessions, setSessions] = useState([]);
  const [warehousesById, setWarehousesById] = useState({});
  const [search, setSearch] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    Promise.all([
      cycleCountService.listSessions(accessToken),
      warehouseService.listWarehouses(accessToken),
    ])
      .then(([sessionRows, warehouseRows]) => {
        setSessions(sessionRows);
        setWarehousesById(Object.fromEntries(warehouseRows.map((warehouse) => [warehouse.id, warehouse])));
      })
      .catch((e) => setError(e.message))
      .finally(() => setIsLoading(false));
  }, [accessToken]);

  const rows = useMemo(() => {
    const value = search.trim().toLowerCase();
    if (!value) return sessions;
    return sessions.filter((s) => `${s.session_number} ${s.status}`.toLowerCase().includes(value));
  }, [sessions, search]);

  return (
    <div className="space-y-6">
      <PageHeader kicker="Operations" title="Cycle counts" description="Physical stock count sessions. Create a session, count items, submit, and reconcile variances." />
      <TableShell
        description={`${rows.length} session(s) in view`}
        emptyDescription={search ? 'Adjust your filters.' : 'Create your first cycle count session to start verifying stock.'}
        emptyIllustration={search ? emptyStateIllustrations.noResult : emptyStateIllustrations.inventory}
        emptyPrimaryActionLabel={!search ? 'New cycle count' : undefined}
        emptyPrimaryActionTo={!search ? '/cycle-counts/new' : undefined}
        emptySecondaryActionLabel={search ? 'Clear filters' : undefined}
        emptyTitle={search ? 'No matching sessions' : 'No cycle count sessions yet'}
        error={error}
        isEmpty={rows.length === 0}
        isLoading={isLoading}
        onEmptySecondaryAction={search ? () => setSearch('') : undefined}
        rowCount={rows.length}
        title="Cycle count sessions"
        toolbar={
          <ScreenToolbar onSearchChange={setSearch} searchPlaceholder="Search session number or status" searchValue={search}>
            <Link to="/cycle-counts/new"><Button>New session</Button></Link>
          </ScreenToolbar>
        }
      >
        <table>
          <thead>
            <tr>
              <th>Session</th>
              <th>Status</th>
              <th>Warehouse</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((session) => (
              <tr key={session.id}>
                <td>
                  <Link className="font-semibold text-warelyn-primary" to={`/cycle-counts/${session.id}`}>
                    {session.session_number}
                  </Link>
                </td>
                <td><StatusBadge status={session.status}>{session.status}</StatusBadge></td>
                <td>{warehousesById[session.warehouse_id]?.name ?? `#${session.warehouse_id}`}</td>
                <td>{formatDate(session.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </TableShell>
    </div>
  );
}

export function CycleCountFormPage() {
  const { accessToken } = useAuth();
  const navigate = useNavigate();
  const [warehouses, setWarehouses] = useState([]);
  const [form, setForm] = useState({ warehouse_id: '', notes: '' });
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    warehouseService.listWarehouses(accessToken).then((rows) => {
      setWarehouses(rows);
      if (rows.length) setForm((f) => ({ ...f, warehouse_id: String(rows[0].id) }));
    }).catch((e) => setError(e.message)).finally(() => setIsLoading(false));
  }, [accessToken]);

  async function handleSubmit(event) {
    event.preventDefault();
    setIsSaving(true);
    setError('');
    try {
      const session = await cycleCountService.createSession(accessToken, { warehouse_id: Number(form.warehouse_id), notes: form.notes || null });
      navigate(`/cycle-counts/${session.id}`);
    } catch (e) {
      setError(e.message);
    } finally {
      setIsSaving(false);
    }
  }

  if (isLoading) return <LoadingState />;

  return (
    <div className="space-y-6">
      <BackButton to="/cycle-counts" />
      <PageHeader backTo="/cycle-counts" description="Create a new cycle count session for a warehouse. Add count lines after creation." kicker="Operations" title="New cycle count" />
      {error ? <ErrorState description={error} /> : null}
      <form className="space-y-6" onSubmit={handleSubmit}>
        <Card>
          <CardHeader><h2 className="text-lg font-semibold text-warelyn-text">Session details</h2></CardHeader>
          <CardBody className="grid gap-4 md:grid-cols-2">
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-warelyn-text">Warehouse</span>
              <select className={selectClass} required value={form.warehouse_id} onChange={(e) => setForm({ ...form, warehouse_id: e.target.value })}>
                <option value="">Select warehouse</option>
                {warehouses.map((w) => <option key={w.id} value={w.id}>{w.name}</option>)}
              </select>
            </label>
            <Input label="Notes" value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
          </CardBody>
        </Card>
        <div className="sticky-form-footer">
          <div className="workflow-helper-panel max-w-xl">
            <h3>What happens next?</h3>
            <p>This creates a draft session. Add count lines, record counted quantities, submit, then reconcile to adjust stock.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button onClick={() => navigate('/cycle-counts')} type="button" variant="ghost">Cancel</Button>
            <Button disabled={isSaving} type="submit">{isSaving ? 'Creating...' : 'Create session'}</Button>
          </div>
        </div>
      </form>
    </div>
  );
}

export function CycleCountDetailPage() {
  const { id } = useParams();
  const { accessToken, user } = useAuth();
  const [session, setSession] = useState(null);
  const [lines, setLines] = useState([]);
  const [products, setProducts] = useState([]);
  const [locations, setLocations] = useState([]);
  const [warehouseName, setWarehouseName] = useState('');
  const [newLine, setNewLine] = useState({ product_id: '', location_id: '' });
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');
  const [pendingAction, setPendingAction] = useState(null);
  const mayWrite = user?.role === 'TENANT_ADMIN' || user?.role === 'INVENTORY_MANAGER';

  async function load() {
    setIsLoading(true);
    setError('');
    try {
      const [sessionRow, productRows, warehouseRows] = await Promise.all([
        cycleCountService.getSession(accessToken, id),
        catalogService.listProducts(accessToken),
        warehouseService.listWarehouses(accessToken),
      ]);
      setSession(sessionRow);
      setLines(sessionRow.lines || []);
      setProducts(productRows);
      setWarehouseName(warehouseRows.find((warehouse) => warehouse.id === sessionRow.warehouse_id)?.name ?? `#${sessionRow.warehouse_id}`);
      const locs = await warehouseService.listWarehouseLocations(accessToken, sessionRow.warehouse_id);
      setLocations(locs);
      if (locs.length && !newLine.location_id) setNewLine((n) => ({ ...n, location_id: String(locs[0].id) }));
    } catch (e) {
      setError(e.message);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => { load(); }, [accessToken, id]);

  async function addLine(event) {
    event.preventDefault();
    setIsSaving(true);
    setError('');
    try {
      await cycleCountService.addLine(accessToken, id, { product_id: Number(newLine.product_id), location_id: Number(newLine.location_id) });
      setNewLine({ product_id: '', location_id: locations[0]?.id ? String(locations[0].id) : '' });
      await load();
    } catch (e) {
      setError(e.message);
    } finally {
      setIsSaving(false);
    }
  }

  async function saveLine(lineId, countedQty, notes) {
    setIsSaving(true);
    setError('');
    try {
      await cycleCountService.updateLine(accessToken, id, lineId, { counted_quantity: countedQty, notes: notes || null });
      await load();
    } catch (e) {
      setError(e.message);
    } finally {
      setIsSaving(false);
    }
  }

  async function runAction(action) {
    setIsSaving(true);
    setError('');
    try {
      await action();
      setPendingAction(null);
      await load();
    } catch (e) {
      setError(e.message);
    } finally {
      setIsSaving(false);
    }
  }

  if (isLoading) return <LoadingState />;
  if (!session) return <ErrorState description={error || 'Session not found.'} />;

  const productsById = Object.fromEntries(products.map((p) => [p.id, p]));
  const locationsById = Object.fromEntries(locations.map((l) => [l.id, l]));
  const totalVariance = lines.reduce((sum, l) => sum + Number(l.variance || 0), 0);
  const countedLines = lines.filter((l) => l.counted_quantity !== null).length;
  const canAddLines = ['DRAFT', 'IN_PROGRESS'].includes(session.status);
  const canSubmit = ['DRAFT', 'IN_PROGRESS'].includes(session.status) && countedLines > 0;
  const canReconcile = session.status === 'SUBMITTED';

  return (
    <div className="space-y-6">
      <BackButton to="/cycle-counts" />
      {error ? <ErrorState description={error} /> : null}
      <RecordDetailShell
        actions={
          <div className="flex flex-wrap gap-2">
            {mayWrite && ['DRAFT', 'IN_PROGRESS', 'SUBMITTED'].includes(session.status) ? (
              <Button
                disabled={isSaving}
                variant="danger"
                onClick={() => setPendingAction({
                  label: 'Cancel session',
                  description: 'Cancel this cycle count session. No stock adjustments will be made.',
                  run: () => runAction(() => cycleCountService.cancelSession(accessToken, id)),
                  variant: 'danger',
                })}
              >
                Cancel
              </Button>
            ) : null}
            {mayWrite && canSubmit ? (
              <Button disabled={isSaving} onClick={() => setPendingAction({ label: 'Submit count', description: 'Submit this cycle count for reconciliation review. No further counting after submission.', run: () => runAction(() => cycleCountService.submitSession(accessToken, id)), variant: 'primary' })}>
                Submit
              </Button>
            ) : null}
            {mayWrite && canReconcile ? (
              <Button disabled={isSaving} variant="accent" onClick={() => setPendingAction({ label: 'Reconcile', description: 'Reconcile variances and adjust stock levels. This action is irreversible.', run: () => runAction(() => cycleCountService.reconcileSession(accessToken, id)), variant: 'accent' })}>
                Reconcile
              </Button>
            ) : null}
          </div>
        }
        backTo="/cycle-counts"
        description="Count physical stock, record variances, and reconcile to adjust inventory levels."
        kicker="Cycle count"
        meta={[
          { label: 'Warehouse', value: warehouseName || `#${session.warehouse_id}` },
          { label: 'Created', value: formatDate(session.created_at) },
          { label: 'Notes', value: session.notes || 'None' },
        ]}
        progress={<WorkflowProgress current={session.status} steps={countSteps} />}
        status={<StatusBadge status={session.status}>{session.status}</StatusBadge>}
        summary={[
          { label: 'Lines', value: lines.length, helper: 'Count lines added' },
          { label: 'Counted', value: countedLines, helper: 'Lines with recorded count' },
          { label: 'Net variance', value: formatDecimal(totalVariance), helper: 'Sum of all variances' },
        ]}
        title={session.session_number}
      >
        <TableShell description="Count lines with system vs counted quantities." isEmpty={lines.length === 0} rowCount={lines.length} title="Count lines">
          <table>
            <thead>
              <tr>
                <th>Product</th>
                <th>Location</th>
                <th className="text-right">System qty</th>
                <th className="text-right">Counted qty</th>
                <th className="text-right">Variance</th>
                <th>Notes</th>
                {canAddLines ? <th>Action</th> : null}
              </tr>
            </thead>
            <tbody>
              {lines.map((line) => (
                <CountLineRow
                  key={line.id}
                  canEdit={canAddLines}
                  line={line}
                  location={locationsById[line.location_id]}
                  onSave={saveLine}
                  product={productsById[line.product_id]}
                  saving={isSaving}
                />
              ))}
            </tbody>
          </table>
        </TableShell>

        {mayWrite && canAddLines ? (
          <Card>
            <CardHeader><h2 className="text-lg font-semibold text-warelyn-text">Add count line</h2></CardHeader>
            <CardBody>
              <form className="grid gap-3 md:grid-cols-[2fr_2fr_auto]" onSubmit={addLine}>
                <label className="block">
                  <span className="mb-2 block text-sm font-medium text-warelyn-text">Product</span>
                  <select className={selectClass} required value={newLine.product_id} onChange={(e) => setNewLine({ ...newLine, product_id: e.target.value })}>
                    <option value="">Select product</option>
                    {products.map((p) => <option key={p.id} value={p.id}>{p.name} ({p.sku})</option>)}
                  </select>
                </label>
                <label className="block">
                  <span className="mb-2 block text-sm font-medium text-warelyn-text">Location</span>
                  <select className={selectClass} required value={newLine.location_id} onChange={(e) => setNewLine({ ...newLine, location_id: e.target.value })}>
                    <option value="">Select location</option>
                    {locations.map((l) => <option key={l.id} value={l.id}>{l.name} ({l.location_type})</option>)}
                  </select>
                </label>
                <div className="flex items-end">
                  <Button disabled={isSaving} type="submit">Add line</Button>
                </div>
              </form>
            </CardBody>
          </Card>
        ) : null}
      </RecordDetailShell>

      <ConfirmationModal
        confirmLabel={pendingAction?.label}
        description={pendingAction?.description}
        isLoading={isSaving}
        onCancel={() => setPendingAction(null)}
        onConfirm={async () => { await pendingAction?.run(); }}
        open={Boolean(pendingAction)}
        title="Confirm cycle count action"
        variant={pendingAction?.variant}
      />
    </div>
  );
}

function CountLineRow({ line, product, location, canEdit, onSave, saving }) {
  const [counted, setCounted] = useState(line.counted_quantity !== null ? String(Number(line.counted_quantity)) : '');
  const [notes, setNotes] = useState(line.notes || '');

  useEffect(() => {
    setCounted(line.counted_quantity !== null ? String(Number(line.counted_quantity)) : '');
    setNotes(line.notes || '');
  }, [line.counted_quantity, line.notes]);

  const dirty = Number(counted || Number.NaN) !== Number(line.counted_quantity ?? Number.NaN) || (line.notes || '') !== notes;

  return (
    <tr>
      <td><span className="font-semibold text-warelyn-text">{product?.name ?? `#${line.product_id}`}</span></td>
      <td>{location?.name ?? `#${line.location_id}`}</td>
      <td className="number-cell">{formatDecimal(line.system_quantity)}</td>
      <td className="number-cell">
        {canEdit ? (
          <input className="w-24 rounded border border-warelyn-border px-2 py-1 text-right text-sm" min="0" step="0.001" type="number" value={counted} onChange={(e) => setCounted(e.target.value)} />
        ) : (
          line.counted_quantity !== null ? formatDecimal(line.counted_quantity) : '-'
        )}
      </td>
      <td className="number-cell">{line.variance !== null ? formatDecimal(line.variance) : '-'}</td>
      <td>
        {canEdit ? (
          <input className="w-32 rounded border border-warelyn-border px-2 py-1 text-sm" value={notes} onChange={(e) => setNotes(e.target.value)} />
        ) : (
          line.notes || '-'
        )}
      </td>
      {canEdit ? (
        <td>
          <Button disabled={saving || !dirty || !counted} type="button" variant="secondary" onClick={() => onSave(line.id, counted, notes)}>
            Save
          </Button>
        </td>
      ) : null}
    </tr>
  );
}
