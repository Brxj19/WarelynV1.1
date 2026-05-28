import { ArrowRight, CheckCircle2, Package, XCircle } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { Button } from '../components/ui/Button.jsx';
import { Card, CardBody, CardHeader } from '../components/ui/Card.jsx';
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

export function PutawayTasksPage() {
  const { accessToken } = useAuth();
  const [tasks, setTasks] = useState([]);
  const [search, setSearch] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    listPutawayTasks(accessToken)
      .then(setTasks)
      .catch((e) => setError(e.message))
      .finally(() => setIsLoading(false));
  }, [accessToken]);

  const rows = search
    ? tasks.filter((t) => `${t.id} ${t.status} ${t.product_id}`.toLowerCase().includes(search.toLowerCase()))
    : tasks;

  return (
    <div className="space-y-6">
      <PageHeader kicker="Warehousing" title="Putaway Tasks" description="Move received stock from receiving docks to storage locations." />
      <TableShell
        description={`${rows.length} putaway task(s)`}
        emptyDescription={search ? 'No tasks match your filter.' : 'No putaway tasks created yet.'}
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
                  <a href={`/putaway-tasks/${task.id}`}>#{task.id}</a>
                </td>
                <td><StatusBadge status={task.status}>{task.status}</StatusBadge></td>
                <td>#{task.product_id}</td>
                <td>#{task.warehouse_id}</td>
                <td>#{task.from_location_id}</td>
                <td>{task.to_location_id ? `#${task.to_location_id}` : '-'}</td>
                <td className="number-cell">{task.quantity}</td>
                <td>{formatDate(task.created_at)}</td>
                <td>
                  <a href={`/putaway-tasks/${task.id}`}>
                    <Button size="sm" variant="secondary">View</Button>
                  </a>
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

  async function load() {
    setIsLoading(true);
    setError('');
    try {
      setTask(await getPutawayTask(accessToken, id));
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
              <StatusBadge status={task.status}>{task.status}</StatusBadge>
            </div>
            <div>
              <p className="text-xs text-warelyn-muted">Product ID</p>
              <p className="font-medium">#{task.product_id}</p>
            </div>
            <div>
              <p className="text-xs text-warelyn-muted">Warehouse ID</p>
              <p className="font-medium">#{task.warehouse_id}</p>
            </div>
            <div>
              <p className="text-xs text-warelyn-muted">Quantity</p>
              <p className="font-medium">{task.quantity}</p>
            </div>
            <div>
              <p className="text-xs text-warelyn-muted">From Location</p>
              <p className="font-medium">#{task.from_location_id}</p>
            </div>
            <div>
              <p className="text-xs text-warelyn-muted">To Location</p>
              <p className="font-medium">{task.to_location_id ? `#${task.to_location_id}` : 'Not assigned'}</p>
            </div>
            {task.receipt_id && (
              <div>
                <p className="text-xs text-warelyn-muted">Receipt</p>
                <p className="font-medium">#{task.receipt_id}</p>
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
            <Button disabled={isBusy} variant="secondary" onClick={() => handleAction(() => startPutawayTask(accessToken, id))}>
              <ArrowRight size={16} /> Start
            </Button>
          )}
          <Button disabled={isBusy} variant="accent" onClick={() => handleAction(() => completePutawayTask(accessToken, id))}>
            <CheckCircle2 size={16} /> Complete Putaway
          </Button>
          <Button disabled={isBusy} variant="danger" onClick={() => handleAction(() => cancelPutawayTask(accessToken, id))}>
            <XCircle size={16} /> Cancel
          </Button>
        </div>
      )}
    </div>
  );
}
