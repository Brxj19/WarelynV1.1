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
      <div className="space-y-2 p-2">
        <div className="grid grid-cols-4 gap-1.5">
          {['Revenue', 'Spend', 'Margin', 'AOV'].map((label, i) => (
            <div className="rounded-md border border-slate-200 bg-white p-1.5" key={label}>
              <p className="text-[7px] font-semibold uppercase text-slate-500">{label}</p>
              <p className="text-[10px] font-bold text-slate-900">{['$42k', '$18k', '$24k', '$890'][i]}</p>
            </div>
          ))}
        </div>
        <div className="h-16 rounded-md border border-slate-200 bg-gradient-to-t from-blue-50 to-white p-1.5">
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
      <div className="p-2">
        <div className="mb-1.5 flex gap-1">
          <div className="h-4 flex-1 rounded border border-slate-200 bg-slate-50" />
          <div className="h-4 w-8 rounded bg-warelyn-primary/90" />
        </div>
        <div className="rounded-md border border-slate-200 text-[8px]">
          <div className="grid grid-cols-3 gap-1 border-b border-slate-100 bg-slate-50 px-1.5 py-1 font-semibold text-slate-600">
            <span>Product</span>
            <span>Stock</span>
            <span>Status</span>
          </div>
          {rows.map((row) => (
            <div className="grid grid-cols-3 gap-1 border-b border-slate-50 px-1.5 py-1 last:border-0" key={row}>
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
      <div className="grid grid-cols-2 gap-1.5 p-2">
        {['North DC', 'South Hub'].map((name) => (
          <div className="rounded-md border border-slate-200 bg-white p-1.5" key={name}>
            <p className="text-[9px] font-semibold text-slate-900">{name}</p>
            <p className="mt-0.5 text-[7px] text-slate-500">Zones · 12</p>
            <div className="mt-1 h-1.5 w-full rounded-full bg-slate-100">
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
      <div className="p-2 space-y-1">
        {[
          ['PO-2401', 'Submitted'],
          ['PO-2402', 'Partial'],
          ['PO-2403', 'Received'],
        ].map(([id, status]) => (
          <div className="flex items-center justify-between rounded border border-slate-200 px-1.5 py-1 text-[8px]" key={id}>
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
      <div className="p-2">
        <div className="mb-1 flex justify-between text-[8px]">
          <span className="font-semibold text-slate-800">Open orders</span>
          <span className="text-warelyn-primary">24</span>
        </div>
        <div className="flex h-14 items-end gap-1 rounded-md border border-slate-200 bg-slate-50 p-1">
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
      <div className="p-2 space-y-1.5">
        <div className="grid grid-cols-2 gap-1">
          {['Valuation', 'Movement'].map((t) => (
            <div className="rounded border border-slate-200 p-1 text-[7px]" key={t}>
              <p className="text-slate-500">{t}</p>
              <p className="font-bold text-slate-900">$128k</p>
            </div>
          ))}
        </div>
        <div className="h-10 rounded border border-slate-200 bg-white p-1">
          <div className="flex h-full items-center justify-center gap-2">
            <div className="h-6 w-6 rounded-full border-4 border-emerald-500 border-r-transparent" />
            <span className="text-[8px] text-slate-600">Stock health</span>
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
  { title: 'Operations command center', description: 'Live KPI pulse and team activity across roles.', tag: 'Dashboard' },
  { title: 'Catalog management', description: 'Products, categories, brands, customers, and vendors.', tag: 'Catalog' },
  { title: 'Warehouse control', description: 'Warehouse visibility, cycle counts, and putaway orchestration.', tag: 'Warehousing' },
  { title: 'Purchases + receipts', description: 'Create POs, receive stock, and track vendor commitments.', tag: 'Purchases' },
  { title: 'Sales + invoicing', description: 'From order capture to pick-pack-fulfill and invoicing.', tag: 'Sales' },
  { title: 'Reports suite', description: 'Inventory summaries, valuation, movement, and reconciliation.', tag: 'Reports' },
];
