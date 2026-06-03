import { ArrowRight, CheckCircle2, Plus, XCircle } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';

import { Button } from '../components/ui/Button.jsx';
import { Card, CardBody, CardHeader } from '../components/ui/Card.jsx';
import { ConfirmationModal } from '../components/ui/ConfirmationModal.jsx';
import { ErrorState } from '../components/ui/ErrorState.jsx';
import { LoadingState } from '../components/ui/LoadingState.jsx';
import { PageHeader } from '../components/ui/PageHeader.jsx';
import { StatusBadge } from '../components/ui/Badge.jsx';
import { TableShell } from '../components/ui/TableShell.jsx';
import { ScreenToolbar } from '../components/ui/ScreenToolbar.jsx';
import { emptyStateIllustrations } from '../lib/emptyStates.js';
import { formatDate } from '../utils/formatters.js';
import { useAuth } from '../context/AuthContext.jsx';
import { apiRequest } from '../services/apiClient.js';

function listPutawayTasks(accessToken, status) {
  const params = status ? `?status=${status}` : '';
  return apiRequest(`/putaway-tasks${params}`, { accessToken });
}

function createPutawayTask(accessToken, body) {
  return apiRequest('/putaway-tasks', { accessToken, method: 'POST', body: JSON.stringify(body) });
}

function getPutawayTask(accessToken, id) {
  return apiRequest(`/putaway-tasks/${id}`, { accessToken });
}

function completePutawayTask(accessToken, id) {
  return apiRequest(`/putaway-tasks/${id}/complete`, { accessToken, method: 'POST', body: JSON.stringify({}) });
}

function startPutawayTask(accessToken, id) {
  return apiRequest(`/putaway-tasks/${id}/start`, { accessToken, method: 'POST', body: JSON.stringify({}) });
}

function cancelPutawayTask(accessToken, id) {
  return apiRequest(`/putaway-tasks/${id}/cancel`, { accessToken, method: 'POST', body: JSON.stringify({}) });
}

function listWarehouses(accessToken) {
  return apiRequest('/warehouses', { accessToken });
}

function listLocations(accessToken, warehouseId) {
  return apiRequest(`/warehouses/${warehouseId}/locations`, { accessToken });
}

function listProducts(accessToken) {
  return apiRequest('/catalog/products', { accessToken });
}

function normalizePutawayTask(task) {
  if (!task || typeof task !== 'object' || Array.isArray(task)) return null;
  const status = typeof task.status === 'string' ? task.status : task.status?.value ?? String(task.status ?? '');
  return {
    ...task,
    status,
    product_id: task.product_id ?? '',
    warehouse_id: task.warehouse_id ?? '',
    from_location_id: task.from_location_id ?? '',
    to_location_id: task.to_location_id ?? null,
    quantity: task.quantity ?? '',
    receipt_id: task.receipt_id ?? null,
    created_at: task.created_at ?? null,
  };
}

export function PutawayTasksPage() {
  const { accessToken } = useAuth();
  const navigate = useNavigate();
  const [tasks, setTasks] = useState([]);
  const [search, setSearch] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [warehouses, setWarehouses] = useState([]);
  const [locations, setLocations] = useState([]);
  const [products, setProducts] = useState([]);
  const [form, setForm] = useState({ product_id: '', warehouse_id: '', from_location_id: '', to_location_id: '', quantity: '', receipt_id: '' });
  const [formError, setFormError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function loadTasks() {
    setIsLoading(true);
    try {
      setTasks(await listPutawayTasks(accessToken));
    } catch (e) {
      setError(e.message);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => { loadTasks(); }, [accessToken]);

  useEffect(() => {
    if (showForm) {
      listWarehouses(accessToken).then(setWarehouses).catch(() => {});
      listProducts(accessToken).then(setProducts).catch(() => {});
    }
  }, [showForm, accessToken]);

  useEffect(() => {
    if (form.warehouse_id) {
      listLocations(accessToken, form.warehouse_id).then(setLocations).catch(() => setLocations([]));
    } else {
      setLocations([]);
    }
  }, [form.warehouse_id, accessToken]);

  async function handleCreate(e) {
    e.preventDefault();
    setFormError('');
    if (!form.product_id || !form.warehouse_id || !form.from_location_id || !form.quantity) {
      setFormError('Product, warehouse, from location, and quantity are required.');
      return;
    }
    setIsSubmitting(true);
    try {
      const body = {
        product_id: Number(form.product_id),
        warehouse_id: Number(form.warehouse_id),
        from_location_id: Number(form.from_location_id),
        to_location_id: form.to_location_id ? Number(form.to_location_id) : null,
        quantity: form.quantity,
      };
      if (form.receipt_id) body.receipt_id = Number(form.receipt_id);
      await createPutawayTask(accessToken, body);
      setShowForm(false);
      setForm({ product_id: '', warehouse_id: '', from_location_id: '', to_location_id: '', quantity: '', receipt_id: '' });
      await loadTasks();
    } catch (e) {
      setFormError(e.message);
    } finally {
      setIsSubmitting(false);
    }
  }

  const rows = search
    ? tasks.filter((t) => `${t.id} ${t.status} ${t.product_id}`.toLowerCase().includes(search.toLowerCase()))
    : tasks;

  return (
    <div className="space-y-6">
      <PageHeader
        kicker="Warehousing"
        title="Putaway Tasks"
        description="Move received stock from receiving docks to storage locations."
        actions={
          <Button variant="primary" onClick={() => setShowForm(!showForm)}>
            <Plus size={16} /> Create Putaway Task
          </Button>
        }
      />

      {showForm && (
        <Card>
          <CardHeader title="Create Putaway Task" />
          <CardBody>
            {formError && <p className="mb-3 text-sm text-red-600">{formError}</p>}
            <form className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3" onSubmit={handleCreate}>
              <div>
                <label className="mb-1 block text-xs font-medium text-warelyn-muted">Product</label>
                <select
                  className="w-full rounded-lg border border-warelyn-border px-3 py-2 text-sm"
                  value={form.product_id}
                  onChange={(e) => setForm({ ...form, product_id: e.target.value })}
                >
                  <option value="">Select product...</option>
                  {products.map((p) => (
                    <option key={p.id} value={p.id}>{p.name} ({p.sku})</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-warelyn-muted">Warehouse</label>
                <select
                  className="w-full rounded-lg border border-warelyn-border px-3 py-2 text-sm"
                  value={form.warehouse_id}
                  onChange={(e) => setForm({ ...form, warehouse_id: e.target.value, from_location_id: '', to_location_id: '' })}
                >
                  <option value="">Select warehouse...</option>
                  {warehouses.map((w) => (
                    <option key={w.id} value={w.id}>{w.name} ({w.code})</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-warelyn-muted">From Location</label>
                <select
                  className="w-full rounded-lg border border-warelyn-border px-3 py-2 text-sm"
                  value={form.from_location_id}
                  onChange={(e) => setForm({ ...form, from_location_id: e.target.value })}
                  disabled={!form.warehouse_id}
                >
                  <option value="">Select from location...</option>
                  {locations.map((l) => (
                    <option key={l.id} value={l.id}>{l.name} ({l.code}) — {l.location_type}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-warelyn-muted">To Location</label>
                <select
                  className="w-full rounded-lg border border-warelyn-border px-3 py-2 text-sm"
                  value={form.to_location_id}
                  onChange={(e) => setForm({ ...form, to_location_id: e.target.value })}
                  disabled={!form.warehouse_id}
                >
                  <option value="">Select to location...</option>
                  {locations.map((l) => (
                    <option key={l.id} value={l.id}>{l.name} ({l.code}) — {l.location_type}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-warelyn-muted">Quantity</label>
                <input
                  className="w-full rounded-lg border border-warelyn-border px-3 py-2 text-sm"
                  min="1"
                  placeholder="e.g. 2000"
                  type="number"
                  value={form.quantity}
                  onChange={(e) => setForm({ ...form, quantity: e.target.value })}
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-warelyn-muted">Receipt ID (optional)</label>
                <input
                  className="w-full rounded-lg border border-warelyn-border px-3 py-2 text-sm"
                  placeholder="e.g. 1"
                  type="number"
                  value={form.receipt_id}
                  onChange={(e) => setForm({ ...form, receipt_id: e.target.value })}
                />
              </div>
              <div className="flex items-end gap-2 sm:col-span-2 lg:col-span-3">
                <Button disabled={isSubmitting} type="submit" variant="primary">
                  {isSubmitting ? 'Creating...' : 'Create Task'}
                </Button>
                <Button type="button" variant="ghost" onClick={() => setShowForm(false)}>Cancel</Button>
              </div>
            </form>
          </CardBody>
        </Card>
      )}

      <TableShell
        description={`${rows.length} putaway task(s)`}
        emptyDescription={search ? 'No tasks match your filter.' : 'No putaway tasks created yet. Click "Create Putaway Task" to get started.'}
        emptyIllustration={search ? emptyStateIllustrations.noResult : emptyStateIllustrations.warehouse}
        emptySecondaryActionLabel={search ? 'Clear filters' : undefined}
        emptyTitle={search ? 'No matching tasks' : 'No putaway tasks'}
        error={error}
        isEmpty={rows.length === 0}
        isLoading={isLoading}
        onEmptySecondaryAction={search ? () => setSearch('') : undefined}
        rowCount={rows.length}
        title="Putaway tasks"
        toolbar={<ScreenToolbar onSearchChange={setSearch} searchPlaceholder="Search by ID or status" searchValue={search} />}
      >
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Status</th>
              <th>Product</th>
              <th>Warehouse</th>
              <th>From</th>
              <th>To</th>
              <th className="text-right">Qty</th>
              <th>Created</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {rows.map((task) => (
              <tr key={task.id}>
                <td className="font-semibold text-warelyn-primary">
                  <Link to={`/putaway-tasks/${task.id}`}>#{task.id}</Link>
                </td>
                <td><StatusBadge status={task.status}>{task.status}</StatusBadge></td>
                <td>#{task.product_id}</td>
                <td>#{task.warehouse_id}</td>
                <td>#{task.from_location_id}</td>
                <td>{task.to_location_id ? `#${task.to_location_id}` : '-'}</td>
                <td className="number-cell">{task.quantity}</td>
                <td>{formatDate(task.created_at)}</td>
                <td>
                  <Link to={`/putaway-tasks/${task.id}`}>
                    <Button size="sm" variant="secondary">View</Button>
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </TableShell>
    </div>
  );
}

export function PutawayTaskDetailPage() {
  const { id } = useParams();
  const { accessToken } = useAuth();
  const navigate = useNavigate();
  const [task, setTask] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [isBusy, setIsBusy] = useState(false);
  const [pendingAction, setPendingAction] = useState(null);

  async function load() {
    setIsLoading(true);
    setError('');
    try {
      setTask(normalizePutawayTask(await getPutawayTask(accessToken, id)));
    } catch (e) {
      setError(e.message);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => { load(); }, [accessToken, id]);

  async function handleAction(action) {
    setIsBusy(true);
    setError('');
    try {
      await action();
      await load();
    } catch (e) {
      setError(e.message);
    } finally {
      setIsBusy(false);
    }
  }

  if (isLoading) return <LoadingState />;
  if (!task) return <ErrorState description={error || 'Putaway task not found.'} />;

  return (
    <div className="space-y-6">
      {error && <ErrorState description={error} />}
      <PageHeader
        kicker="Putaway Task"
        title={`Putaway #${task.id}`}
        description="Move stock from receiving location to storage location."
        backTo="/putaway-tasks"
      />

      <Card>
        <CardHeader title="Task Details" />
        <CardBody>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
              <div>
                <p className="text-xs text-warelyn-muted">Status</p>
              <StatusBadge status={task.status}>{task.status || '-'}</StatusBadge>
              </div>
            <div>
              <p className="text-xs text-warelyn-muted">Product ID</p>
              <p className="font-medium">#{String(task.product_id || '-')}</p>
            </div>
            <div>
              <p className="text-xs text-warelyn-muted">Warehouse ID</p>
              <p className="font-medium">#{String(task.warehouse_id || '-')}</p>
            </div>
            <div>
              <p className="text-xs text-warelyn-muted">Quantity</p>
              <p className="font-medium">{String(task.quantity || '-')}</p>
            </div>
            <div>
              <p className="text-xs text-warelyn-muted">From Location</p>
              <p className="font-medium">#{String(task.from_location_id || '-')}</p>
            </div>
            <div>
              <p className="text-xs text-warelyn-muted">To Location</p>
              <p className="font-medium">{task.to_location_id ? `#${String(task.to_location_id)}` : 'Not assigned'}</p>
            </div>
            {task.receipt_id && (
              <div>
                <p className="text-xs text-warelyn-muted">Receipt</p>
                <p className="font-medium">#{String(task.receipt_id)}</p>
              </div>
            )}
            <div>
              <p className="text-xs text-warelyn-muted">Created</p>
              <p className="font-medium">{formatDate(task.created_at)}</p>
            </div>
          </div>
        </CardBody>
      </Card>

      {task.status !== 'COMPLETED' && task.status !== 'CANCELLED' && (
        <div className="flex flex-wrap gap-2">
          {task.status === 'PENDING' && (
            <Button
              disabled={isBusy}
              variant="secondary"
              onClick={() => setPendingAction({
                label: 'Start task',
                description: 'Start this putaway task and mark it as in progress.',
                variant: 'secondary',
                run: () => startPutawayTask(accessToken, id),
              })}
            >
              <ArrowRight size={16} /> Start
            </Button>
          )}
          <Button
            disabled={isBusy}
            variant="accent"
            onClick={() => setPendingAction({
              label: 'Complete putaway',
              description: 'Complete this putaway task and post the workflow completion.',
              variant: 'accent',
              run: () => completePutawayTask(accessToken, id),
            })}
          >
            <CheckCircle2 size={16} /> Complete Putaway
          </Button>
          <Button
            disabled={isBusy}
            variant="danger"
            onClick={() => setPendingAction({
              label: 'Cancel task',
              description: 'Cancel this putaway task. This cannot be undone.',
              variant: 'danger',
              run: () => cancelPutawayTask(accessToken, id),
            })}
          >
            <XCircle size={16} /> Cancel
          </Button>
        </div>
      )}
      <ConfirmationModal
        open={Boolean(pendingAction)}
        title="Confirm putaway action"
        description={pendingAction?.description}
        confirmLabel={pendingAction?.label}
        variant={pendingAction?.variant ?? 'primary'}
        isLoading={isBusy}
        onCancel={() => setPendingAction(null)}
        onConfirm={async () => {
          const run = pendingAction?.run;
          setPendingAction(null);
          if (run) await handleAction(run);
        }}
      />
    </div>
  );
}
