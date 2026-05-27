import { Download, Plus, Upload } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { BarcodeInput } from '../components/forms/BarcodeInput.jsx';
import { PageHeader } from '../components/ui/PageHeader.jsx';
import { ScreenToolbar } from '../components/ui/ScreenToolbar.jsx';
import { StatusBadge } from '../components/ui/Badge.jsx';
import { Button } from '../components/ui/Button.jsx';
import { Card, CardBody, CardHeader } from '../components/ui/Card.jsx';
import { ErrorState } from '../components/ui/ErrorState.jsx';
import { Input } from '../components/ui/Input.jsx';
import { LoadingState } from '../components/ui/LoadingState.jsx';
import { PhoneInput } from '../components/ui/PhoneInput.jsx';
import { SortableHeader } from '../components/ui/SortableHeader.jsx';
import { TableShell } from '../components/ui/TableShell.jsx';
import { emptyStateIllustrations } from '../lib/emptyStates.js';
import { formatMoney } from '../utils/formatters.js';
import { getNextSort, sortRows } from '../utils/table.js';
import { useAuth } from '../context/AuthContext.jsx';
import { useTenantSettings } from '../context/TenantSettingsContext.jsx';
import * as catalogService from '../services/catalogService.js';
import { MasterDataFormPage, MasterDataListPage } from './MasterDataPage.jsx';

const canWrite = new Set(['TENANT_ADMIN', 'INVENTORY_MANAGER']);

// Adapter to use PhoneInput within MasterDataFormPage's customInputs pattern
function PhoneFieldInput({ label, value, onChange }) {
  return (
    <PhoneInput
      label={label}
      value={value}
      onChange={(val) => onChange({ target: { value: val } })}
    />
  );
}

const partyCustomInputs = { phone: PhoneFieldInput };

const nameDescriptionFields = [
  { name: 'name', label: 'Name', required: true },
  { name: 'description', label: 'Description' },
];

const partyFields = [
  { name: 'name', label: 'Name', required: true },
  { name: 'email', label: 'Email', type: 'email' },
  { name: 'phone', label: 'Phone' },
  { name: 'gst_number', label: 'GST Number' },
];

const productTrackingOptions = [
  ['ALL', 'All tracking'],
  ['STANDARD', 'Standard'],
  ['BATCH', 'Batch'],
  ['EXPIRY', 'Expiry'],
  ['SERIAL', 'Serial'],
];

export function ProductsPage() {
  const { accessToken, user } = useAuth();
  const { currency } = useTenantSettings();
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [brands, setBrands] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('ALL');
  const [brandFilter, setBrandFilter] = useState('ALL');
  const [trackingFilter, setTrackingFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [sortState, setSortState] = useState({ key: 'name', direction: 'asc' });
  const mayWrite = canWrite.has(user?.role);

  async function exportProducts() {
    const blob = await catalogService.downloadProductsCsv(accessToken, search);
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = 'products.csv';
    anchor.click();
    URL.revokeObjectURL(url);
  }

  useEffect(() => {
    async function load() {
      setIsLoading(true);
      setError('');
      try {
        const [productRows, categoryRows, brandRows] = await Promise.all([
          catalogService.listProducts(accessToken),
          catalogService.listCategories(accessToken),
          catalogService.listBrands(accessToken),
        ]);
        setProducts(productRows);
        setCategories(categoryRows);
        setBrands(brandRows);
      } catch (loadError) {
        setError(loadError.message);
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, [accessToken]);

  const categoriesById = useMemo(() => Object.fromEntries(categories.map((row) => [row.id, row])), [categories]);
  const brandsById = useMemo(() => Object.fromEntries(brands.map((row) => [row.id, row])), [brands]);

  const filteredProducts = useMemo(() => {
    return products.filter((product) => {
      if (categoryFilter !== 'ALL' && String(product.category_id ?? '') !== categoryFilter) return false;
      if (brandFilter !== 'ALL' && String(product.brand_id ?? '') !== brandFilter) return false;
      if (statusFilter !== 'ALL' && product.status !== statusFilter) return false;
      if (trackingFilter !== 'ALL' && trackingType(product) !== trackingFilter) return false;
      if (!search) return true;
      const value = search.toLowerCase();
      return `${product.name} ${product.sku ?? ''} ${product.barcode ?? ''}`.toLowerCase().includes(value);
    });
  }, [brandFilter, categoryFilter, products, search, statusFilter, trackingFilter]);
  const sortedProducts = useMemo(
    () =>
      sortRows(filteredProducts, sortState, {
        name: { type: 'text', accessor: (product) => product.name },
        sku: { type: 'text', accessor: (product) => product.sku },
        barcode: { type: 'text', accessor: (product) => product.barcode },
        category: { type: 'text', accessor: (product) => categoriesById[product.category_id]?.name ?? '' },
        brand: { type: 'text', accessor: (product) => brandsById[product.brand_id]?.name ?? '' },
        tracking: { type: 'text', accessor: trackingLabel },
        reorder_level: { type: 'number', accessor: (product) => product.reorder_level },
        cost_price: { type: 'number', accessor: (product) => product.cost_price },
        status: { type: 'text', accessor: (product) => product.status },
      }),
    [brandsById, categoriesById, filteredProducts, sortState],
  );

  const activeFilters = [
    search
      ? {
          key: 'search',
          label: `Search: ${search}`,
          onRemove: () => setSearch(''),
        }
      : null,
    categoryFilter !== 'ALL'
      ? {
          key: 'category',
          label: `Category: ${categoriesById[Number(categoryFilter)]?.name ?? categoryFilter}`,
          onRemove: () => setCategoryFilter('ALL'),
        }
      : null,
    brandFilter !== 'ALL'
      ? {
          key: 'brand',
          label: `Brand: ${brandsById[Number(brandFilter)]?.name ?? brandFilter}`,
          onRemove: () => setBrandFilter('ALL'),
        }
      : null,
    trackingFilter !== 'ALL'
      ? { key: 'tracking', label: `Tracking: ${productTrackingOptions.find(([value]) => value === trackingFilter)?.[1] ?? trackingFilter}`, onRemove: () => setTrackingFilter('ALL') }
      : null,
    statusFilter !== 'ALL'
      ? { key: 'status', label: `Status: ${statusFilter}`, onRemove: () => setStatusFilter('ALL') }
      : null,
  ].filter(Boolean);
  const hasActiveFilters = activeFilters.length > 0;

  return (
    <div className="space-y-6">
      <PageHeader
        actions={
          mayWrite ? (
            <>
              <Button variant="secondary" onClick={exportProducts}>
                <Download size={16} />
                Export CSV
              </Button>
              <Link to="/catalog/products/import">
                <Button variant="secondary">
                  <Upload size={16} />
                  Import Products
                </Button>
              </Link>
              <Link to="/catalog/products/new">
                <Button>
                  <Plus size={16} />
                  Product
                </Button>
              </Link>
            </>
          ) : null
        }
        kicker="Catalog"
        title="Products"
        description="Manage product records, SKUs, barcode tracking, and inventory configuration."
      />
      <TableShell
        description={`${sortedProducts.length} product record(s) in view`}
        emptyAction={
          !hasActiveFilters && mayWrite ? (
            <div className="flex flex-wrap gap-2">
              <Link to="/catalog/products/import">
                <Button variant="secondary">Import Products</Button>
              </Link>
              <Link to="/catalog/products/new">
                <Button>Create product</Button>
              </Link>
            </div>
          ) : null
        }
        emptyDescription={hasActiveFilters ? 'Try changing the search keyword, category, warehouse, or stock filter.' : 'Add your first product to start managing stock, pricing, and inventory movement.'}
        emptyIllustration={hasActiveFilters ? emptyStateIllustrations.noResult : emptyStateIllustrations.products}
        emptySecondaryActionLabel={hasActiveFilters ? 'Clear filters' : undefined}
        emptyTitle={hasActiveFilters ? 'No matching products found' : 'No products added yet'}
        error={error}
        isEmpty={sortedProducts.length === 0}
        isLoading={isLoading}
        onEmptySecondaryAction={hasActiveFilters ? () => { setSearch(''); setCategoryFilter('ALL'); setBrandFilter('ALL'); setTrackingFilter('ALL'); setStatusFilter('ALL'); } : undefined}
        rowCount={sortedProducts.length}
        title="Product records"
        toolbar={
          <ScreenToolbar
            activeFilters={activeFilters}
            onReset={
              hasActiveFilters
                ? () => {
                    setSearch('');
                    setCategoryFilter('ALL');
                    setBrandFilter('ALL');
                    setTrackingFilter('ALL');
                    setStatusFilter('ALL');
                  }
                : undefined
            }
            onSearchChange={setSearch}
            searchPlaceholder="Search by product name, SKU, or barcode"
            searchValue={search}
          >
            <div className="flex flex-wrap gap-2">
              <SelectField label="Category" onChange={setCategoryFilter} options={[['ALL', 'All categories'], ...categories.map((row) => [String(row.id), row.name])]} value={categoryFilter} />
              <SelectField label="Brand" onChange={setBrandFilter} options={[['ALL', 'All brands'], ...brands.map((row) => [String(row.id), row.name])]} value={brandFilter} />
              <SelectField label="Tracking" onChange={setTrackingFilter} options={productTrackingOptions} value={trackingFilter} />
              <SelectField label="Status" onChange={setStatusFilter} options={[['ALL', 'All statuses'], ['ACTIVE', 'Active'], ['INACTIVE', 'Inactive'], ['ARCHIVED', 'Archived']]} value={statusFilter} />
            </div>
          </ScreenToolbar>
        }
      >
        <table>
          <thead>
            <tr>
              <th><SortableHeader label="Product name" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="name" sortState={sortState} /></th>
              <th><SortableHeader label="SKU" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="sku" sortState={sortState} /></th>
              <th><SortableHeader label="Barcode" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="barcode" sortState={sortState} /></th>
              <th><SortableHeader label="Category" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="category" sortState={sortState} /></th>
              <th><SortableHeader label="Brand" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="brand" sortState={sortState} /></th>
              <th><SortableHeader label="Tracking type" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="tracking" sortState={sortState} /></th>
              <th className="text-right"><SortableHeader align="right" label="Reorder level" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="reorder_level" sortState={sortState} /></th>
              <th className="text-right"><SortableHeader align="right" label="Cost" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="cost_price" sortState={sortState} /></th>
              <th><SortableHeader label="Status" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="status" sortState={sortState} /></th>
            </tr>
          </thead>
          <tbody>
            {sortedProducts.map((product) => (
              <tr key={product.id}>
                <td>
                  <div className="space-y-1">
                    <span className="font-semibold text-warelyn-text">{product.name}</span>
                    <p className="text-xs text-warelyn-muted">Unit {product.unit ?? 'pcs'}</p>
                  </div>
                </td>
                <td><span className="mono-cell">{product.sku ?? '-'}</span></td>
                <td><span className="mono-cell">{product.barcode ?? '-'}</span></td>
                <td>{categoriesById[product.category_id]?.name ?? '-'}</td>
                <td>{brandsById[product.brand_id]?.name ?? '-'}</td>
                <td>{trackingLabel(product)}</td>
                <td className="number-cell">{product.reorder_level ?? '-'}</td>
                <td className="number-cell">{formatMoney(product.cost_price, currency)}</td>
                <td><StatusBadge status={product.status ?? 'ACTIVE'}>{product.status ?? 'ACTIVE'}</StatusBadge></td>
              </tr>
            ))}
          </tbody>
        </table>
      </TableShell>
    </div>
  );
}

export function ProductFormPage() {
  const { accessToken } = useAuth();
  const navigate = useNavigate();
  const [categories, setCategories] = useState([]);
  const [brands, setBrands] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');
  const [form, setForm] = useState({
    name: '',
    sku: '',
    barcode: '',
    unit: 'pcs',
    cost_price: '',
    selling_price: '',
    category_id: '',
    brand_id: '',
    reorder_level: '',
    track_batch: false,
    track_expiry: false,
    track_serial: false,
  });

  useEffect(() => {
    async function load() {
      setIsLoading(true);
      setError('');
      try {
        const [categoryRows, brandRows] = await Promise.all([
          catalogService.listCategories(accessToken),
          catalogService.listBrands(accessToken),
        ]);
        setCategories(categoryRows);
        setBrands(brandRows);
      } catch (loadError) {
        setError(loadError.message);
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, [accessToken]);

  async function handleSubmit(event) {
    event.preventDefault();
    setIsSaving(true);
    setError('');
    try {
      const payload = {
        name: form.name,
        sku: form.sku,
        barcode: form.barcode || null,
        unit: form.unit || 'pcs',
        cost_price: form.cost_price || null,
        selling_price: form.selling_price || null,
        category_id: form.category_id ? Number(form.category_id) : null,
        brand_id: form.brand_id ? Number(form.brand_id) : null,
        reorder_level: form.reorder_level ? Number(form.reorder_level) : null,
        track_batch: form.track_batch,
        track_expiry: form.track_expiry,
        track_serial: form.track_serial,
      };
      await catalogService.createProduct(accessToken, payload);
      navigate('/catalog/products');
    } catch (saveError) {
      setError(saveError.message);
    } finally {
      setIsSaving(false);
    }
  }

  if (isLoading) return <LoadingState />;

  return (
    <div className="space-y-6">
      <PageHeader
        backTo="/catalog/products"
        kicker="Catalog"
        title="Create product"
        description="Add a focused product master record with SKU, barcode, pricing, tracking, and reorder settings."
      />
      {error ? <ErrorState description={error} /> : null}
      <form className="space-y-6" onSubmit={handleSubmit}>
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-warelyn-text">Basic details</h2>
          </CardHeader>
          <CardBody className="grid gap-4 md:grid-cols-2">
            <Input label="Product name" required value={form.name} onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))} />
            <Input label="SKU" required value={form.sku} onChange={(event) => setForm((current) => ({ ...current, sku: event.target.value }))} />
            <BarcodeInput label="Barcode" onChange={(event) => setForm((current) => ({ ...current, barcode: event.target.value }))} value={form.barcode} />
            <Input label="Unit" required value={form.unit} onChange={(event) => setForm((current) => ({ ...current, unit: event.target.value }))} />
            <SelectField label="Category" onChange={(value) => setForm((current) => ({ ...current, category_id: value }))} options={[['', 'No category'], ...categories.map((row) => [String(row.id), row.name])]} value={form.category_id} />
            <SelectField label="Brand" onChange={(value) => setForm((current) => ({ ...current, brand_id: value }))} options={[['', 'No brand'], ...brands.map((row) => [String(row.id), row.name])]} value={form.brand_id} />
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-warelyn-text">Pricing and reorder</h2>
          </CardHeader>
          <CardBody className="grid gap-4 md:grid-cols-3">
            <Input label="Cost price" min="0" step="0.01" type="number" value={form.cost_price} onChange={(event) => setForm((current) => ({ ...current, cost_price: event.target.value }))} />
            <Input label="Selling price" min="0" step="0.01" type="number" value={form.selling_price} onChange={(event) => setForm((current) => ({ ...current, selling_price: event.target.value }))} />
            <Input label="Reorder level" min="0" step="1" type="number" value={form.reorder_level} onChange={(event) => setForm((current) => ({ ...current, reorder_level: event.target.value }))} />
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-warelyn-text">Tracking configuration</h2>
          </CardHeader>
          <CardBody className="grid gap-3 md:grid-cols-3">
            <CheckboxField checked={form.track_batch} helper="Track inbound and outbound lots." label="Batch tracking" onChange={(checked) => setForm((current) => ({ ...current, track_batch: checked }))} />
            <CheckboxField checked={form.track_expiry} helper="Capture expiry-controlled inventory." label="Expiry tracking" onChange={(checked) => setForm((current) => ({ ...current, track_expiry: checked }))} />
            <CheckboxField checked={form.track_serial} helper="Require serial-level handling downstream." label="Serial tracking" onChange={(checked) => setForm((current) => ({ ...current, track_serial: checked }))} />
          </CardBody>
        </Card>

        <div className="sticky-form-footer">
          <div className="workflow-helper-panel max-w-xl">
            <h3>What happens next?</h3>
            <p>Saving creates the product master only. Stock remains backend-driven and is not calculated or mutated from this screen.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button onClick={() => navigate('/catalog/products')} type="button" variant="ghost">
              Cancel
            </Button>
            <Button isLoading={isSaving} type="submit">
              Create product
            </Button>
          </div>
        </div>
      </form>
    </div>
  );
}

export function CategoriesPage() {
  return (
    <MasterDataListPage
      actions={
        <Link to="/catalog/categories/new">
          <Button>
            <Plus size={16} />
            Category
          </Button>
        </Link>
      }
      description="Manage category records used to organize products and catalog reporting."
      emptyDescription="Create categories to organize products and simplify reporting."
      emptyFilteredDescription="Try changing your search keyword or clearing filters."
      emptyFilteredTitle="No matching categories found"
      emptyIllustration={emptyStateIllustrations.products}
      emptyTitle="No categories created yet"
      fields={nameDescriptionFields}
      listRecords={catalogService.listCategories}
      searchPlaceholder="Search categories"
      title="Categories"
    />
  );
}

export function CategoryFormPage() {
  return (
    <MasterDataFormPage
      backTo="/catalog/categories"
      createRecord={catalogService.createCategory}
      description="Create a focused category record without mixing it into the catalog list view."
      fields={nameDescriptionFields}
      kicker="Catalog"
      submitLabel="Create category"
      title="Create category"
    />
  );
}

export function BrandsPage() {
  return (
    <MasterDataListPage
      actions={
        <Link to="/catalog/brands/new">
          <Button>
            <Plus size={16} />
            Brand
          </Button>
        </Link>
      }
      description="Maintain brand master data used across products and reports."
      emptyDescription="Create a brand to classify catalog records."
      emptyFilteredDescription="Try changing your search keyword or clearing filters."
      emptyFilteredTitle="No matching brands found"
      emptyIllustration={emptyStateIllustrations.products}
      fields={nameDescriptionFields}
      listRecords={catalogService.listBrands}
      searchPlaceholder="Search brands"
      title="Brands"
    />
  );
}

export function BrandFormPage() {
  return (
    <MasterDataFormPage
      backTo="/catalog/brands"
      createRecord={catalogService.createBrand}
      description="Create a focused brand record without mixing it into the brand list."
      fields={nameDescriptionFields}
      kicker="Catalog"
      submitLabel="Create brand"
      title="Create brand"
    />
  );
}

export function VendorsPage() {
  return (
    <MasterDataListPage
      actions={
        <Link to="/catalog/vendors/new">
          <Button>
            <Plus size={16} />
            Vendor
          </Button>
        </Link>
      }
      description="Maintain supplier records used by purchase order workflows."
      emptyDescription="Add suppliers to create purchase orders, record bills, and manage procurement."
      emptyFilteredDescription="Adjust your search or filters to find the supplier you need."
      emptyFilteredTitle="No matching suppliers found"
      emptyIllustration={emptyStateIllustrations.billings}
      emptyTitle="No suppliers added yet"
      fields={partyFields}
      listRecords={catalogService.listVendors}
      searchPlaceholder="Search vendors by name, email, or GST number"
      title="Vendors"
    />
  );
}

export function VendorFormPage() {
  return (
    <MasterDataFormPage
      backTo="/catalog/vendors"
      createRecord={catalogService.createVendor}
      customInputs={partyCustomInputs}
      description="Create a dedicated vendor record for purchasing workflows."
      fields={partyFields}
      kicker="Catalog"
      submitLabel="Create vendor"
      title="Create vendor"
    />
  );
}

export function CustomersPage() {
  return (
    <MasterDataListPage
      actions={
        <Link to="/catalog/customers/new">
          <Button>
            <Plus size={16} />
            Customer
          </Button>
        </Link>
      }
      description="Maintain customer records used by sales orders and returns."
      emptyDescription="Add customers to create sales orders, invoices, and track receivables."
      emptyFilteredDescription="Adjust your search or filters to find the customer you need."
      emptyFilteredTitle="No matching customers found"
      emptyIllustration={emptyStateIllustrations.sales}
      emptyTitle="No customers added yet"
      fields={partyFields}
      listRecords={catalogService.listCustomers}
      searchPlaceholder="Search customers by name, email, or GST number"
      title="Customers"
    />
  );
}

export function CustomerFormPage() {
  return (
    <MasterDataFormPage
      backTo="/catalog/customers"
      createRecord={catalogService.createCustomer}
      customInputs={partyCustomInputs}
      description="Create a dedicated customer record for sales workflows."
      fields={partyFields}
      kicker="Catalog"
      submitLabel="Create customer"
      title="Create customer"
    />
  );
}

function trackingType(product) {
  if (product.track_serial) return 'SERIAL';
  if (product.track_expiry) return 'EXPIRY';
  if (product.track_batch) return 'BATCH';
  return 'STANDARD';
}

function trackingLabel(product) {
  const type = trackingType(product);
  return type === 'STANDARD' ? 'Standard' : type.charAt(0) + type.slice(1).toLowerCase();
}

function SelectField({ label, onChange, options, value }) {
  return (
    <label className="block min-w-[160px]">
      <span className="mb-2 block text-sm font-medium text-warelyn-text">{label}</span>
      <select
        className="block w-full rounded-lg border border-warelyn-border bg-white px-3 py-2.5 text-sm text-warelyn-text shadow-sm outline-none transition focus:border-warelyn-primary focus:ring-4 focus:ring-blue-900/10"
        onChange={(event) => onChange(event.target.value)}
        value={value}
      >
        {options.map(([optionValue, optionLabel]) => (
          <option key={`${label}-${optionValue}`} value={optionValue}>
            {optionLabel}
          </option>
        ))}
      </select>
    </label>
  );
}

function CheckboxField({ checked, helper, label, onChange }) {
  return (
    <label className="rounded-xl border border-warelyn-border bg-slate-50 p-4">
      <span className="flex items-start gap-3">
        <input checked={checked} className="mt-1" onChange={(event) => onChange(event.target.checked)} type="checkbox" />
        <span>
          <strong className="block text-sm text-warelyn-text">{label}</strong>
          <small className="mt-1 block text-xs text-warelyn-muted">{helper}</small>
        </span>
      </span>
    </label>
  );
}
