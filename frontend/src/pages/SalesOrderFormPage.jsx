import { useEffect, useState } from 'react';
import { BackButton } from '../components/ui/BackButton.jsx';
import { useNavigate, useParams } from 'react-router-dom';

import { PageHeader } from '../components/ui/PageHeader.jsx';
import { Button } from '../components/ui/Button.jsx';
import { Card, CardBody, CardHeader } from '../components/ui/Card.jsx';
import { ErrorState } from '../components/ui/ErrorState.jsx';
import { Input } from '../components/ui/Input.jsx';
import { LoadingState } from '../components/ui/LoadingState.jsx';
import { useAuth } from '../context/AuthContext.jsx';
import * as catalogService from '../services/catalogService.js';
import * as inventoryService from '../services/inventoryService.js';
import * as salesService from '../services/salesService.js';

const selectClass = 'block w-full rounded-lg border border-warelyn-border bg-white px-3 py-2.5 text-sm text-warelyn-text shadow-sm outline-none transition focus:border-warelyn-primary focus:ring-4 focus:ring-blue-900/10';

export function SalesOrderFormPage() {
  const { id } = useParams();
  const isEdit = Boolean(id);
  const { accessToken } = useAuth();
  const navigate = useNavigate();
  const [customers, setCustomers] = useState([]);
  const [products, setProducts] = useState([]);
  const [stockByProduct, setStockByProduct] = useState({});
  const [form, setForm] = useState({
    customer_id: '',
    order_number: `SO-${Date.now()}`,
    order_date: new Date().toISOString().slice(0, 10),
    expected_ship_date: '',
    notes: '',
  });
  const [items, setItems] = useState([{ product_id: '', ordered_quantity: '1', unit_price: '0', notes: '' }]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    async function load() {
      setIsLoading(true);
      try {
        const [customerRows, productRows, stockRows] = await Promise.all([
          catalogService.listCustomers(accessToken),
          catalogService.listProducts(accessToken),
          inventoryService.listStock(accessToken),
        ]);
        setCustomers(customerRows);
        const availableByProduct = {};
        for (const row of stockRows) {
          availableByProduct[row.product_id] = (availableByProduct[row.product_id] || 0) + Number(row.quantity_available);
        }
        setStockByProduct(availableByProduct);
        const inStockProducts = productRows.filter((p) => (availableByProduct[p.id] || 0) > 0);
        setProducts(isEdit ? productRows : inStockProducts);
        if (isEdit) {
          const order = await salesService.getSalesOrder(accessToken, id);
          if (order.status !== 'DRAFT') {
            navigate(`/sales/${id}`, { replace: true });
            return;
          }
          setForm({
            customer_id: String(order.customer_id),
            order_number: order.order_number,
            order_date: order.order_date,
            expected_ship_date: order.expected_ship_date || '',
            notes: order.notes || '',
          });
          setItems(order.items.map((item) => ({
            product_id: String(item.product_id),
            ordered_quantity: String(item.ordered_quantity),
            unit_price: String(item.unit_price),
            notes: item.notes || '',
          })));
        }
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
      current.map((item, itemIndex) => (itemIndex === index ? { ...item, [key]: value } : item)),
    );
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setIsSaving(true);
    setError('');
    try {
      const payload = {
        ...Object.fromEntries(Object.entries(form).filter(([, value]) => value !== '')),
        customer_id: Number(form.customer_id),
        items: items
          .filter((item) => item.product_id)
          .map((item) => ({ ...item, product_id: Number(item.product_id) })),
      };
      let order;
      if (isEdit) {
        order = await salesService.updateSalesOrder(accessToken, id, payload);
      } else {
        order = await salesService.createSalesOrder(accessToken, payload);
      }
      navigate(`/sales/${order.id}`);
    } catch (saveError) {
      setError(saveError.message);
    } finally {
      setIsSaving(false);
    }
  }

  if (isLoading) return <LoadingState />;

  return (
    <div className="space-y-6">
      <BackButton to={isEdit ? `/sales/${id}` : '/sales'} />
      <PageHeader
        backTo={isEdit ? `/sales/${id}` : '/sales'}
        description={isEdit ? 'Edit this draft sales order. Changes are saved when you click Update.' : 'Create a draft sales order first. Stock is only reserved later during confirmation with warehouse and location allocation.'}
        kicker="Sales"
        title={isEdit ? `Edit ${form.order_number || 'sales order'}` : 'New sales order'}
      />
      {error ? <ErrorState description={error} /> : null}
      <form className="space-y-6" onSubmit={handleSubmit}>
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-warelyn-text">Customer and document details</h2>
          </CardHeader>
          <CardBody className="grid gap-4 md:grid-cols-2">
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-warelyn-text">Customer *</span>
              <select
                className={selectClass}
                required
                value={form.customer_id}
                onChange={(event) => setForm((current) => ({ ...current, customer_id: event.target.value }))}
              >
                <option value="">Select customer</option>
                {customers.map((customer) => (
                  <option key={customer.id} value={customer.id}>
                    {customer.name}
                  </option>
                ))}
              </select>
            </label>
            <Input
              label="Order number"
              required
              value={form.order_number}
              onChange={(event) => setForm((current) => ({ ...current, order_number: event.target.value }))}
            />
            <Input
              label="Order date"
              required
              type="date"
              value={form.order_date}
              onChange={(event) => setForm((current) => ({ ...current, order_date: event.target.value }))}
            />
            <Input
              label="Expected ship date"
              type="date"
              value={form.expected_ship_date}
              onChange={(event) => setForm((current) => ({ ...current, expected_ship_date: event.target.value }))}
            />
            <Input
              className="md:col-span-2"
              label="Notes"
              value={form.notes}
              onChange={(event) => setForm((current) => ({ ...current, notes: event.target.value }))}
            />
          </CardBody>
        </Card>

        <Card>
          <CardHeader className="flex items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-warelyn-text">Line items</h2>
              <p className="mt-1 text-sm text-warelyn-muted">Add sellable catalog items. Allocation and reservation happen later during confirmation.</p>
            </div>
            <Button
              type="button"
              variant="secondary"
              onClick={() => setItems((current) => [...current, { product_id: '', ordered_quantity: '1', unit_price: '0', notes: '' }])}
            >
              Add line
            </Button>
          </CardHeader>
          <CardBody className="space-y-4">
            {items.map((item, index) => {
              const product = products.find((entry) => String(entry.id) === String(item.product_id));
              return (
                <div className="grid gap-3 rounded-xl border border-warelyn-border p-4 md:grid-cols-2 xl:grid-cols-[minmax(0,2fr)_140px_160px_auto]" key={index}>
                  <label className="block">
                    <span className="mb-2 block text-sm font-medium text-warelyn-text">Product *</span>
                    <select
                      className={selectClass}
                      required
                      value={item.product_id}
                      onChange={(event) => updateItem(index, 'product_id', event.target.value)}
                    >
                      <option value="">Select product</option>
                      {products.map((productOption) => (
                        <option key={productOption.id} value={productOption.id}>
                          {productOption.name} ({productOption.sku}) — Avail: {stockByProduct[productOption.id] ?? 0}
                        </option>
                      ))}
                    </select>
                    <p className="mt-1.5 text-xs text-warelyn-muted">
                      {product?.track_serial
                        ? 'Serial-tracked products require reservation-aware confirmation before they can be picked.'
                        : product?.track_batch || product?.track_expiry
                          ? 'Batch and expiry tracking are preserved downstream in picking and fulfillment.'
                          : 'Standard inventory item.'}
                    </p>
                  </label>
                  <Input
                    label="Quantity *"
                    min="0.001"
                    required
                    step="0.001"
                    type="number"
                    value={item.ordered_quantity}
                    onChange={(event) => updateItem(index, 'ordered_quantity', event.target.value)}
                  />
                  <Input
                    label="Unit price *"
                    min="0"
                    required
                    step="0.01"
                    type="number"
                    value={item.unit_price}
                    onChange={(event) => updateItem(index, 'unit_price', event.target.value)}
                  />
                  <div className="flex items-end">
                    <Button
                      disabled={items.length === 1}
                      type="button"
                      variant="ghost"
                      onClick={() => setItems((current) => current.filter((_, itemIndex) => itemIndex !== index))}
                    >
                      Remove
                    </Button>
                  </div>
                  <Input
                    className="md:col-span-2 xl:col-span-4"
                    label="Line notes"
                    value={item.notes}
                    onChange={(event) => updateItem(index, 'notes', event.target.value)}
                  />
                </div>
              );
            })}
          </CardBody>
        </Card>

        <div className="sticky-form-footer">
          <div className="workflow-helper-panel max-w-xl">
            <h3>What happens next?</h3>
            <p>
              {isEdit ? 'Your changes will be saved to the draft. Confirm the order when ready to reserve stock.' : 'Saving creates a draft sales order only. After creation, the document still needs confirmation so the backend can reserve stock against warehouse and location allocations.'}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button onClick={() => navigate(isEdit ? `/sales/${id}` : '/sales')} type="button" variant="ghost">
              Cancel
            </Button>
            <Button disabled={isSaving} type="submit">
              {isSaving ? 'Saving...' : isEdit ? 'Update sales order' : 'Create sales order'}
            </Button>
          </div>
        </div>
      </form>
    </div>
  );
}
