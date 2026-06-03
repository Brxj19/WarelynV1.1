/** Static UI mocks for marketing — no API, no navigation */

function DemoChrome({ title, children }) {
  return (
    <div className="landing-demo-frame">
      <div className="landing-demo-chrome">
        <span className="landing-demo-dot bg-red-400" />
        <span className="landing-demo-dot bg-amber-400" />
        <span className="landing-demo-dot bg-emerald-400" />
        <span className="landing-demo-url">{title}</span>
      </div>
      <div className="landing-demo-body">{children}</div>
    </div>
  );
}

function DashboardDemo() {
  return (
    <DemoChrome title="app.warelyn.io/dashboard">
      <div className="space-y-3 p-3">
        <div className="grid grid-cols-4 gap-2">
          {['Revenue', 'Spend', 'Margin', 'AOV'].map((label, i) => (
            <div className="rounded-lg border border-slate-200 bg-white p-2" key={label}>
              <p className="text-[8px] font-semibold uppercase text-slate-500">{label}</p>
              <p className="text-[12px] font-bold text-slate-900">{['$42k', '$18k', '$24k', '$890'][i]}</p>
            </div>
          ))}
        </div>
        <div className="h-24 rounded-lg border border-slate-200 bg-gradient-to-t from-blue-50 to-white p-2">
          <div className="flex h-full items-end gap-0.5">
            {[40, 55, 48, 62, 58, 70, 65].map((h, i) => (
              <div className="flex-1 rounded-sm bg-warelyn-primary/70" key={i} style={{ height: `${h}%` }} />
            ))}
          </div>
        </div>
      </div>
    </DemoChrome>
  );
}

function CatalogDemo() {
  const rows = ['SKU-1042 · Widget A', 'SKU-2091 · Carton B', 'SKU-3310 · Pallet C'];
  return (
    <DemoChrome title="app.warelyn.io/catalog/products">
      <div className="p-3">
        <div className="mb-2 flex gap-1.5">
          <div className="h-5 flex-1 rounded border border-slate-200 bg-slate-50" />
          <div className="h-5 w-10 rounded bg-warelyn-primary/90" />
        </div>
        <div className="rounded-lg border border-slate-200 text-[9px]">
          <div className="grid grid-cols-3 gap-1 border-b border-slate-100 bg-slate-50 px-2 py-1.5 font-semibold text-slate-600">
            <span>Product</span>
            <span>Stock</span>
            <span>Status</span>
          </div>
          {rows.map((row) => (
            <div className="grid grid-cols-3 gap-1 border-b border-slate-50 px-2 py-1.5 last:border-0" key={row}>
              <span className="truncate text-slate-800">{row}</span>
              <span className="text-slate-600">124</span>
              <span className="text-emerald-600">Active</span>
            </div>
          ))}
        </div>
      </div>
    </DemoChrome>
  );
}

function WarehouseDemo() {
  return (
    <DemoChrome title="app.warelyn.io/warehouses">
      <div className="grid grid-cols-2 gap-2 p-3">
        {['North DC', 'South Hub'].map((name) => (
          <div className="rounded-lg border border-slate-200 bg-white p-2" key={name}>
            <p className="text-[10px] font-semibold text-slate-900">{name}</p>
            <p className="mt-0.5 text-[8px] text-slate-500">Zones · 12</p>
            <div className="mt-2 h-2 w-full rounded-full bg-slate-100">
              <div className="h-full w-3/4 rounded-full bg-emerald-500" />
            </div>
          </div>
        ))}
      </div>
    </DemoChrome>
  );
}

function PurchasesDemo() {
  return (
    <DemoChrome title="app.warelyn.io/purchases">
      <div className="space-y-1.5 p-3">
        {[
          ['PO-2401', 'Submitted'],
          ['PO-2402', 'Partial'],
          ['PO-2403', 'Received'],
        ].map(([id, status]) => (
          <div className="flex items-center justify-between rounded border border-slate-200 px-2 py-1.5 text-[9px]" key={id}>
            <span className="font-medium text-slate-800">{id}</span>
            <span className="rounded-full bg-indigo-50 px-1 py-0.5 text-indigo-700">{status}</span>
          </div>
        ))}
      </div>
    </DemoChrome>
  );
}

function SalesDemo() {
  return (
    <DemoChrome title="app.warelyn.io/sales">
      <div className="p-3">
        <div className="mb-2 flex justify-between text-[9px]">
          <span className="font-semibold text-slate-800">Open orders</span>
          <span className="text-warelyn-primary">24</span>
        </div>
        <div className="flex h-20 items-end gap-1 rounded-lg border border-slate-200 bg-slate-50 p-2">
          {[30, 45, 38, 52, 48].map((h, i) => (
            <div className="flex-1 rounded-sm bg-amber-400/80" key={i} style={{ height: `${h}%` }} />
          ))}
        </div>
      </div>
    </DemoChrome>
  );
}

function ReportsDemo() {
  return (
    <DemoChrome title="app.warelyn.io/reports">
      <div className="space-y-2 p-3">
        <div className="grid grid-cols-2 gap-2">
          {['Valuation', 'Movement'].map((t) => (
            <div className="rounded-lg border border-slate-200 p-2 text-[8px]" key={t}>
              <p className="text-slate-500">{t}</p>
              <p className="font-bold text-slate-900">$128k</p>
            </div>
          ))}
        </div>
        <div className="h-16 rounded-lg border border-slate-200 bg-white p-2">
          <div className="flex h-full items-center justify-center gap-2">
            <div className="h-8 w-8 rounded-full border-4 border-emerald-500 border-r-transparent" />
            <span className="text-[9px] text-slate-600">Stock health</span>
          </div>
        </div>
      </div>
    </DemoChrome>
  );
}

const DEMOS = {
  Dashboard: DashboardDemo,
  Catalog: CatalogDemo,
  Warehousing: WarehouseDemo,
  Purchases: PurchasesDemo,
  Sales: SalesDemo,
  Reports: ReportsDemo,
};

export function LandingDemoPreview({ tag }) {
  const Demo = DEMOS[tag] ?? DashboardDemo;
  return <Demo />;
}

export const landingDemoMeta = [
  {
    title: 'Operations command center',
    description: 'Live KPI pulse and team activity across roles.',
    tag: 'Dashboard',
    points: ['See operational health at a glance.', 'Keep role-specific tasks visible without noise.'],
  },
  {
    title: 'Catalog management',
    description: 'Products, categories, brands, customers, and vendors.',
    tag: 'Catalog',
    points: ['Maintain SKUs and tracking metadata in one place.', 'Inspect product records without leaving the catalog.'],
  },
  {
    title: 'Warehouse control',
    description: 'Warehouse visibility, cycle counts, and putaway orchestration.',
    tag: 'Warehousing',
    points: ['Watch stock movement by warehouse and location.', 'Move through putaway and cycle count workflows quickly.'],
  },
  {
    title: 'Purchases + receipts',
    description: 'Create POs, receive stock, and track vendor commitments.',
    tag: 'Purchases',
    points: ['Track receiving progress from order to shelf.', 'Keep vendor commitments and follow-up work visible.'],
  },
  {
    title: 'Sales + invoicing',
    description: 'From order capture to pick-pack-fulfill and invoicing.',
    tag: 'Sales',
    points: ['Follow sales orders through fulfillment milestones.', 'Generate invoices only when the workflow is ready.'],
  },
  {
    title: 'Reports suite',
    description: 'Inventory summaries, valuation, movement, and reconciliation.',
    tag: 'Reports',
    points: ['Review totals, trends, and mismatches in one place.', 'Move from insight to action with direct report links.'],
  },
];
