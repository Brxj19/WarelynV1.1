import { useEffect, useState } from 'react';
import { BackButton } from '../components/ui/BackButton.jsx';
import { useNavigate } from 'react-router-dom';

import { PageHeader } from '../components/ui/PageHeader.jsx';
import { Button } from '../components/ui/Button.jsx';
import { Card, CardBody, CardHeader } from '../components/ui/Card.jsx';
import { ErrorState } from '../components/ui/ErrorState.jsx';
import { Input } from '../components/ui/Input.jsx';
import { LoadingState } from '../components/ui/LoadingState.jsx';
import { useAuth } from '../context/AuthContext.jsx';
import * as catalogService from '../services/catalogService.js';
import * as purchasingService from '../services/purchasingService.js';

const selectClass = 'block w-full rounded-lg border border-warelyn-border bg-white px-3 py-2.5 text-sm text-warelyn-text shadow-sm outline-none transition focus:border-warelyn-primary focus:ring-4 focus:ring-blue-900/10';

export function PurchaseOrderFormPage() {
  const { accessToken } = useAuth();
  const navigate = useNavigate();
  const [vendors, setVendors] = useState([]);
  const [products, setProducts] = useState([]);
  const [form, setForm] = useState({ vendor_id: '', po_number: '', order_date: new Date().toISOString().slice(0, 10), expected_date: '', notes: '' });
  const [items, setItems] = useState([{ product_id: '', ordered_quantity: '1', unit_cost: '0', notes: '' }]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    async function load() {
      setIsLoading(true);
      try {
        const [vendorRows, productRows] = await Promise.all([catalogService.listVendors(accessToken), catalogService.listProducts(accessToken)]);
        setVendors(vendorRows);
        setProducts(productRows);
      } catch (loadError) {
        setError(loadError.message);
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, [accessToken]);

  function updateItem(index, key, value) {
    setItems((current) => current.map((item, itemIndex) => (itemIndex === index ? { ...item, [key]: value } : item)));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setIsSaving(true);
    setError('');
    try {
      const payload = {
        ...Object.fromEntries(Object.entries(form).filter(([, value]) => value !== '')),
        vendor_id: Number(form.vendor_id),
        items: items.filter((item) => item.product_id).map((item) => ({ ...item, product_id: Number(item.product_id) })),
      };
      const order = await purchasingService.createPurchaseOrder(accessToken, payload);
      navigate(`/purchases/${order.id}`);
    } catch (saveError) {
      setError(saveError.message);
    } finally {
      setIsSaving(false);
    }
  }

  if (isLoading) return <LoadingState />;

  return (
    <div className="space-y-6">
      <BackButton to="/purchases" />
      <PageHeader backTo="/purchases" description="Create a draft purchase order. Stock is not changed until a receipt is committed." kicker="Purchasing" title="New purchase order" />
      {error ? <ErrorState description={error} /> : null}
      <form className="space-y-6" onSubmit={handleSubmit}>
        <Card>
          <CardHeader><h2 className="text-lg font-semibold text-warelyn-text">Order details</h2></CardHeader>
          <CardBody className="grid gap-4 md:grid-cols-2">
            <label className="block"><span className="mb-2 block text-sm font-medium text-warelyn-text">Vendor</span><select className={selectClass} required value={form.vendor_id} onChange={(event) => setForm((current) => ({ ...current, vendor_id: event.target.value }))}><option value="">Select vendor</option>{vendors.map((vendor) => <option key={vendor.id} value={vendor.id}>{vendor.name}</option>)}</select></label>
            <Input label="PO number" required value={form.po_number} onChange={(event) => setForm((current) => ({ ...current, po_number: event.target.value }))} />
            <Input label="Order date" required type="date" value={form.order_date} onChange={(event) => setForm((current) => ({ ...current, order_date: event.target.value }))} />
            <Input label="Expected date" type="date" value={form.expected_date} onChange={(event) => setForm((current) => ({ ...current, expected_date: event.target.value }))} />
            <Input className="md:col-span-2" label="Notes" value={form.notes} onChange={(event) => setForm((current) => ({ ...current, notes: event.target.value }))} />
          </CardBody>
        </Card>
        <Card>
          <CardHeader className="flex items-center justify-between"><h2 className="text-lg font-semibold text-warelyn-text">Product lines</h2><Button variant="secondary" onClick={() => setItems((current) => [...current, { product_id: '', ordered_quantity: '1', unit_cost: '0', notes: '' }])}>Add line</Button></CardHeader>
          <CardBody className="space-y-4">
            {items.map((item, index) => (
              <div className="grid gap-3 rounded-xl border border-warelyn-border p-4 md:grid-cols-[2fr_1fr_1fr_auto]" key={index}>
                <label className="block"><span className="mb-2 block text-sm font-medium text-warelyn-text">Product</span><select className={selectClass} required value={item.product_id} onChange={(event) => updateItem(index, 'product_id', event.target.value)}><option value="">Select product</option>{products.map((product) => <option key={product.id} value={product.id}>{product.name} ({product.sku})</option>)}</select></label>
                <Input label="Quantity" min="0.001" required step="0.001" type="number" value={item.ordered_quantity} onChange={(event) => updateItem(index, 'ordered_quantity', event.target.value)} />
                <Input label="Unit cost" min="0" required step="0.01" type="number" value={item.unit_cost} onChange={(event) => updateItem(index, 'unit_cost', event.target.value)} />
                <div className="flex items-end"><Button disabled={items.length === 1} variant="secondary" onClick={() => setItems((current) => current.filter((_, itemIndex) => itemIndex !== index))}>Remove</Button></div>
              </div>
            ))}
          </CardBody>
        </Card>
        <div className="sticky-form-footer">
          <div className="workflow-helper-panel max-w-xl">
            <h3>What happens next?</h3>
            <p>This saves a draft purchase order only. Receiving and stock increase happen later through the receipt workflow.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button onClick={() => navigate('/purchases')} type="button" variant="ghost">Cancel</Button>
            <Button disabled={isSaving} type="submit">{isSaving ? 'Creating...' : 'Create purchase order'}</Button>
          </div>
        </div>
      </form>
    </div>
  );
}
