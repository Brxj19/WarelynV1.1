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
import * as catalogService from '../services/catalogService.js';
import * as fulfillmentService from '../services/fulfillmentService.js';
import * as salesService from '../services/salesService.js';

const canWrite = new Set(['TENANT_ADMIN', 'INVENTORY_MANAGER', 'SALES_STAFF']);

export function SalesPackagePage() {
  const { id } = useParams();
  const { accessToken, user } = useAuth();
  const [order, setOrder] = useState(null);
  const [pickTasks, setPickTasks] = useState([]);
  const [packages, setPackages] = useState([]);
  const [productsById, setProductsById] = useState({});
  const [packageNumber, setPackageNumber] = useState(`PKG-${Date.now()}`);
  const [selectedItems, setSelectedItems] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');
  const mayWrite = canWrite.has(user?.role);

  const pickedItems = pickTasks
    .flatMap((task) => task.items.map((item) => ({ ...item, pick_number: task.pick_number })))
    .filter((item) => item.status === 'PICKED');

  async function load() {
    setIsLoading(true);
    setError('');
    try {
      const [orderRow, taskRows, packageRows, productRows] = await Promise.all([
        salesService.getSalesOrder(accessToken, id),
        fulfillmentService.listPickTasksForOrder(accessToken, id),
        fulfillmentService.listPackagesForOrder(accessToken, id),
        catalogService.listProducts(accessToken),
      ]);
      setOrder(orderRow);
      setPickTasks(taskRows);
      setPackages(packageRows);
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

  function toggleItem(itemId) {
    setSelectedItems((current) =>
      current.includes(itemId) ? current.filter((idValue) => idValue !== itemId) : [...current, itemId],
    );
  }

  async function createPackage(event) {
    event.preventDefault();
    setIsSaving(true);
    setError('');
    try {
      await fulfillmentService.createPackage(accessToken, id, {
        package_number: packageNumber,
        pick_task_item_ids: selectedItems,
      });
      setPackageNumber(`PKG-${Date.now()}`);
      setSelectedItems([]);
      await load();
    } catch (saveError) {
      setError(saveError.message);
    } finally {
      setIsSaving(false);
    }
  }

  if (isLoading) return <LoadingState />;
  if (!order) return <ErrorState description={error || 'Sales order not found.'} />;

  const selectedQuantity = pickedItems
    .filter((item) => selectedItems.includes(item.id))
    .reduce((sum, item) => sum + Number(item.picked_quantity), 0);

  return (
    <div className="space-y-6">
      <BackButton to="/packages" />
      <PageHeader
        actions={
          mayWrite ? (
            <Button disabled={isSaving || selectedItems.length === 0} form="create-package-form" type="submit">
              Create package
            </Button>
          ) : null
        }
        backTo="/sales"
        description="Packages group already-picked items into shipping-ready units. Packing does not create ledger entries on its own."
        kicker="Packing"
        status={<StatusBadge status={order.status}>{order.status}</StatusBadge>}
        title={`Package ${order.order_number}`}
      />
      {error ? <ErrorState description={error} /> : null}

      <div className="record-summary-grid">
        <Card className="record-summary-card">
          <CardBody>
            <span>Picked lines</span>
            <strong>{pickedItems.length}</strong>
            <small>Available for package selection</small>
          </CardBody>
        </Card>
        <Card className="record-summary-card">
          <CardBody>
            <span>Selected lines</span>
            <strong>{selectedItems.length}</strong>
            <small>Ready for the next package</small>
          </CardBody>
        </Card>
        <Card className="record-summary-card">
          <CardBody>
            <span>Selected qty</span>
            <strong>{formatDecimal(selectedQuantity)}</strong>
            <small>Picked quantity in selection</small>
          </CardBody>
        </Card>
        <Card className="record-summary-card">
          <CardBody>
            <span>Packages</span>
            <strong>{packages.length}</strong>
            <small>Document records on this order</small>
          </CardBody>
        </Card>
      </div>

      {mayWrite ? (
        <form className="space-y-6" id="create-package-form" onSubmit={createPackage}>
          <Card>
            <CardHeader>
              <h2 className="text-lg font-semibold text-warelyn-text">Create package</h2>
            </CardHeader>
            <CardBody className="space-y-4">
              <Input label="Package number" required value={packageNumber} onChange={(event) => setPackageNumber(event.target.value)} />
              {pickedItems.length === 0 ? (
                <EmptyState title="No picked items" description="Pick items before creating a package." />
              ) : (
                <div className="grid gap-3 md:grid-cols-2">
                  {pickedItems.map((item) => {
                    const product = productsById[item.product_id];
                    return (
                      <label className="flex cursor-pointer items-start gap-3 rounded-xl border border-warelyn-border p-4" key={item.id}>
                        <input checked={selectedItems.includes(item.id)} type="checkbox" onChange={() => toggleItem(item.id)} />
                        <span>
                          <span className="block font-semibold text-warelyn-text">{product?.name ?? `Product #${item.product_id}`}</span>
                          <span className="mt-1 block text-xs text-warelyn-muted">SKU {product?.sku ?? '-'} • Pick {item.pick_number}</span>
                          <span className="mt-1 block text-sm text-warelyn-muted">Picked quantity {formatDecimal(item.picked_quantity)}</span>
                        </span>
                      </label>
                    );
                  })}
                </div>
              )}
            </CardBody>
          </Card>
        </form>
      ) : null}

      <TableShell
        description="Existing packages linked to this sales order."
        isEmpty={packages.length === 0}
        rowCount={packages.length}
        title="Packages"
      >
        <table>
          <thead>
            <tr>
              <th>Package</th>
              <th>Status</th>
              <th className="text-right">Items</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {packages.map((pkg) => (
              <tr key={pkg.id}>
                <td>
                  <div className="space-y-1">
                    <span className="font-semibold text-warelyn-text">{pkg.package_number}</span>
                    <p className="text-xs text-warelyn-muted">Sales order {order.order_number}</p>
                  </div>
                </td>
                <td><StatusBadge status={pkg.status}>{pkg.status}</StatusBadge></td>
                <td className="number-cell">{pkg.items.length}</td>
                <td>
                  <Link className="text-sm font-semibold text-warelyn-primary" to={`/packages/${pkg.id}`}>
                    Open package
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
