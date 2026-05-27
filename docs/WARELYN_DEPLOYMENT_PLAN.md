# Warelyn Inventory — Deployment Readiness Phase Plan
**Version:** 3.0 — Post Phase 15–18 Audit  
**Date:** 2026-05-25  
**Baseline:** 218 tests passing  
**Goal:** Production-ready deployment

---

## Section 1: Full Bug Registry (All Issues Found in Audit)

### CRITICAL — App-Breaking

| ID | Category | File(s) | Description |
|----|----------|---------|-------------|
| C-01 | Reports | `ReportsPage.jsx → SimpleReportPage` | **All report sub-pages crash** — `InventorySummaryReport` returns an object, but `SimpleReportPage` passes it directly as `data` to `loadRows ? loadRows(data) : data`. Since `InventorySummaryReportPage` passes no `loadRows` prop, `data` (an object) is fed into `Array.isArray(sourceRows)` which returns `false`, so `normalizedRows = []`. Summary renders fine but the component still crashes because it tries to call `sortRows([], ...)` on the result of the object—the root crash is that `data` is never null-guarded before `summary(data)` is called during the loading phase (data is null initially). Fix: add `data !== null` guard in the summary render, and add proper `loadRows` to all non-array reports. |
| C-02 | Reports | `InventorySummaryReportPage.jsx` | No `loadRows` prop — backend returns a flat object `{total_products, active_products, ...}` but `SimpleReportPage` tries to `.map()` it. Add `loadRows={() => []}` and make the summary the primary display. |
| C-03 | Reports | `ProductValuationReportPage.jsx` | Backend returns `{total_stock_value, total_units, rows:[...]}` but page uses `loadRows={(data) => data?.rows ?? []}` — this is correct, but the `summary` prop receives the raw object before it loads, crashing `Object.entries(null)`. Fix: null-guard `summary(data)` — render nothing until data is loaded. |
| C-04 | Reports | `ReconciliationReportPage.jsx` | Same pattern — `loadRows={(data) => data?.mismatches ?? []}` is correct, but `summary` receives null on first render. Fix same as C-03. |

### HIGH — Wrong Behavior (User Reported)

| ID | Category | File(s) | Description |
|----|----------|---------|-------------|
| H-01 | PDF/Templates | `documents.py → _invoice_context()` | **`tax_rate` always shows "0"** — `InvoiceItem` model has no `tax_rate` column (only `tax_amount`). Template shows `{{ item.tax_rate }}%` which always renders as `0`. Fix: compute tax_rate from `item.tax_amount / item.line_total * 100` if non-zero, else `0`, and pass that. |
| H-02 | PDF/Templates | `documents.py → _invoice_context()` | **`warehouse_name` always empty** — items are built from `invoice.items` (InvoiceItem records) which have no warehouse FK. Must look up the fulfillment's warehouse via `item.sales_order_item_id → fulfillment_items → location_id → warehouse`. If no fulfillment, use `"N/A"`. |
| H-03 | Email Templates | `documents.py → send_invoice() / send_bill()` | **Email templates still not applying company branding** — `DEFAULT_TEMPLATES` for INVOICE_SEND still shows `"Northstar Inventory"` in the HTML header `<p>` tag. Must be changed to `"Warelyn Inventory"` and use `{{ sender_name }}` (which is set at line 543). Also: the OTP email `DEFAULT_TEMPLATES` contains a raw `{{ code }}` with the old plain layout; it needs the new decorated template from `otp_email.html` in `docs/templates/`. |
| H-04 | Email Templates | `EmailTemplatesPage.jsx` | **Editor has no rich toolbar** — template description says "word-like toolkit in the window" (reference to Zoho-style WYSIWYG). The editor currently shows a plain `<textarea>`. Must add a formatting toolbar: Bold, Italic, Underline, Strikethrough, font size selector, text color button, and "Insert Placeholder" dropdown — all operating on the `body_template` state via `document.execCommand` or a lightweight custom approach. |
| H-05 | Preferences | `UserPreferences` model + `SettingsPage.jsx` | **Preferences not persisted end-to-end** — model exists, API exists, but `table_density`, `default_landing_page`, `theme_preference` are stored in DB but never *applied* to the UI. The app must read preferences on login and apply them: redirect to `default_landing_page` after login (currently always `/dashboard`), apply `table_density` class to all `<table>` elements, apply `theme_preference` toggling a CSS class on `<html>`. |
| H-06 | Preferences | `SettingsPage.jsx → UserPreferencesSection` | **Preferences UI is plain and forgettable** — must be completely redesigned as specified in Section 3 of this document. It looks like a settings form, not a personalization experience. |
| H-07 | Preferences | `UserPreferences` model | **Missing template preference fields** — user cannot select which PDF template or email template they prefer for documents. Add: `preferred_invoice_template_id`, `preferred_bill_template_id`, `preferred_invoice_email_template_id`, `preferred_bill_email_template_id` (all nullable FK to `document_templates.id`) to `UserPreferences`. |
| H-08 | XLSX Download | `imports.py → build_template_xlsx()` | **XLSX template download broken** — `build_template_xlsx()` is a static method on `ProductImportService` but the import service constructor requires `db: Session`. The endpoint calls `ProductImportService.build_template_xlsx()` as a static method, but `ProductImportService` may not define it as `@staticmethod` correctly, causing an error. Verify the `@staticmethod` decorator is present and the method produces a valid XLSX. |
| H-09 | Navigation | `navigation.js` | **Duplicate icons in sidebar** — collapsed sidebar shows only icons, making navigation ambiguous when multiple items share the same icon. Specifically: `Layers` is used for both "Tenants" and "Categories"; `FileText` is used for both "Bills" and "Invoices"; `Plus` reused everywhere; `Warehouse` duplicated; `PackageCheck` duplicated. Every item must have a unique, semantically correct icon. See Section 2 for the full icon replacement map. |
| H-10 | Navigation | All detail/form pages | **No back button on any page** — `BackButton` component exists with full label-resolution logic and CSS, but it is imported in zero pages. Every detail page and form page must import and render `<BackButton to="/parent-path" />` at the top. See Section 2 for the complete per-page list. |

### MEDIUM — Quality/UX Issues

| ID | Category | File(s) | Description |
|----|----------|---------|-------------|
| M-01 | PDF Quality | `documents.py → DEFAULT_TEMPLATES` | **PDF templates are functional but plain** — the current invoice/bill PDF uses basic Arial with a simple blue header. Needs 4–5 distinct styled templates (see Section 4 for full HTML for each). |
| M-02 | Email Quality | `documents.py → DEFAULT_TEMPLATES` | **Email templates are plain** — OTP and invoice email look like system emails, not brand emails. Need polished templates with Warelyn logo placeholder, proper color blocks, footer (see Section 4). |
| M-03 | Reports | Various report pages | **Report pages have no filters wired** — `SimpleReportPage` accepts a `filters` prop but no report page actually passes warehouse/date filters. Low-stock, warehouse-stock, and stock-movements reports especially need date and warehouse filters. |
| M-04 | Documents | `DocumentsPages.jsx` | **Invoice/Bill list pages have no Create button wired to proper form** — "Create Invoice" button calls `documentService.createInvoice` with a minimal hardcoded payload. Needs a proper create flow (select sales order, then generate invoice). |
| M-05 | Settings | `SettingsPage.jsx` | **Template shortcut cards don't reflect current template** — the cards linking to email/pdf template editors show no preview thumbnail or name of current active template. |
| M-06 | PDF | `pdf_service.py` | **WeasyPrint system fonts may not exist in Docker** — `weasyprint.HTML(string=html).write_pdf()` requires system fonts. In a minimal Docker container, Arial/fonts may be missing, causing WeasyPrint to fall back to serif. Must install fonts in Dockerfile or use web-safe CSS.Also solve the weasy print compatitbility issue with python 3.14 if not solvable then use some other alternative |
| M-07 | PDF | Invoice PDF (INV-01-00034.pdf attached) | **Good structure but missing logo area** — the delivered PDF already renders the 2-column layout, line items, and totals correctly. The only gaps: logo box is a dashed border placeholder, no `@page` A4 margins are applied in all templates, and the font is wrong (not the provided template fonts). |

---

## Section 2: Required Icon Replacements and Back Button Map

### 2.1 Icon Replacement Map

**File to edit:** `frontend/src/components/navigation.js`

Every nav item must use a unique icon. Import the new icons at the top of the file.

| Nav Item | Current Icon | New Icon | Import Name |
|----------|-------------|----------|-------------|
| Platform Console | `UserCog` | `ShieldAlert` | `ShieldAlert` |
| Tenants | `Layers` | `Building2` | `Building2` |
| Audit Logs | `ClipboardList` | `ScrollText` | `ScrollText` |
| Platform Health | `Server` | `HeartPulse` | `HeartPulse` |
| Dashboard | `LayoutDashboard` | ✅ keep | — |
| Products (group) | `Package` | `Boxes` | already imported |
| All Products | `Package` | `Package` | ✅ keep |
| Create Product | `Plus` | `PackagePlus` | `PackagePlus` |
| Import Products | `Upload` | `FileUp` | `FileUp` |
| Categories | `Layers` | `Tag` | `Tag` |
| Brands | `BadgeCheck` | `Star` | `Star` |
| Vendors | `BriefcaseBusiness` | `Handshake` | `Handshake` |
| Customers | `Users` | `UserRound` | `UserRound` |
| Warehouses (group) | `Warehouse` | `Warehouse` | ✅ keep |
| All Warehouses | `Warehouse` | `Warehouse` | ✅ keep |
| Create Warehouse | `Plus` | `PlusSquare` | `PlusSquare` |
| Purchase Orders (group) | `ClipboardList` | `ShoppingBag` | `ShoppingBag` |
| All Purchase Orders | `ClipboardList` | `ShoppingBag` | same |
| Create Purchase Order | `Plus` | `BadgePlus` | `BadgePlus` |
| Purchase Receipts (group) | `Truck` | `Truck` | ✅ keep |
| All Receipts | `Truck` | `Truck` | ✅ keep |
| Receive Stock | `Plus` | `LogIn` | `LogIn` |
| Bills | `FileText` | `ReceiptText` | `ReceiptText` |
| Sales Orders (group) | `ShoppingCart` | `ShoppingCart` | ✅ keep |
| All Sales Orders | `ShoppingCart` | `ShoppingCart` | ✅ keep |
| Create Sales Order | `Plus` | `FilePlus2` | `FilePlus2` |
| Invoices | `FileText` | `FileCheck2` | `FileCheck2` |
| Pick Tasks (group) | `ListChecks` | `ClipboardCheck` | `ClipboardCheck` |
| Pick Tasks | `ListChecks` | `ClipboardCheck` | same |
| Packages (group) | `PackageCheck` | `PackageCheck` | ✅ keep |
| Packages | `PackageCheck` | `PackageCheck` | ✅ keep |
| Fulfillments (group) | `Boxes` | `TruckElectric` OR `Send` | `Send` |
| Fulfillments | `Boxes` | `Send` | same |
| Sales Returns (group) | `Undo2` | `RotateCcw` | `RotateCcw` |
| Sales Returns | `Undo2` | `RotateCcw` | same |
| Create Return | `Plus` | `CornerUpLeft` | `CornerUpLeft` |
| Returns QC | `ShieldCheck` | `ShieldCheck` | ✅ keep |
| Reports Overview | `BarChart3` | `BarChart3` | ✅ keep |
| Inventory Summary | `Boxes` | `Database` | `Database` |
| Warehouse Stock | `Warehouse` | `Layers2` | `Layers2` |
| Location Stock | `Warehouse` | `MapPin` | `MapPin` |
| Stock Movements | `Activity` | `TrendingUp` | `TrendingUp` |
| Low Stock | `AlertTriangle` | `AlertTriangle` | ✅ keep |
| Reorder Suggestions | `ClipboardList` | `RefreshCw` | `RefreshCw` |
| Product Valuation | `BarChart3` | `DollarSign` | `DollarSign` |
| Batch Expiry | `PackageCheck` | `CalendarClock` | `CalendarClock` |
| Serial Status | `PackageCheck` | `Hash` | `Hash` |
| Blocked Stock | `ShieldCheck` | `ShieldOff` | `ShieldOff` |
| Reconciliation | `ShieldCheck` | `Scale` | `Scale` |
| Settings | `Settings` | `Settings` | ✅ keep |

**Step-by-step for this change:**
1. At the top of `navigation.js`, add to imports: `Building2, CalendarClock, ClipboardCheck, CornerUpLeft, Database, DollarSign, FileCheck2, FilePlus2, FileUp, HandShake, Hash, HeartPulse, Layers2, LogIn, MapPin, PackagePlus, PlusSquare, ReceiptText, RefreshCw, RotateCcw, Scale, ScrollText, Send, ShieldAlert, ShieldOff, Star, Tag, TrendingUp, UserRound, BadgePlus`
2. Replace each `icon:` value in the array using the table above.
3. Remove all unused icon imports from the import block.

### 2.2 Back Button Additions

The `BackButton` component at `frontend/src/components/ui/BackButton.jsx` is fully built. It has zero usages. Add it to every detail and form page.

**Import to add at top of each file:**
```jsx
import { BackButton } from '../components/ui/BackButton.jsx';
```

**Where to place:** Immediately inside the page's outer `<div>`, before the page header or title element, on its own line.

```jsx
// Pattern — place at top of page JSX return
return (
  <div className="space-y-6">
    <BackButton to="/parent-route" />
    <PageHeader ... />
    ...
  </div>
);
```

**Complete per-page back button map:**

| Page File | `to` prop value |
|-----------|----------------|
| `PurchaseOrderDetailPage.jsx` | `/purchases` |
| `PurchaseOrderFormPage.jsx` | `/purchases` |
| `PurchaseReceiptDetailPage.jsx` | `/purchase-receipts` |
| `PurchaseReceivePage.jsx` | `/purchase-receipts` |
| `SalesOrderDetailPage.jsx` | `/sales` |
| `SalesOrderFormPage.jsx` | `/sales` |
| `SalesReturnDetailPage.jsx` | `/returns` |
| `SalesReturnFormPage.jsx` | `/returns` |
| `SalesReturnInspectPage.jsx` | `/returns/qc` |
| `SalesFulfillPage.jsx` | `/sales` |
| `SalesFulfillmentDetailPage.jsx` | `/sales-fulfillments` |
| `SalesPickPage.jsx` | `/pick-tasks` |
| `SalesPackagePage.jsx` | `/packages` |
| `PickTaskDetailPage.jsx` | `/pick-tasks` |
| `PackageDetailPage.jsx` | `/packages` |
| `WarehouseDetailPage.jsx` | `/warehouses` |
| `TenantDetailPage.jsx` | `/admin/tenants` |
| `ProductImportPage.jsx` | `/catalog/products` |
| `VerifyEmailPage.jsx` | `/settings` |
| `VerifyPhonePage.jsx` | `/settings` |
| `AuditLogsPage.jsx` | `/admin` |
| `PlatformHealthPage.jsx` | `/admin` |
| `EmailTemplatesPage.jsx` | `/settings` |
| `PdfTemplatesPage.jsx` | `/settings` |
| `CatalogMasterPages.jsx` (all form sub-pages inside) | their respective list pages — add to `ProductFormPage → /catalog/products`, `CategoryFormPage → /catalog/categories`, `BrandFormPage → /catalog/brands`, `VendorFormPage → /catalog/vendors`, `CustomerFormPage → /catalog/customers` |

**Note on `CatalogMasterPages.jsx`:** It's a single file containing multiple exported page components. Add the import once at the top of the file and add `<BackButton to="..." />` inside each `*FormPage` return.

---

## Section 3: Preferences Page — Complete Redesign Spec

### 3.1 What Must Change

The current `UserPreferencesSection` is a plain card with two `<select>` dropdowns. It must be completely replaced with a visually distinct, two-panel settings experience that feels like a personalization dashboard.

### 3.2 New Design: Left-Sidebar Navigation + Right Content Panel

```
┌─────────────────────────────────────────────────────────────────────┐
│  My Preferences                                                     │
│  How Warelyn looks and behaves just for you.                        │
├────────────────────┬────────────────────────────────────────────────┤
│  Appearance        │                                                │
│  ──────────────    │   ┌────────────────────────────────────────┐   │
│  🎨 Display        │   │  Display & Appearance                  │   │
│                    │   │  ─────────────────────────────────────  │   │
│  Workspace         │   │  Theme                                  │   │
│  ──────────────    │   │  ○ ☀ Light  ● 🌙 Dark  ○ 💻 System   │   │
│  🏠 Startup Page  │   │                                         │   │
│  📋 Table View    │   │  Table Density                          │   │
│                    │   │  ○ Compact  ● Comfortable  ○ Spacious  │   │
│  Notifications     │   └────────────────────────────────────────┘   │
│  ──────────────    │                                                │
│  🔔 Alerts        │                                                │
│                    │                                                │
│  Documents         │                                                │
│  ──────────────    │                                                │
│  📄 Templates      │                                                │
└────────────────────┴────────────────────────────────────────────────┘
```

### 3.3 React Component Structure

**File: `frontend/src/pages/SettingsPage.jsx` → `UserPreferencesSection` function**

Replace the entire function body with the following structure. Do NOT use a `<form>` tag; use individual save buttons per section or a single "Save All" at the bottom.

```jsx
function UserPreferencesSection({ accessToken }) {
  const toast = useToast();
  const { user } = useAuth();
  const [prefs, setPrefs] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeSection, setActiveSection] = useState('display');
  const [saving, setSaving] = useState(false);

  // sections: 'display' | 'workspace' | 'notifications' | 'documents'
  
  // Left nav items:
  const prefSections = [
    {
      group: 'Appearance',
      items: [{ id: 'display', icon: Palette, label: 'Display' }],
    },
    {
      group: 'Workspace',
      items: [
        { id: 'startup', icon: Home, label: 'Startup Page' },
        { id: 'tables', icon: LayoutList, label: 'Table View' },
      ],
    },
    {
      group: 'Notifications',
      items: [{ id: 'alerts', icon: Bell, label: 'Alerts' }],
    },
    {
      group: 'Documents',
      items: [{ id: 'templates', icon: FileText, label: 'Templates' }],
    },
  ];
```

### 3.4 Theme Selector — Visual Cards (not a `<select>`)

```jsx
function ThemeCard({ value, label, icon, selected, onClick }) {
  return (
    <button
      type="button"
      onClick={() => onClick(value)}
      className={`flex flex-col items-center gap-2 rounded-xl border-2 p-4 transition w-32
        ${selected
          ? 'border-warelyn-primary bg-blue-50 text-warelyn-primary'
          : 'border-warelyn-border bg-white text-warelyn-muted hover:border-warelyn-primary/40'
        }`}
    >
      {icon}
      <span className="text-xs font-semibold">{label}</span>
      {selected && <div className="h-2 w-2 rounded-full bg-warelyn-primary" />}
    </button>
  );
}
```

Display three `<ThemeCard>` buttons in a row: Light (Sun icon), Dark (Moon icon), System (Monitor icon).

### 3.5 Table Density Selector — Radio Toggle Strip

```jsx
function DensityToggle({ value, onChange }) {
  const options = [
    { id: 'compact', label: 'Compact', description: 'More rows visible' },
    { id: 'comfortable', label: 'Comfortable', description: 'Standard spacing' },
    { id: 'spacious', label: 'Spacious', description: 'Extra breathing room' },
  ];
  return (
    <div className="flex gap-2">
      {options.map((opt) => (
        <button key={opt.id} type="button" onClick={() => onChange(opt.id)}
          className={`flex-1 rounded-xl border-2 p-3 text-left transition
            ${value === opt.id
              ? 'border-warelyn-primary bg-blue-50'
              : 'border-warelyn-border bg-white hover:border-warelyn-primary/40'
            }`}
        >
          <p className={`text-sm font-semibold ${value === opt.id ? 'text-warelyn-primary' : 'text-warelyn-text'}`}>
            {opt.label}
          </p>
          <p className="text-xs text-warelyn-muted mt-0.5">{opt.description}</p>
        </button>
      ))}
    </div>
  );
}
```

### 3.6 Startup Page — Landing Route Picker

Replace the `<select>` with a list of route cards. Each card shows an icon + label + route. Selected one has a primary border.

Routes to show: Dashboard, Inventory Summary, Warehouse Stock, Sales Orders, Purchase Orders.

### 3.7 Notifications Section

Two large toggle switches (not checkboxes):
```jsx
function ToggleSwitch({ label, description, checked, onChange }) {
  return (
    <div className="flex items-start justify-between py-4 border-b border-warelyn-border last:border-0">
      <div>
        <p className="text-sm font-semibold text-warelyn-text">{label}</p>
        <p className="text-xs text-warelyn-muted mt-0.5">{description}</p>
      </div>
      <button type="button" onClick={() => onChange(!checked)}
        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors
          ${checked ? 'bg-warelyn-primary' : 'bg-gray-200'}`}
      >
        <span className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform
          ${checked ? 'translate-x-6' : 'translate-x-1'}`}
        />
      </button>
    </div>
  );
}
```

### 3.8 Documents / Template Preferences Section

Show two subsections: "Invoice Templates" and "Email Templates". Each shows radio cards for all available templates fetched from the API.

```jsx
// Fetch templates on mount
useEffect(() => {
  documentService.listTemplates(accessToken, 'PDF').then(setPdfTemplates);
  documentService.listTemplates(accessToken, 'EMAIL').then(setEmailTemplates);
}, [accessToken]);
```

For PDF templates — show the same `TemplateCard` thumbnail previews from `PdfTemplatesPage.jsx` (reuse the scaled iframe approach). For email templates — show a name card with subject preview.

The selected template ID is stored in `prefs.preferred_invoice_template_id` etc.

### 3.9 Backend Changes for H-07

**File: `backend/app/models/settings.py`**

Add to `UserPreferences`:
```python
preferred_invoice_template_id: Mapped[int | None] = mapped_column(
    ForeignKey("document_templates.id", ondelete="SET NULL"), nullable=True
)
preferred_bill_template_id: Mapped[int | None] = mapped_column(
    ForeignKey("document_templates.id", ondelete="SET NULL"), nullable=True
)
preferred_invoice_email_template_id: Mapped[int | None] = mapped_column(
    ForeignKey("document_templates.id", ondelete="SET NULL"), nullable=True
)
preferred_bill_email_template_id: Mapped[int | None] = mapped_column(
    ForeignKey("document_templates.id", ondelete="SET NULL"), nullable=True
)
```

**New Alembic migration:** `20260526_0015_user_preferences_template_fields.py`

**File: `backend/app/schemas/settings.py`**

Add the 4 new fields (all `int | None`) to both `UserPreferencesRead` and `UserPreferencesUpdate`.

### 3.10 Apply Preferences in Frontend After Login

**File: `frontend/src/context/AuthContext.jsx`**

After a successful `loadMe()`, fetch preferences and apply:
```js
const prefs = await settingsService.getUserPreferences(token);
// Apply landing page redirect (if not already on intended page)
if (prefs.default_landing_page && window.location.pathname === '/') {
  // the router will handle this — store in context
}
// Apply theme
const theme = prefs.theme_preference ?? 'light';
document.documentElement.setAttribute('data-theme', theme);
// Apply table density
document.documentElement.setAttribute('data-density', prefs.table_density ?? 'comfortable');
```

**File: `frontend/src/styles/index.css`**

Add CSS rules for `data-density`:
```css
[data-density="compact"] table th,
[data-density="compact"] table td { padding: 4px 8px; font-size: 11px; }

[data-density="spacious"] table th,
[data-density="spacious"] table td { padding: 16px 12px; }

/* Theme dark mode skeleton */
[data-theme="dark"] { --color-bg: #0F172A; --color-surface: #1E293B; --color-text: #F1F5F9; --color-muted: #94A3B8; --color-border: #334155; }
[data-theme="dark"] .sidebar { background: #020617; }
[data-theme="dark"] .topbar { background: #0F172A; }
```

---

## Section 4: New Email and PDF Templates (Full HTML)

### 4.1 Branded OTP Email Template

Replace `DEFAULT_TEMPLATES[(EMAIL, EMAIL_VERIFICATION)]["body_template"]` with:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Verification Code — Warelyn</title>
</head>
<body style="margin:0;padding:0;background-color:#F1F5F9;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F1F5F9;padding:40px 0;">
    <tr>
      <td align="center">
        <table role="presentation" width="560" cellpadding="0" cellspacing="0"
               style="background:#FFFFFF;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
          <!-- Header bar -->
          <tr>
            <td style="background:linear-gradient(135deg,#1E3A8A 0%,#2563EB 100%);padding:28px 40px;">
              <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td>
                    <p style="margin:0;font-size:22px;font-weight:700;color:#FFFFFF;letter-spacing:-0.5px;">Warelyn</p>
                    <p style="margin:4px 0 0;font-size:12px;color:rgba(255,255,255,0.7);letter-spacing:0.5px;text-transform:uppercase;">Inventory Platform</p>
                  </td>
                  <td align="right">
                    <div style="background:rgba(255,255,255,0.15);border-radius:50%;width:48px;height:48px;display:inline-flex;align-items:center;justify-content:center;">
                      <p style="margin:0;font-size:22px;">🔐</p>
                    </div>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <!-- Body -->
          <tr>
            <td style="padding:40px;">
              <p style="margin:0 0 8px;font-size:14px;color:#64748B;text-transform:uppercase;letter-spacing:1px;font-weight:600;">Security Code</p>
              <h1 style="margin:0 0 20px;font-size:28px;font-weight:700;color:#0F172A;line-height:1.2;">
                Verify your {{ purpose|lower }}
              </h1>
              <p style="margin:0 0 32px;font-size:15px;color:#475569;line-height:1.6;">
                Use the code below to complete your request. This code expires in <strong>{{ ttl_minutes }} minutes</strong>.
              </p>
              <!-- OTP Box -->
              <div style="background:linear-gradient(135deg,#EFF6FF,#DBEAFE);border:2px solid #BFDBFE;border-radius:12px;padding:28px;text-align:center;margin-bottom:32px;">
                <p style="margin:0 0 8px;font-size:11px;color:#3B82F6;font-weight:600;letter-spacing:2px;text-transform:uppercase;">Your Code</p>
                <p style="margin:0;font-size:40px;font-weight:800;letter-spacing:12px;color:#1E3A8A;font-variant-numeric:tabular-nums;">{{ code }}</p>
              </div>
              <p style="margin:0;font-size:13px;color:#94A3B8;text-align:center;line-height:1.5;">
                If you didn't request this, you can safely ignore this email.<br>
                Your account remains secure.
              </p>
            </td>
          </tr>
          <!-- Footer -->
          <tr>
            <td style="background:#F8FAFC;border-top:1px solid #E2E8F0;padding:20px 40px;">
              <p style="margin:0;font-size:12px;color:#94A3B8;text-align:center;">
                © Warelyn Inventory · Secure Verification System
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
```

### 4.2 Branded Invoice/Bill Email Template

Replace `DEFAULT_TEMPLATES[(EMAIL, INVOICE_SEND)]["body_template"]` and `(EMAIL, BILL_SEND)["body_template"]` with:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{ title }}</title>
</head>
<body style="margin:0;padding:0;background-color:#F1F5F9;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F1F5F9;padding:40px 0;">
    <tr>
      <td align="center">
        <table role="presentation" width="560" cellpadding="0" cellspacing="0"
               style="background:#FFFFFF;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
          <!-- Header -->
          <tr>
            <td style="background:linear-gradient(135deg,#1E3A8A 0%,#2563EB 100%);padding:28px 40px;">
              <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td>
                    <p style="margin:0;font-size:22px;font-weight:700;color:#FFFFFF;">{{ sender_name }}</p>
                    <p style="margin:4px 0 0;font-size:12px;color:rgba(255,255,255,0.7);">{{ document_kind }} Notification</p>
                  </td>
                  <td align="right" style="color:#FFFFFF;font-size:32px;">📄</td>
                </tr>
              </table>
            </td>
          </tr>
          <!-- Document badge -->
          <tr>
            <td style="padding:0 40px;">
              <div style="background:#EFF6FF;border-left:4px solid #1E3A8A;border-radius:0 8px 8px 0;padding:16px 20px;margin:28px 0 0;">
                <p style="margin:0;font-size:11px;color:#3B82F6;font-weight:700;letter-spacing:1px;text-transform:uppercase;">{{ document_kind }}</p>
                <p style="margin:4px 0 0;font-size:20px;font-weight:700;color:#0F172A;">{{ document_number }}</p>
              </div>
            </td>
          </tr>
          <!-- Body -->
          <tr>
            <td style="padding:24px 40px 40px;">
              <p style="margin:0 0 16px;font-size:15px;color:#475569;line-height:1.7;">{{ intro }}</p>
              {% if notes %}
              <div style="background:#FFFBEB;border:1px solid #FDE68A;border-radius:8px;padding:14px 18px;margin:16px 0;">
                <p style="margin:0;font-size:12px;color:#92400E;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">Notes</p>
                <p style="margin:6px 0 0;font-size:14px;color:#78350F;">{{ notes }}</p>
              </div>
              {% endif %}
              <p style="margin:24px 0 0;font-size:14px;color:#64748B;">
                Please find your {{ document_kind|lower }} attached as a PDF.
              </p>
            </td>
          </tr>
          <!-- Footer -->
          <tr>
            <td style="background:#F8FAFC;border-top:1px solid #E2E8F0;padding:20px 40px;">
              <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td>
                    <p style="margin:0;font-size:13px;color:#64748B;font-weight:500;">{{ sender_name }}</p>
                    <p style="margin:2px 0 0;font-size:12px;color:#94A3B8;">Sent via Warelyn Inventory</p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
```

### 4.3 PDF Template Variants (5 templates total)

Add these as additional `DocumentTemplate` DB records seeded in `_ensure_defaults()`. The current single invoice/bill template remains as "Classic". Add 4 more.

**Template naming convention in DEFAULT_TEMPLATES:**
- Each variant gets its own `DocumentTemplateKey`. 

**Add new keys to `DocumentTemplateKey` enum** in `models/documents.py`:
```python
class DocumentTemplateKey(str, enum.Enum):
    EMAIL_VERIFICATION = "EMAIL_VERIFICATION"
    INVOICE_SEND = "INVOICE_SEND"
    BILL_SEND = "BILL_SEND"
    PDF_INVOICE = "PDF_INVOICE"            # Classic (existing)
    PDF_INVOICE_MODERN = "PDF_INVOICE_MODERN"
    PDF_INVOICE_MINIMAL = "PDF_INVOICE_MINIMAL"
    PDF_INVOICE_BOLD = "PDF_INVOICE_BOLD"
    PDF_INVOICE_WARM = "PDF_INVOICE_WARM"
    PDF_BILL = "PDF_BILL"                  # Classic (existing)
    PDF_BILL_MODERN = "PDF_BILL_MODERN"
    PDF_BILL_MINIMAL = "PDF_BILL_MINIMAL"
    PDF_BILL_BOLD = "PDF_BILL_BOLD"
    PDF_BILL_WARM = "PDF_BILL_WARM"
```

**Template 2: Modern (two-tone sidebar)**
```html
<!DOCTYPE html><html>
<head><meta charset="utf-8"><style>
@page { size: A4; margin: 0; }
body { margin:0; font-family: 'Helvetica Neue', Arial, sans-serif; font-size:11px; color:#1E293B; }
.page { display:flex; min-height:297mm; }
.sidebar { width:64mm; background:#1E3A8A; padding:24mm 8mm 8mm; color:white; }
.sidebar h1 { font-size:16px; font-weight:800; letter-spacing:-0.5px; margin:0 0 4px; color:white; }
.sidebar .sub { font-size:9px; opacity:0.7; text-transform:uppercase; letter-spacing:1px; margin:0 0 24px; }
.sidebar .label { font-size:8px; text-transform:uppercase; letter-spacing:1px; opacity:0.6; margin:16px 0 4px; }
.sidebar .value { font-size:11px; color:white; font-weight:600; }
.sidebar .doc-num { font-size:22px; font-weight:800; color:#93C5FD; margin:0; }
.main { flex:1; padding:12mm 10mm; }
.bill-to { margin-bottom:12mm; }
.bill-to .heading { font-size:8px; text-transform:uppercase; letter-spacing:1px; color:#64748B; margin:0 0 6px; }
table.items { width:100%; border-collapse:collapse; margin:8mm 0; }
table.items thead tr { background:#EFF6FF; }
table.items th { padding:8px 6px; text-align:left; font-size:9px; text-transform:uppercase; letter-spacing:0.8px; color:#1E3A8A; border-bottom:2px solid #BFDBFE; }
table.items td { padding:8px 6px; border-bottom:1px solid #F1F5F9; }
.totals-block { margin-left:auto; width:180px; }
.totals-block table { width:100%; }
.totals-block td { padding:5px 0; font-size:11px; }
.totals-block td:last-child { text-align:right; font-weight:600; }
.total-row td { font-size:15px; font-weight:800; color:#1E3A8A; border-top:2px solid #BFDBFE; padding-top:10px; }
.footer { margin-top:8mm; font-size:9px; color:#94A3B8; }
</style></head>
<body>
<div class="page">
  <div class="sidebar">
    <h1>{{ tenant.company_name }}</h1>
    <p class="sub">Inventory Platform</p>
    <p class="label">Invoice</p>
    <p class="doc-num">{{ invoice.invoice_number }}</p>
    <p class="label">Date</p><p class="value">{{ invoice.invoice_date }}</p>
    {% if invoice.due_date %}<p class="label">Due Date</p><p class="value">{{ invoice.due_date }}</p>{% endif %}
    {% if sales_order %}<p class="label">Sales Order</p><p class="value">{{ sales_order.so_number }}</p>{% endif %}
    <p class="label">Status</p><p class="value">{{ invoice.invoice_number }}</p>
    <br><br>
    <p class="label">Bill To</p>
    <p class="value">{{ customer.name }}</p>
    {% if customer.email %}<p class="value" style="font-size:9px;opacity:0.8;">{{ customer.email }}</p>{% endif %}
    {% if customer.phone %}<p class="value" style="font-size:9px;opacity:0.8;">{{ customer.phone }}</p>{% endif %}
  </div>
  <div class="main">
    <div style="margin-bottom:6mm;">
      <p style="margin:0;font-size:28px;font-weight:800;color:#1E3A8A;letter-spacing:-1px;">INVOICE</p>
    </div>
    <table class="items">
      <thead><tr>
        <th>Item</th><th>Warehouse</th><th>Qty</th><th>Rate</th><th>Tax</th><th>Amount</th>
      </tr></thead>
      <tbody>
        {% for item in items %}
        <tr>
          <td>{{ item.product_name }}</td>
          <td style="color:#64748B;">{{ item.warehouse_name }}</td>
          <td>{{ item.quantity }}</td>
          <td>{{ item.unit_price }}</td>
          <td style="color:#64748B;">{{ item.tax_rate }}%</td>
          <td style="font-weight:600;">{{ item.total_price }}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
    <div class="totals-block">
      <table>
        <tr><td>Subtotal</td><td>{{ invoice.subtotal }}</td></tr>
        <tr><td>Tax</td><td>{{ invoice.tax_amount }}</td></tr>
        <tr><td>Discount</td><td>{{ invoice.discount_amount }}</td></tr>
        <tr class="total-row"><td>Total</td><td>{{ invoice.total_amount }}</td></tr>
      </table>
    </div>
    {% if invoice.notes %}
    <div style="margin-top:8mm;padding:10px;background:#FFFBEB;border-radius:6px;">
      <p style="margin:0;font-size:10px;color:#92400E;font-weight:600;">Notes</p>
      <p style="margin:4px 0 0;font-size:11px;color:#78350F;">{{ invoice.notes }}</p>
    </div>
    {% endif %}
    <div class="footer">{{ tenant.footer }}</div>
  </div>
</div>
</body></html>
```

**Template 3: Minimal (clean white, thin lines)**
```html
<!DOCTYPE html><html>
<head><meta charset="utf-8"><style>
@page { size: A4; margin: 20mm 16mm; }
body { font-family: Georgia, 'Times New Roman', serif; font-size:11px; color:#1E293B; }
.top { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:16mm; border-bottom:0.5px solid #CBD5E1; padding-bottom:8mm; }
.company-name { font-size:24px; font-weight:bold; letter-spacing:-1px; color:#0F172A; margin:0; }
.invoice-title { text-align:right; }
.invoice-title h2 { font-size:28px; font-weight:300; letter-spacing:4px; color:#CBD5E1; margin:0; text-transform:uppercase; }
.invoice-title .num { font-size:14px; font-weight:bold; color:#1E3A8A; }
.parties { display:flex; gap:20mm; margin-bottom:12mm; }
.party { flex:1; }
.party .label { font-size:8px; text-transform:uppercase; letter-spacing:2px; color:#94A3B8; margin:0 0 6px; }
.party .name { font-size:13px; font-weight:bold; color:#0F172A; }
table { width:100%; border-collapse:collapse; margin:8mm 0; }
thead tr th { font-size:8px; text-transform:uppercase; letter-spacing:1.5px; color:#94A3B8; padding:8px 0; text-align:left; border-bottom:0.5px solid #E2E8F0; }
tbody tr td { padding:10px 0; border-bottom:0.5px solid #F1F5F9; font-size:11px; }
.totals { width:200px; margin-left:auto; margin-top:4mm; }
.totals table td { padding:4px 0; font-size:11px; }
.totals table td:last-child { text-align:right; }
.grand-total td { font-size:16px; font-weight:bold; color:#0F172A; border-top:1px solid #1E293B; padding-top:8px; }
</style></head>
<body>
<div class="top">
  <div>
    <p class="company-name">{{ tenant.company_name }}</p>
    <p style="margin:4px 0 0;font-size:11px;color:#94A3B8;">{{ tenant.contact_email }}</p>
  </div>
  <div class="invoice-title">
    <h2>Invoice</h2>
    <p class="num">{{ invoice.invoice_number }}</p>
    <p style="font-size:11px;color:#64748B;margin:4px 0 0;">{{ invoice.invoice_date }}</p>
  </div>
</div>
<div class="parties">
  <div class="party"><p class="label">Bill To</p>
    <p class="name">{{ customer.name }}</p>
    <p style="color:#64748B;font-size:10px;margin:2px 0;">{{ customer.email or '' }}</p>
  </div>
  {% if invoice.due_date %}
  <div class="party"><p class="label">Due Date</p><p class="name">{{ invoice.due_date }}</p></div>
  {% endif %}
</div>
<table>
  <thead><tr><th>Description</th><th>Qty</th><th>Rate</th><th>Tax</th><th style="text-align:right;">Amount</th></tr></thead>
  <tbody>
    {% for item in items %}
    <tr>
      <td>{{ item.product_name }}</td>
      <td>{{ item.quantity }}</td>
      <td>{{ item.unit_price }}</td>
      <td style="color:#94A3B8;">{{ item.tax_rate }}%</td>
      <td style="text-align:right;">{{ item.total_price }}</td>
    </tr>
    {% endfor %}
  </tbody>
</table>
<div class="totals">
  <table>
    <tr><td style="color:#64748B;">Subtotal</td><td>{{ invoice.subtotal }}</td></tr>
    <tr><td style="color:#64748B;">Tax</td><td>{{ invoice.tax_amount }}</td></tr>
    <tr><td style="color:#64748B;">Discount</td><td>({{ invoice.discount_amount }})</td></tr>
    <tr class="grand-total"><td>Total</td><td>{{ invoice.total_amount }}</td></tr>
  </table>
</div>
{% if invoice.notes %}<p style="margin-top:8mm;font-size:10px;color:#94A3B8;"><em>{{ invoice.notes }}</em></p>{% endif %}
<p style="margin-top:12mm;font-size:9px;color:#CBD5E1;border-top:0.5px solid #E2E8F0;padding-top:4mm;">{{ tenant.footer }}</p>
</body></html>
```

**Template 4: Bold (dark header, strong colors)** and **Template 5: Warm (earthy tones)** follow the same structural pattern with these color adjustments:
- Bold: `background:#0F172A` header, `color:#F59E0B` accent, white text on header
- Warm: `background:#7C2D12` header, `color:#D97706` accent, `background:#FFFBEB` body tint

Each invoice template must have a corresponding bill template variant (same HTML structure, with `bill.*` variables instead of `invoice.*` and `vendor` instead of `customer`).

---

## Section 5: Reports Crash Fix — Exact Code Changes

### 5.1 Fix `SimpleReportPage` null guard

**File:** `frontend/src/pages/ReportsPage.jsx`

In `SimpleReportPage`, find the `return` statement. The `summary` prop is rendered directly without checking if `data` is non-null. Current code:

```jsx
{summary ? <div className="mb-4">{summary(data)}</div> : null}
```

Change to:
```jsx
{summary && data !== null && data !== undefined
  ? <div className="mb-4">{summary(data)}</div>
  : null}
```

Also add a guard before `sourceRows` computation. Currently:
```jsx
const sourceRows = loadRows ? loadRows(data) : data;
```

Change to:
```jsx
const sourceRows = data === null || data === undefined
  ? []
  : loadRows ? loadRows(data) : data;
```

### 5.2 Fix `InventorySummaryReportPage.jsx`

The backend returns `InventorySummaryReport` (an object, not an array). The page tries to render it as a table. Fix: add `loadRows={() => []}` so the table is empty, and let `summary` be the only display.

```jsx
export function InventorySummaryReportPage() {
  return (
    <SimpleReportPage
      title="Inventory summary"
      description="Backend-calculated inventory KPIs and exception counts."
      load={reportsService.getInventorySummary}
      columns={[]}
      loadRows={() => []}
      summary={(data) => (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {data && Object.entries(data).map(([key, value]) => (
            <Card key={key}>
              <CardBody>
                <p className="text-xs font-semibold uppercase tracking-wide text-warelyn-muted">
                  {key.replaceAll('_', ' ')}
                </p>
                <p className="mt-1 text-2xl font-bold text-warelyn-text">
                  {typeof value === 'object' ? String(value) : value}
                </p>
              </CardBody>
            </Card>
          ))}
        </div>
      )}
    />
  );
}
```

### 5.3 Fix remaining non-array report pages

**`InventorySummaryReportPage.jsx`** — add `loadRows={() => []}` ✅ (above)

**`ProductValuationReportPage.jsx`** — already has `loadRows={(data) => data?.rows ?? []}` — only needs the `summary` null guard from 5.1.

**`ReconciliationReportPage.jsx`** — already has `loadRows={(data) => data?.mismatches ?? []}` — only needs the `summary` null guard from 5.1.

All array-returning report pages (`WarehouseStockReportPage`, `LocationStockReportPage`, `StockMovementReportPage`, `LowStockReportPage`, `ReorderSuggestionsPage`, `BatchExpiryReportPage`, `SerialStatusReportPage`, `BlockedStockReportPage`) — these receive arrays so `sourceRows` is already an array. They don't crash but also need the `data !== null` guard on the summary.

---

## Section 6: Remaining Backend Fixes

### 6.1 Fix H-01: `tax_rate` in Item Context

**File:** `backend/app/services/documents.py → _invoice_context()`

In the items list comprehension, replace:
```python
"tax_rate": "0",
```

With:
```python
"tax_rate": (
    str(round(float(item.tax_amount) / float(item.line_total) * 100, 1))
    if item.line_total and float(item.line_total) > 0 and item.tax_amount
    else "0"
),
```

Apply the same logic in `_bill_context()` for `BillItem.tax_amount` / `BillItem.line_total`.

### 6.2 Fix H-02: `warehouse_name` in Item Context

**File:** `backend/app/services/documents.py → _invoice_context()`

After building the basic items list, attempt to enrich warehouse names from fulfillment items:
```python
# After building items list:
if invoice.fulfillment_id:
    fulfillment = self.repository.get_fulfillment(invoice.tenant_id, invoice.fulfillment_id)
    if fulfillment:
        for fi in fulfillment.items:
            if fi.location_id:
                location = self.repository.get_location(invoice.tenant_id, fi.location_id)
                if location:
                    warehouse = self.repository.get_warehouse(invoice.tenant_id, location.warehouse_id)
                    # Match to item by product_id
                    for item in items:
                        if item["product_name"] and warehouse:
                            item["warehouse_name"] = warehouse.name
                            break
```

This requires `get_location()` and `get_warehouse()` to be accessible from `DocumentsRepository`. Verify these methods exist in `repositories/documents.py`; if not, add:
```python
def get_location(self, tenant_id: int, location_id: int):
    from app.models.master_data import WarehouseLocation
    return self.db.scalar(select(WarehouseLocation).where(
        WarehouseLocation.id == location_id,
        WarehouseLocation.tenant_id == tenant_id
    ))

def get_warehouse(self, tenant_id: int, warehouse_id: int):
    from app.models.master_data import Warehouse
    return self.db.scalar(select(Warehouse).where(
        Warehouse.id == warehouse_id,
        Warehouse.tenant_id == tenant_id
    ))
```

### 6.3 Fix H-08: XLSX Template Static Method

**File:** `backend/app/services/imports.py`

Verify `build_template_xlsx` has the `@staticmethod` decorator:
```python
@staticmethod
def build_template_xlsx() -> bytes:
    # existing implementation
```

If the method does not exist yet, add it:
```python
@staticmethod
def build_template_xlsx() -> bytes:
    """Generate a minimal XLSX file with correct import headers for download."""
    headers = ["name", "sku", "unit", "barcode", "description",
               "category_name", "brand_name", "vendor_name",
               "cost_price", "selling_price", "reorder_level",
               "track_batch", "track_expiry", "track_serial", "status"]
    # Build XLSX using the existing hand-rolled XML writer from _parse_xlsx
    # Use openpyxl if available; otherwise use the ZipFile/XML approach
    try:
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Products Import"
        for col, header in enumerate(headers, 1):
            ws.cell(row=1, column=col, value=header)
        # Add one sample row
        sample = ["Sample Product", "SKU-001", "pcs", "", "A sample product",
                  "Electronics", "Acme Brand", "Sample Vendor",
                  "100.00", "150.00", "10", "false", "false", "false", "active"]
        for col, value in enumerate(sample, 1):
            ws.cell(row=2, column=col, value=value)
        import io
        buffer = io.BytesIO()
        wb.save(buffer)
        return buffer.getvalue()
    except ImportError:
        # Fall back to minimal XLSX XML
        return _build_minimal_xlsx(headers)
```

---

## Section 7: Phase Execution Order

### PHASE 19 — Reports Crash Fix + Back Buttons + Nav Icons

**Priority:** P0 (reports are completely broken — users can't use any report)  
**Files changed:** 14 frontend files  
**Test target:** 218 → ~222  
**Estimated time:** 2–3 hours

**Step-by-step:**

1. Fix `SimpleReportPage` null guard (Section 5.1) — 2 lines changed
2. Fix `InventorySummaryReportPage.jsx` (Section 5.2) — replace component
3. Add `summary` null guard to `ProductValuationReportPage.jsx` and `ReconciliationReportPage.jsx` (Section 5.3)
4. Add `<BackButton>` to all pages in the map (Section 2.2) — add import + one line per page
5. Replace all nav icons (Section 2.1) — update `navigation.js` only

**Validation:** Navigate to every report page. None should crash. All should show `LoadingState` while fetching and then data. Every detail page should show a back arrow at the top.

---

### PHASE 20 — Email + PDF Templates (Branded)

**Priority:** P1  
**Files changed:** 3 backend files  
**Test target:** 222 → ~230

**Step-by-step:**

1. Replace OTP email `body_template` in `DEFAULT_TEMPLATES` with Section 4.1 HTML
2. Replace INVOICE_SEND and BILL_SEND `body_template` with Section 4.2 HTML
3. Add `DocumentTemplateKey` enum values for 4 new PDF variants (Section 4.3)
4. Add 4 invoice PDF variants + 4 bill PDF variants to `DEFAULT_TEMPLATES` (Section 4.3)
5. Update `_ensure_defaults()` to seed all new template keys
6. **CRITICAL:** Because `_ensure_defaults` runs once per tenant and old records already exist, existing tenants will NOT get the new templates. Add an `update_if_default` flag: if the template `body_template` has not been modified since creation (by checking `updated_at == created_at`), update it to the new default.
7. Add new Alembic migration for the 8 new `DocumentTemplateKey` enum values if MySQL enforces the enum (it does when `native_enum=False` with CHECK constraints — verify and add migration if needed)

**New tests to add:**
- `test_otp_email_template_contains_gradient_header` — rendered HTML contains `linear-gradient`
- `test_invoice_email_body_contains_document_number`
- `test_pdf_modern_template_renders_sidebar_layout`
- `test_pdf_minimal_template_renders_georgia_font`
- `test_all_5_pdf_invoice_templates_seed_for_new_tenant`
- `test_all_5_pdf_bill_templates_seed_for_new_tenant`
- `test_legacy_templates_updated_on_ensure_defaults`

---

### PHASE 21 — PDF Context Fixes + XLSX Download

**Priority:** P1  
**Files changed:** 3 backend files  
**Test target:** 230 → ~238

**Step-by-step:**

1. Fix `tax_rate` computation (Section 6.1)
2. Add `get_location` + `get_warehouse` to `DocumentsRepository` (Section 6.2)
3. Enrich `warehouse_name` from fulfillment (Section 6.2)
4. Verify / fix `build_template_xlsx()` static method (Section 6.3)
5. Add `openpyxl==3.1.3` to `requirements.txt` for XLSX template generation

**New tests:**
- `test_invoice_item_tax_rate_computed_from_tax_amount`
- `test_invoice_pdf_warehouse_name_populated_from_fulfillment`
- `test_xlsx_template_download_returns_200_with_valid_file`
- `test_xlsx_template_has_all_required_header_columns`
- `test_xlsx_template_has_sample_row`

---

### PHASE 22 — Preferences Redesign + Template Selection + Persistence

**Priority:** P1  
**Files changed:** 5 files (2 backend, 3 frontend)  
**Test target:** 238 → ~248

**Backend Step-by-step:**

1. Add 4 new FK columns to `UserPreferences` model (Section 3.9)
2. Create migration `20260526_0015_user_preferences_template_fields.py`
3. Add fields to `UserPreferencesRead` and `UserPreferencesUpdate` schemas
4. No service change needed — existing `update_preferences()` handles new fields via `setattr` loop

**Frontend Step-by-step:**

1. Rewrite `UserPreferencesSection` in `SettingsPage.jsx` (Section 3.3–3.8):
   - New imports: `Bell, Home, LayoutList, Monitor, Moon, Palette, Sun` from lucide-react
   - Left-sidebar + right-panel layout (Section 3.2)
   - `ThemeCard` component (Section 3.4)
   - `DensityToggle` component (Section 3.5)
   - `ToggleSwitch` component for notifications (Section 3.7)
   - Template selection using iframe thumbnails for PDF, name cards for email (Section 3.8)

2. Apply preferences on login in `AuthContext.jsx` (Section 3.10):
   - After `loadMe()` succeeds, call `settingsService.getUserPreferences(token)`
   - Set `document.documentElement.setAttribute('data-theme', prefs.theme_preference)`
   - Set `document.documentElement.setAttribute('data-density', prefs.table_density)`
   - Store `prefs.default_landing_page` in auth context as `defaultLandingPage`

3. In `frontend/src/routes/AppRoutes.jsx`, add redirect logic:
   ```jsx
   // When user first lands on '/' while authenticated, redirect to their preferred landing page
   import { useAuth } from '../context/AuthContext';
   // In a ProtectedRoute wrapper component:
   const { user, prefs } = useAuth();
   if (user && location.pathname === '/') {
     return <Navigate to={prefs?.defaultLandingPage ?? '/dashboard'} replace />;
   }
   ```

4. Add CSS for dark theme and density in `styles/index.css` (Section 3.10)

**New tests:**
- `test_user_preferences_preferred_invoice_template_id_stored`
- `test_user_preferences_preferred_bill_template_id_stored`
- `test_user_preferences_nullable_template_fields_default_null`
- `test_user_preferences_migration_runs_clean`

---

### PHASE 23 — Email Template Editor Toolbar

**Priority:** P2  
**Files changed:** 1 frontend file  
**Test target:** 248 → ~250

**File:** `frontend/src/pages/EmailTemplatesPage.jsx`

The editor textarea needs a formatting toolbar that operates on the `body_template` HTML content. Since `body_template` stores HTML, the toolbar must insert HTML tags around selected text.

**Toolbar implementation (no external library — pure DOM):**

```jsx
function FormatToolbar({ textareaRef, onBodyChange, body }) {
  function applyFormat(openTag, closeTag) {
    const el = textareaRef.current;
    if (!el) return;
    const start = el.selectionStart;
    const end = el.selectionEnd;
    const selected = body.substring(start, end);
    const newBody = body.substring(0, start) + openTag + selected + closeTag + body.substring(end);
    onBodyChange(newBody);
    setTimeout(() => {
      el.selectionStart = start + openTag.length;
      el.selectionEnd = start + openTag.length + selected.length;
      el.focus();
    }, 0);
  }

  const tools = [
    { label: 'B', title: 'Bold', open: '<strong>', close: '</strong>', style: 'font-weight:bold' },
    { label: 'I', title: 'Italic', open: '<em>', close: '</em>', style: 'font-style:italic' },
    { label: 'U', title: 'Underline', open: '<u>', close: '</u>', style: 'text-decoration:underline' },
    { label: 'S', title: 'Strikethrough', open: '<s>', close: '</s>', style: 'text-decoration:line-through' },
  ];

  return (
    <div className="flex items-center gap-1 border-b border-warelyn-border bg-gray-50 px-3 py-2 rounded-t-lg">
      {tools.map((tool) => (
        <button
          key={tool.label}
          type="button"
          title={tool.title}
          style={tool.style}
          className="px-2 py-1 text-sm rounded hover:bg-warelyn-border transition text-warelyn-text"
          onClick={() => applyFormat(tool.open, tool.close)}
        >
          {tool.label}
        </button>
      ))}
      <div className="w-px h-4 bg-warelyn-border mx-1" />
      {/* Insert Placeholder dropdown — existing component */}
      <PlaceholderDropdown
        vars={PLACEHOLDER_VARS[selected?.template_key] ?? []}
        onInsert={(ph) => insertAtCursor(ph)}
      />
    </div>
  );
}
```

Place `<FormatToolbar>` immediately above the `<textarea>` for `body_template`.

---

### PHASE 24 — Final Hardening (Deploy Readiness)

**Priority:** P0 for production  
**Files changed:** Dockerfile, docker-compose.yml, `.env.example`, `requirements.txt`, README  
**Test target:** 250 → ~250 (no new features, just infra)

**Step-by-step:**

1. **Dockerfile font fix** — WeasyPrint requires system fonts. Add to `Dockerfile`:
   ```dockerfile
   RUN apt-get update && apt-get install -y \
       fonts-liberation \
       fonts-dejavu-core \
       libpango-1.0-0 \
       libpangocairo-1.0-0 \
       libgdk-pixbuf2.0-0 \
       && rm -rf /var/lib/apt/lists/*
   ```

2. **Production `.env.example` hardening** — add:
   ```
   WARELYN_EMAIL_DELIVERY_MODE=mailhog  # change to "smtp" in production
   WARELYN_SEED_SUPER_ADMIN_ON_STARTUP=true  # only for first deploy
   ```

3. **CORS production lock** — `WARELYN_CORS_ORIGINS` must be set to exact frontend domain in production. Add a startup check in `main.py`:
   ```python
   if not settings.debug and "*" in settings.cors_origins:
       raise RuntimeError("CORS wildcard not allowed in production. Set WARELYN_CORS_ORIGINS explicitly.")
   ```

4. **JWT secret check** — add startup validation:
   ```python
   if settings.jwt_secret_key in ("replace-with-a-long-random-secret", "changeme", ""):
       raise RuntimeError("JWT_SECRET_KEY must be changed from default before production.")
   ```

5. **Database connection pool** — in `db/session.py`, add:
   ```python
   engine = create_engine(
       settings.database_url,
       pool_pre_ping=True,        # detect stale connections
       pool_size=10,
       max_overflow=20,
       pool_timeout=30,
       pool_recycle=3600,         # recycle connections every hour
   )
   ```

6. **Rate limiting** — add `slowapi` to `requirements.txt` and apply to auth endpoints:
   ```python
   from slowapi import Limiter, _rate_limit_exceeded_handler
   from slowapi.util import get_remote_address
   limiter = Limiter(key_func=get_remote_address)
   app.state.limiter = limiter
   
   # On login route:
   @router.post("/login")
   @limiter.limit("10/minute")
   def login(...): ...
   
   # On OTP send:
   @router.post("/verification/email/send")
   @limiter.limit("5/minute")
   def send_email_verification(...): ...
   ```

7. **Add openpyxl to requirements.txt** for XLSX template generation: `openpyxl==3.1.3`

---

## Section 8: Additional UI/UX Improvements (Bonus Recommendations)

These are suggested improvements beyond the reported bugs. Implement in Phase 24 or later.

### 8.1 Dashboard KPI Cards — Add Sparkline Trend Arrows
The dashboard currently shows flat numbers. Add trend indicators: compare current week vs prior week for stock counts and orders. Show a small colored arrow (↑ green / ↓ red) next to key metrics. Backend: add a `?compare_previous=true` query param to the dashboard endpoint.

### 8.2 Global Search — Search Across Entities
The current topbar search only navigates to pages. Implement actual API-backed search:
- `GET /search?q=term&types=product,customer,vendor,invoice` endpoint returning unified results
- Frontend: show search results dropdown with grouped sections (Products, Customers, Orders)

### 8.3 Notification Toast Queue — Add Action Buttons
Current toasts are dismissible only. For key toasts (e.g. "Invoice generated"), add an "Open" action button that navigates to the related entity.

### 8.4 Table Keyboard Navigation
Add `tabIndex`, `onKeyDown` handlers to table rows so power users can navigate rows with arrow keys and press Enter to open a detail.

### 8.5 Inventory Dashboard — Low Stock Alert Banner
When `low_stock_count > 0`, show a persistent amber banner at the top of the dashboard: "⚠ {n} products below reorder level — View Report". This surfaces the most actionable information immediately.

### 8.6 Document PDF — Print-Specific CSS
Add `@media print` CSS to the PDF templates so users can also print from the browser:
```css
@media print {
  .no-print { display: none; }
  body { margin: 0; }
}
```

### 8.7 Settings Page — Logo Upload (Not Just URL)
The current logo field is a URL input. Add a file picker that uploads the logo to a temporary URL (or base64 encodes it for PDF templates). This requires an `POST /uploads/logo` endpoint returning a URL.

### 8.8 Mobile Responsive Audit
Several pages have tables that overflow on mobile. Add `overflow-x-auto` wrapper around all `<TableShell>` usages on list pages. The sidebar should collapse by default on mobile.

### 8.9 Error Boundary
Wrap the main `<App>` in a React ErrorBoundary that shows a branded error page instead of a white screen on unhandled exceptions. Show "Something went wrong — Refresh the page" with the Warelyn logo.

### 8.10 Empty State Illustrations
Current empty states show a text message. Add subtle SVG illustrations for key empty states: no products (warehouse box illustration), no orders (clipboard illustration), no notifications (bell illustration). These can be inline SVGs using Warelyn brand colors.

---

## Section 9: Final Test Count Target

| After Phase | Tests | New Tests | Key Changes |
|-------------|-------|-----------|-------------|
| Phase 18 baseline | 218 | — | — |
| Phase 19 | 222 | +4 | Report crash guard, back buttons, nav icons |
| Phase 20 | 230 | +8 | Branded email/PDF templates, 5-variant seeding |
| Phase 21 | 238 | +8 | Tax rate, warehouse name, XLSX download |
| Phase 22 | 248 | +10 | Preferences migration, template FK, persistence |
| Phase 23 | 250 | +2 | Editor toolbar |
| Phase 24 | 250 | 0 | Deploy hardening (infra changes, no new API) |

---

## Appendix A: Files Changed Per Phase (Exact List)

### Phase 19
- `frontend/src/pages/ReportsPage.jsx` — null guard in SimpleReportPage
- `frontend/src/pages/InventorySummaryReportPage.jsx` — loadRows fix
- `frontend/src/pages/ProductValuationReportPage.jsx` — summary null guard
- `frontend/src/pages/ReconciliationReportPage.jsx` — summary null guard
- `frontend/src/components/navigation.js` — all icon replacements
- `frontend/src/pages/PurchaseOrderDetailPage.jsx` — add BackButton
- `frontend/src/pages/PurchaseOrderFormPage.jsx` — add BackButton
- `frontend/src/pages/PurchaseReceiptDetailPage.jsx` — add BackButton
- `frontend/src/pages/PurchaseReceivePage.jsx` — add BackButton
- `frontend/src/pages/SalesOrderDetailPage.jsx` — add BackButton
- `frontend/src/pages/SalesOrderFormPage.jsx` — add BackButton
- `frontend/src/pages/SalesReturnDetailPage.jsx` — add BackButton
- `frontend/src/pages/SalesReturnFormPage.jsx` — add BackButton
- `frontend/src/pages/SalesReturnInspectPage.jsx` — add BackButton
- `frontend/src/pages/SalesFulfillPage.jsx` — add BackButton
- `frontend/src/pages/SalesFulfillmentDetailPage.jsx` — add BackButton
- `frontend/src/pages/SalesPickPage.jsx` — add BackButton
- `frontend/src/pages/SalesPackagePage.jsx` — add BackButton
- `frontend/src/pages/PickTaskDetailPage.jsx` — add BackButton
- `frontend/src/pages/PackageDetailPage.jsx` — add BackButton
- `frontend/src/pages/WarehouseDetailPage.jsx` — add BackButton
- `frontend/src/pages/TenantDetailPage.jsx` — add BackButton
- `frontend/src/pages/ProductImportPage.jsx` — add BackButton
- `frontend/src/pages/VerifyEmailPage.jsx` — add BackButton
- `frontend/src/pages/VerifyPhonePage.jsx` — add BackButton
- `frontend/src/pages/AuditLogsPage.jsx` — add BackButton
- `frontend/src/pages/PlatformHealthPage.jsx` — add BackButton
- `frontend/src/pages/EmailTemplatesPage.jsx` — add BackButton
- `frontend/src/pages/PdfTemplatesPage.jsx` — add BackButton
- `frontend/src/pages/CatalogMasterPages.jsx` — add BackButton to all FormPage components

### Phase 20
- `backend/app/models/documents.py` — add 8 new DocumentTemplateKey enum values
- `backend/app/services/documents.py` — replace DEFAULT_TEMPLATES with branded HTML
- `backend/alembic/versions/20260526_0014_document_template_key_expansion.py` — NEW migration
- `backend/tests/test_phase20_branded_templates.py` — NEW test file with 7 tests

### Phase 21
- `backend/app/services/documents.py` — fix tax_rate, add warehouse_name lookup
- `backend/app/repositories/documents.py` — add get_location, get_warehouse methods
- `backend/app/services/imports.py` — add/fix build_template_xlsx static method
- `backend/requirements.txt` — add openpyxl==3.1.3
- `backend/tests/test_phase21_document_context.py` — NEW test file with 5 tests

### Phase 22
- `backend/app/models/settings.py` — add 4 FK fields to UserPreferences
- `backend/app/schemas/settings.py` — add 4 fields to Read/Update schemas
- `backend/alembic/versions/20260526_0015_user_preferences_template_fields.py` — NEW migration
- `frontend/src/pages/SettingsPage.jsx` — complete UserPreferencesSection rewrite
- `frontend/src/context/AuthContext.jsx` — apply preferences after login
- `frontend/src/styles/index.css` — dark theme + density CSS tokens
- `frontend/src/routes/AppRoutes.jsx` — landing page redirect logic
- `backend/tests/test_phase22_preferences.py` — NEW test file with 4 tests

### Phase 23
- `frontend/src/pages/EmailTemplatesPage.jsx` — add FormatToolbar component

### Phase 24
- `Dockerfile` — font dependencies
- `backend/.env.example` — production hints
- `backend/app/main.py` — CORS and JWT startup validation
- `backend/app/db/session.py` — connection pool config
- `backend/requirements.txt` — add slowapi
- `backend/app/api/auth.py` — rate limit on /login
- `backend/app/api/verification.py` — rate limit on /verification/email/send
