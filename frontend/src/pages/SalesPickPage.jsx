import { useEffect, useState } from 'react';
import { BackButton } from '../components/ui/BackButton.jsx';
import { Link, useParams } from 'react-router-dom';

import { StatusBadge } from '../components/ui/Badge.jsx';
import { PageHeader } from '../components/ui/PageHeader.jsx';
import { Button } from '../components/ui/Button.jsx';
import { Card, CardBody, CardHeader } from '../components/ui/Card.jsx';
import { EmptyState } from '../components/ui/EmptyState.jsx';
import { ErrorState } from '../components/ui/ErrorState.jsx';
import { Input } from '../components/ui/Input.jsx';
import { LoadingState } from '../components/ui/LoadingState.jsx';
import { TableShell } from '../components/ui/TableShell.jsx';
import { formatDecimal } from '../utils/formatters.js';
import { useAuth } from '../context/AuthContext.jsx';
import * as fulfillmentService from '../services/fulfillmentService.js';
import * as salesService from '../services/salesService.js';

const canWrite = new Set(['TENANT_ADMIN', 'INVENTORY_MANAGER', 'SALES_STAFF']);

export function SalesPickPage() {
  const { id } = useParams();
  const { accessToken, user } = useAuth();
  const [order, setOrder] = useState(null);
  const [pickTasks, setPickTasks] = useState([]);
  const [pickNumber, setPickNumber] = useState(`PICK-${Date.now()}`);
  const [notes, setNotes] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');
  const mayWrite = canWrite.has(user?.role);

  async function load() {
    setIsLoading(true);
    setError('');
    try {
      const [orderRow, taskRows] = await Promise.all([
        salesService.getSalesOrder(accessToken, id),
        fulfillmentService.listPickTasksForOrder(accessToken, id),
      ]);
      setOrder(orderRow);
      setPickTasks(taskRows);
    } catch (loadError) {
      setError(loadError.message);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [accessToken, id]);

  async function createTask(event) {
    event.preventDefault();
    setIsSaving(true);
    setError('');
    try {
      await fulfillmentService.createPickTask(accessToken, id, { pick_number: pickNumber, notes: notes || null });
      setPickNumber(`PICK-${Date.now()}`);
      setNotes('');
      await load();
    } catch (saveError) {
      setError(saveError.message);
    } finally {
      setIsSaving(false);
    }
  }

  if (isLoading) return <LoadingState />;
  if (!order) return <ErrorState description={error || 'Sales order not found.'} />;

  const reservedQty = order.items.reduce((sum, item) => sum + Number(item.reserved_quantity), 0);
  const fulfilledQty = order.items.reduce((sum, item) => sum + Number(item.fulfilled_quantity), 0);

  return (
    <div className="space-y-6">
      <BackButton to="/pick-tasks" />
      <PageHeader
        actions={
          mayWrite && ['CONFIRMED', 'PARTIALLY_FULFILLED'].includes(order.status) ? (
            <Button form="create-pick-task" type="submit">
              Create pick task
            </Button>
          ) : null
        }
        backTo="/sales"
        description="Create and manage operational pick work from active reservations. Picking records movement of work, not stock deduction."
        kicker="Sales picking"
        status={<StatusBadge status={order.status}>{order.status}</StatusBadge>}
        title={`Pick ${order.order_number}`}
      />
      {error ? <ErrorState description={error} /> : null}

      <div className="record-summary-grid">
        <Card className="record-summary-card">
          <CardBody>
            <span>Order lines</span>
            <strong>{order.items.length}</strong>
            <small>Reservable document lines</small>
          </CardBody>
        </Card>
        <Card className="record-summary-card">
          <CardBody>
            <span>Reserved qty</span>
            <strong>{formatDecimal(reservedQty)}</strong>
            <small>Allocated by backend confirmation</small>
          </CardBody>
        </Card>
        <Card className="record-summary-card">
          <CardBody>
            <span>Fulfilled qty</span>
            <strong>{formatDecimal(fulfilledQty)}</strong>
            <small>Already deducted downstream</small>
          </CardBody>
        </Card>
        <Card className="record-summary-card">
          <CardBody>
            <span>Pick tasks</span>
            <strong>{pickTasks.length}</strong>
            <small>Operational queue items</small>
          </CardBody>
        </Card>
      </div>

      {mayWrite && ['CONFIRMED', 'PARTIALLY_FULFILLED'].includes(order.status) ? (
        <form className="space-y-6" id="create-pick-task" onSubmit={createTask}>
          <Card>
            <CardHeader>
              <h2 className="text-lg font-semibold text-warelyn-text">Create pick task</h2>
            </CardHeader>
            <CardBody className="grid gap-4 md:grid-cols-[1fr_1fr]">
              <Input label="Pick number" required value={pickNumber} onChange={(event) => setPickNumber(event.target.value)} />
              <Input label="Notes" value={notes} onChange={(event) => setNotes(event.target.value)} />
            </CardBody>
          </Card>
        </form>
      ) : null}

      <TableShell
        description="Active pick tasks linked to this sales order."
        isEmpty={pickTasks.length === 0}
        rowCount={pickTasks.length}
        title="Pick task queue"
      >
        <table>
          <thead>
            <tr>
              <th>Pick task</th>
              <th>Status</th>
              <th className="text-right">Items</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {pickTasks.map((task) => (
              <tr key={task.id}>
                <td>
                  <div className="space-y-1">
                    <span className="font-semibold text-warelyn-text">{task.pick_number}</span>
                    <p className="text-xs text-warelyn-muted">Sales order {order.order_number}</p>
                  </div>
                </td>
                <td><StatusBadge status={task.status}>{task.status}</StatusBadge></td>
                <td className="number-cell">{task.items.length}</td>
                <td>
                  <Link className="text-sm font-semibold text-warelyn-primary" to={`/pick-tasks/${task.id}`}>
                    Open task
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
