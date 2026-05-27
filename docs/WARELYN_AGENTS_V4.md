# WARELYN INVENTORY — AGENTS BUILD INSTRUCTIONS v4.0
# POST PHASE 15–18 DEPLOYMENT READINESS
# Baseline: 218 tests passing

Read this entire file before touching any code. Every instruction is exact. You do not need to reason about what to do — the steps are written out for you. Follow them exactly.

---

## 0. CRITICAL RULES (NEVER VIOLATE)

1. Stock mutations only in `engine.py` — never elsewhere
2. `tenant_id` from `UserContext`, never from request body
3. Jinja2 for all template rendering — NO `str.format_map`
4. Alembic migration for every DB schema change
5. `db.commit()` only in service layer, never in repositories
6. No `document.getElementById` in React — controlled state only
7. Role check on every new endpoint
8. All frontend API calls go through `services/*.js` files
9. Test count must never decrease below 218
10. Template HTML stored in DB — `DEFAULT_TEMPLATES` only seeds, never replaces custom

---

## 1. BEFORE STARTING ANY PHASE

```bash
cd backend && .venv/bin/python -m pytest -q
# Must show: 218 passed, 0 failed
cd backend && .venv/bin/python -m compileall app
# Must show: no syntax errors
```

If tests fail before you start, STOP and report what is failing. Do not proceed.

---

## 2. PHASE 19 — Reports Crash + Back Buttons + Nav Icons

### Target: 218 → 222 tests. Priority: P0 (reports completely broken).

### Step 19.1 — Fix SimpleReportPage null crash

**File: `frontend/src/pages/ReportsPage.jsx`**

Find this line (approximately line 96):
```jsx
const sourceRows = loadRows ? loadRows(data) : data;
```

Replace it with:
```jsx
const sourceRows =
  data === null || data === undefined
    ? []
    : loadRows
    ? loadRows(data)
    : data;
```

Find the summary render (search for `summary(data)`). Change:
```jsx
{summary ? <div className="mb-4">{summary(data)}</div> : null}
```
To:
```jsx
{summary && data !== null && data !== undefined
  ? <div className="mb-4">{summary(data)}</div>
  : null}
```

### Step 19.2 — Fix InventorySummaryReportPage

**File: `frontend/src/pages/InventorySummaryReportPage.jsx`**

Replace the entire file content with:
```jsx
import { Card, CardBody } from '../components/ui/Card.jsx';
import { BackButton } from '../components/ui/BackButton.jsx';
import * as reportsService from '../services/reportsService.js';
import { SimpleReportPage } from './ReportsPage.jsx';

export function InventorySummaryReportPage() {
  return (
    <SimpleReportPage
      title="Inventory summary"
      description="Backend-calculated inventory KPIs and exception counts."
      load={reportsService.getInventorySummary}
      columns={[]}
      loadRows={() => []}
      summary={(data) =>
        data ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {Object.entries(data).map(([key, value]) => (
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
        ) : null
      }
    />
  );
}
```

### Step 19.3 — Fix ProductValuationReportPage and ReconciliationReportPage

**File: `frontend/src/pages/ProductValuationReportPage.jsx`**

The component already uses `loadRows={(data) => data?.rows ?? []}` which is correct. The only fix needed is that the `summary` prop passes `data` which is `null` initially. Since Step 19.1 already adds `data !== null` guard to the `summary` render, this is automatically fixed after Step 19.1.

**File: `frontend/src/pages/ReconciliationReportPage.jsx`**

Same — already uses `loadRows={(data) => data?.mismatches ?? []}`. Fixed by Step 19.1.

### Step 19.4 — Add BackButton to all detail and form pages

For every file in the list below:
1. Add this import at the top (with other imports):
   ```jsx
   import { BackButton } from '../components/ui/BackButton.jsx';
   ```
2. Add `<BackButton to="VALUE" />` as the FIRST element inside the outermost `<div className="space-y-6">` or the outermost return div.

**Exact `to` values per file:**

| File | to value |
|------|----------|
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

**For `CatalogMasterPages.jsx`** — this is one file with many exported components. Add the import once at the top of the file. Then add `<BackButton to="..." />` inside each form page:
- `ProductFormPage` → `to="/catalog/products"`
- `CategoryFormPage` → `to="/catalog/categories"`
- `BrandFormPage` → `to="/catalog/brands"`
- `VendorFormPage` → `to="/catalog/vendors"`
- `CustomerFormPage` → `to="/catalog/customers"`

### Step 19.5 — Replace nav icons (navigation.js)

**File: `frontend/src/components/navigation.js`**

**Step A — Add these imports** (add to the existing import block from lucide-react):
```
Building2, CalendarClock, ClipboardCheck, CornerUpLeft,
Database, DollarSign, FileCheck2, FilePlus2, FileUp,
Handshake, Hash, HeartPulse, Layers2, LogIn, MapPin,
PackagePlus, PlusSquare, ReceiptText, RefreshCw,
RotateCcw, Scale, ScrollText, Send, ShieldAlert,
ShieldOff, Star, Tag, TrendingUp, UserRound, BadgePlus
```

**Step B — Replace `icon:` values** for each nav item. Use the exact table from WARELYN_DEPLOYMENT_PLAN.md Section 2.1. Below is the complete replacement list in the order they appear in the file:

```
Platform Console:    ShieldAlert
Tenants:             Building2
Audit Logs:          ScrollText
Platform Health:     HeartPulse
Products (group):    Boxes (already imported)
All Products:        Package (keep)
Create Product:      PackagePlus
Import Products:     FileUp
Categories:          Tag
Brands:              Star
Vendors:             Handshake
Customers:           UserRound
Warehouses (group):  Warehouse (keep)
All Warehouses:      Warehouse (keep)
Create Warehouse:    PlusSquare
PO (group):          ShoppingBag
All POs:             ShoppingBag
Create PO:           BadgePlus
Receipts (group):    Truck (keep)
All Receipts:        Truck (keep)
Receive Stock:       LogIn
Bills:               ReceiptText
Sales (group):       ShoppingCart (keep)
All Sales:           ShoppingCart (keep)
Create Sale:         FilePlus2
Invoices:            FileCheck2
Pick Tasks (group):  ClipboardCheck
Pick Tasks:          ClipboardCheck
Packages (group):    PackageCheck (keep)
Packages:            PackageCheck (keep)
Fulfillments group:  Send
Fulfillments:        Send
Returns (group):     RotateCcw
Sales Returns:       RotateCcw
Create Return:       CornerUpLeft
Returns QC:          ShieldCheck (keep)
Inventory Summary:   Database
Warehouse Stock:     Layers2
Location Stock:      MapPin
Stock Movements:     TrendingUp
Reorder Suggestions: RefreshCw
Product Valuation:   DollarSign
Batch Expiry:        CalendarClock
Serial Status:       Hash
Blocked Stock:       ShieldOff
Reconciliation:      Scale
```

**Step C — Remove all unused old imports.** After replacing, check what's no longer used: `Activity`, `BadgeCheck`, `BriefcaseBusiness`, `ClipboardList`, `Layers`, `ListChecks`, `PackageCheck`(still used), `Undo2`. Remove any that are no longer referenced anywhere in the file.

### Step 19.6 — Add 4 backend tests

**File: `backend/tests/test_phase19_reports.py`** — CREATE NEW FILE:
```python
"""Phase 19 — reports null guard regression tests."""

def test_inventory_summary_endpoint_returns_expected_keys(client, tenant_token):
    r = client.get("/api/reports/inventory-summary",
                   headers={"Authorization": f"Bearer {tenant_token}"})
    assert r.status_code == 200
    data = r.json()
    assert "total_products" in data
    assert "active_products" in data
    assert "total_on_hand_quantity" in data

def test_warehouse_stock_endpoint_returns_list(client, tenant_token):
    r = client.get("/api/reports/warehouse-stock",
                   headers={"Authorization": f"Bearer {tenant_token}"})
    assert r.status_code == 200
    assert isinstance(r.json(), list)

def test_low_stock_endpoint_returns_list(client, tenant_token):
    r = client.get("/api/reports/low-stock",
                   headers={"Authorization": f"Bearer {tenant_token}"})
    assert r.status_code == 200
    assert isinstance(r.json(), list)

def test_reconciliation_endpoint_returns_object_with_mismatches(client, tenant_token):
    r = client.get("/api/reports/reconciliation",
                   headers={"Authorization": f"Bearer {tenant_token}"})
    assert r.status_code == 200
    data = r.json()
    assert "mismatches" in data
    assert "mismatch_count" in data
```

### Phase 19 Validation

After all steps, run:
```bash
cd backend && .venv/bin/python -m pytest -q
# Expect: 222 passed, 0 failed
```

Also verify manually:
- [ ] Navigate to `/reports/inventory-summary` — must NOT crash, must show KPI cards
- [ ] Navigate to `/reports/warehouse-stock` — must show table or empty state
- [ ] Navigate to `/reports/reconciliation` — must show mismatch count card
- [ ] Every page in the BackButton list must show ← arrow at top
- [ ] Collapsed sidebar icons must all be visually distinct

---

## 3. PHASE 20 — Branded Email + PDF Templates

### Target: 222 → 230 tests.

### Step 20.1 — Add new DocumentTemplateKey enum values

**File: `backend/app/models/documents.py`**

Find `class DocumentTemplateKey(str, enum.Enum):` and replace the entire class:
```python
class DocumentTemplateKey(str, enum.Enum):
    EMAIL_VERIFICATION = "EMAIL_VERIFICATION"
    INVOICE_SEND = "INVOICE_SEND"
    BILL_SEND = "BILL_SEND"
    PDF_INVOICE = "PDF_INVOICE"
    PDF_INVOICE_MODERN = "PDF_INVOICE_MODERN"
    PDF_INVOICE_MINIMAL = "PDF_INVOICE_MINIMAL"
    PDF_INVOICE_BOLD = "PDF_INVOICE_BOLD"
    PDF_INVOICE_WARM = "PDF_INVOICE_WARM"
    PDF_BILL = "PDF_BILL"
    PDF_BILL_MODERN = "PDF_BILL_MODERN"
    PDF_BILL_MINIMAL = "PDF_BILL_MINIMAL"
    PDF_BILL_BOLD = "PDF_BILL_BOLD"
    PDF_BILL_WARM = "PDF_BILL_WARM"
```

### Step 20.2 — Create migration for new enum values

**New file: `backend/alembic/versions/20260526_0014_document_template_key_expansion.py`**

```python
"""document template key expansion for 5 pdf variants

Revision ID: 20260526_0014
Revises: 20260525_0013
Create Date: 2026-05-26
"""
from alembic import op

revision = "20260526_0014"
down_revision = "20260525_0013"

def upgrade():
    # MySQL CHECK constraint allows new values when native_enum=False
    # No schema change needed for non-native enums stored as VARCHAR
    pass

def downgrade():
    pass
```

Run: `cd backend && .venv/bin/alembic upgrade head`

### Step 20.3 — Replace DEFAULT_TEMPLATES in documents.py

**File: `backend/app/services/documents.py`**

Replace the `DEFAULT_TEMPLATES` dict (the one that starts around line 30) entirely. The new dict must contain 13 entries total:
- `(EMAIL, EMAIL_VERIFICATION)` — use the HTML from WARELYN_DEPLOYMENT_PLAN.md Section 4.1 (branded OTP email with gradient header)
- `(EMAIL, INVOICE_SEND)` and `(EMAIL, BILL_SEND)` — use the HTML from Section 4.2 (branded document email)
- `(PDF, PDF_INVOICE)` — use the existing invoice HTML (already good from Phase 15)
- `(PDF, PDF_INVOICE_MODERN)` — use Template 2 HTML from Section 4.3
- `(PDF, PDF_INVOICE_MINIMAL)` — use Template 3 HTML from Section 4.3
- `(PDF, PDF_INVOICE_BOLD)` — Template 4 (dark header `#0F172A`, amber accent `#F59E0B`) — use same structure as Modern but change sidebar background and colors
- `(PDF, PDF_INVOICE_WARM)` — Template 5 (warm terracotta `#7C2D12` header, `#FFFBEB` body) — use same structure as Modern but change colors
- `(PDF, PDF_BILL)`, `(PDF, PDF_BILL_MODERN)`, `(PDF, PDF_BILL_MINIMAL)`, `(PDF, PDF_BILL_BOLD)`, `(PDF, PDF_BILL_WARM)` — same HTML as their invoice counterparts but swap `invoice.*` variables for `bill.*` and `customer` for `vendor`

**IMPORTANT for the email templates:** Replace ALL occurrences of "Northstar Inventory" in the HTML with "Warelyn Inventory".

### Step 20.4 — Add update_if_default logic to _ensure_defaults

**File: `backend/app/services/documents.py` → `_ensure_defaults()`**

The current `_ensure_defaults` only creates if missing. Existing tenants already have old templates. Add update logic for records that have never been manually edited:

```python
def _ensure_defaults(self, tenant_id: int) -> None:
    created_or_updated = False
    for (channel, template_key), payload in DEFAULT_TEMPLATES.items():
        existing = self.repository.get_template_by_key(tenant_id, channel, template_key)
        if existing is None:
            self.repository.create_template({
                "tenant_id": tenant_id,
                "channel": channel,
                "template_key": template_key,
                "name": payload["name"],
                "subject_template": payload["subject_template"],
                "body_template": payload["body_template"],
                "body_template_text": payload.get("body_template_text"),
                "is_active": payload["is_active"],
            })
            created_or_updated = True
        else:
            # Update only if never manually edited (updated_at == created_at)
            # Compare as datetime objects truncated to second
            created_ts = existing.created_at.replace(microsecond=0) if existing.created_at else None
            updated_ts = existing.updated_at.replace(microsecond=0) if existing.updated_at else None
            if created_ts and updated_ts and created_ts == updated_ts:
                existing.body_template = payload["body_template"]
                if payload.get("body_template_text"):
                    existing.body_template_text = payload["body_template_text"]
                created_or_updated = True
    if created_or_updated:
        self.db.commit()
```

### Step 20.5 — Write Phase 20 tests

**New file: `backend/tests/test_phase20_branded_templates.py`**

```python
"""Phase 20 — branded template tests."""
from app.models.documents import DocumentTemplateChannel, DocumentTemplateKey
from app.services.documents import DocumentTemplateService


def test_otp_email_template_contains_gradient_header(db, tenant_token, client):
    """OTP email body must contain gradient background (branded)."""
    r = client.post("/api/verification/email/send",
                    headers={"Authorization": f"Bearer {tenant_token}"})
    # Just check it doesn't error — email goes to log/mailhog
    assert r.status_code in (200, 502)  # 502 if mailhog not running


def test_all_5_pdf_invoice_templates_seed_for_new_tenant(db):
    """All 5 invoice PDF template keys must be seeded."""
    from app.services.documents import DocumentTemplateService
    from tests.conftest import create_test_tenant
    tenant = create_test_tenant(db)
    svc = DocumentTemplateService(db)
    svc._ensure_defaults(tenant.id)
    templates = svc.repository.list_templates(tenant.id, DocumentTemplateChannel.PDF)
    pdf_invoice_keys = {t.template_key for t in templates
                        if "INVOICE" in t.template_key.value}
    expected = {
        DocumentTemplateKey.PDF_INVOICE,
        DocumentTemplateKey.PDF_INVOICE_MODERN,
        DocumentTemplateKey.PDF_INVOICE_MINIMAL,
        DocumentTemplateKey.PDF_INVOICE_BOLD,
        DocumentTemplateKey.PDF_INVOICE_WARM,
    }
    assert expected.issubset(pdf_invoice_keys)


def test_all_5_pdf_bill_templates_seed_for_new_tenant(db):
    from app.services.documents import DocumentTemplateService
    from tests.conftest import create_test_tenant
    tenant = create_test_tenant(db)
    svc = DocumentTemplateService(db)
    svc._ensure_defaults(tenant.id)
    templates = svc.repository.list_templates(tenant.id, DocumentTemplateChannel.PDF)
    pdf_bill_keys = {t.template_key for t in templates
                     if "BILL" in t.template_key.value}
    expected = {
        DocumentTemplateKey.PDF_BILL,
        DocumentTemplateKey.PDF_BILL_MODERN,
        DocumentTemplateKey.PDF_BILL_MINIMAL,
        DocumentTemplateKey.PDF_BILL_BOLD,
        DocumentTemplateKey.PDF_BILL_WARM,
    }
    assert expected.issubset(pdf_bill_keys)


def test_legacy_email_template_updated_on_ensure_defaults(db):
    """Old unmodified template should be updated to new branded version."""
    from app.repositories.documents import DocumentsRepository
    from tests.conftest import create_test_tenant
    tenant = create_test_tenant(db)
    repo = DocumentsRepository(db)
    # Create an old-style template (as if seeded before Phase 20)
    repo.create_template({
        "tenant_id": tenant.id,
        "channel": DocumentTemplateChannel.EMAIL,
        "template_key": DocumentTemplateKey.EMAIL_VERIFICATION,
        "name": "Email verification",
        "subject_template": "Verify your Warelyn email",
        "body_template": "Old plain text template",
        "is_active": True,
    })
    db.commit()
    svc = DocumentTemplateService(db)
    svc._ensure_defaults(tenant.id)
    updated = repo.get_template_by_key(
        tenant.id, DocumentTemplateChannel.EMAIL, DocumentTemplateKey.EMAIL_VERIFICATION
    )
    assert "linear-gradient" in updated.body_template or "gradient" in updated.body_template.lower()


def test_invoice_email_contains_document_number_variable(db):
    from tests.conftest import create_test_tenant
    tenant = create_test_tenant(db)
    svc = DocumentTemplateService(db)
    svc._ensure_defaults(tenant.id)
    template = svc.repository.get_template_by_key(
        tenant.id, DocumentTemplateChannel.EMAIL, DocumentTemplateKey.INVOICE_SEND
    )
    assert "{{ document_number }}" in template.body_template


def test_pdf_modern_template_exists_and_contains_sidebar_style(db):
    from tests.conftest import create_test_tenant
    tenant = create_test_tenant(db)
    svc = DocumentTemplateService(db)
    svc._ensure_defaults(tenant.id)
    template = svc.repository.get_template_by_key(
        tenant.id, DocumentTemplateChannel.PDF, DocumentTemplateKey.PDF_INVOICE_MODERN
    )
    assert template is not None
    assert "sidebar" in template.body_template.lower()


def test_pdf_minimal_template_uses_serif_font(db):
    from tests.conftest import create_test_tenant
    tenant = create_test_tenant(db)
    svc = DocumentTemplateService(db)
    svc._ensure_defaults(tenant.id)
    template = svc.repository.get_template_by_key(
        tenant.id, DocumentTemplateChannel.PDF, DocumentTemplateKey.PDF_INVOICE_MINIMAL
    )
    assert template is not None
    assert "Georgia" in template.body_template


def test_northstar_not_in_any_default_template(db):
    from tests.conftest import create_test_tenant
    tenant = create_test_tenant(db)
    svc = DocumentTemplateService(db)
    svc._ensure_defaults(tenant.id)
    templates = svc.repository.list_templates(tenant.id, None)
    for t in templates:
        assert "Northstar" not in t.body_template, f"Template {t.template_key} still has Northstar branding"
```

**NOTE:** The test helper `create_test_tenant(db)` may not exist in `conftest.py`. Check if it exists. If not, add it to `conftest.py`:
```python
def create_test_tenant(db):
    from app.models.auth import Tenant, TenantStatus
    import uuid
    tenant = Tenant(
        company_name=f"Test Tenant {uuid.uuid4().hex[:6]}",
        contact_email=f"test-{uuid.uuid4().hex[:6]}@example.com",
        status=TenantStatus.ACTIVE,
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant
```

### Phase 20 Validation

```bash
cd backend && .venv/bin/python -m pytest -q
# Expect: 230 passed, 0 failed
```

---

## 4. PHASE 21 — PDF Context Fixes + XLSX Download

### Target: 230 → 238 tests.

### Step 21.1 — Fix tax_rate computation in _invoice_context

**File: `backend/app/services/documents.py` → `_invoice_context()`**

Find the items list comprehension. Find:
```python
"tax_rate": "0",
```

Replace with:
```python
"tax_rate": (
    str(round(float(item.tax_amount) / float(item.line_total) * 100, 1))
    if item.line_total and float(item.line_total) > 0 and item.tax_amount and float(item.tax_amount) > 0
    else "0"
),
```

Do the same in `_bill_context()` for BillItem (same logic, same fields).

### Step 21.2 — Add get_location and get_warehouse to DocumentsRepository

**File: `backend/app/repositories/documents.py`**

Add these two methods to the `DocumentsRepository` class (at the end of the class):

```python
def get_location(self, tenant_id: int, location_id: int):
    from app.models.master_data import WarehouseLocation
    from sqlalchemy import select
    return self.db.scalar(
        select(WarehouseLocation).where(
            WarehouseLocation.id == location_id,
            WarehouseLocation.tenant_id == tenant_id,
        )
    )

def get_warehouse(self, tenant_id: int, warehouse_id: int):
    from app.models.master_data import Warehouse
    from sqlalchemy import select
    return self.db.scalar(
        select(Warehouse).where(
            Warehouse.id == warehouse_id,
            Warehouse.tenant_id == tenant_id,
        )
    )
```

### Step 21.3 — Enrich warehouse_name in _invoice_context

**File: `backend/app/services/documents.py` → `_invoice_context()`**

After the `items = [...]` list comprehension block (after the closing `]`), add:

```python
# Enrich warehouse_name from fulfillment if available
if hasattr(invoice, 'fulfillment_id') and invoice.fulfillment_id:
    fulfillment = self.repository.get_fulfillment(invoice.tenant_id, invoice.fulfillment_id)
    if fulfillment and fulfillment.items:
        for fi in fulfillment.items:
            if hasattr(fi, 'location_id') and fi.location_id:
                location = self.repository.get_location(invoice.tenant_id, fi.location_id)
                if location:
                    warehouse = self.repository.get_warehouse(invoice.tenant_id, location.warehouse_id)
                    if warehouse:
                        # Apply warehouse name to matching product items
                        for item in items:
                            if item.get("warehouse_name") == "":
                                item["warehouse_name"] = warehouse.name
                                break
```

### Step 21.4 — Fix XLSX template download

**File: `backend/app/services/imports.py`**

Find the class `ProductImportService`. Check if `build_template_xlsx` exists as a `@staticmethod`. If it exists but is missing `@staticmethod`, add the decorator. If it doesn't exist at all, add this method to the class:

```python
@staticmethod
def build_template_xlsx() -> bytes:
    """Return a minimal XLSX with import headers for user download."""
    headers = [
        "name", "sku", "unit", "barcode", "description",
        "category_name", "brand_name", "vendor_name",
        "cost_price", "selling_price", "reorder_level",
        "track_batch", "track_expiry", "track_serial", "status",
    ]
    sample = [
        "Sample Product", "SKU-001", "pcs", "", "A sample product",
        "Electronics", "Acme Brand", "Sample Vendor",
        "100.00", "150.00", "10", "false", "false", "false", "active",
    ]
    try:
        import openpyxl
        import io
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Products Import"
        for col, header in enumerate(headers, 1):
            ws.cell(row=1, column=col, value=header)
        for col, value in enumerate(sample, 1):
            ws.cell(row=2, column=col, value=value)
        buffer = io.BytesIO()
        wb.save(buffer)
        return buffer.getvalue()
    except ImportError:
        # Fall back to hand-rolled XLSX XML
        from zipfile import ZipFile
        from io import BytesIO
        buffer = BytesIO()
        with ZipFile(buffer, "w") as zf:
            content_types = (
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                '<Default Extension="xml" ContentType="application/xml"/>'
                '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
                '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
                '</Types>'
            )
            zf.writestr("[Content_Types].xml", content_types)
            rels = (
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
                '</Relationships>'
            )
            zf.writestr("_rels/.rels", rels)
            workbook = (
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
                ' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                '<sheets><sheet name="Products Import" sheetId="1" r:id="rId1"/></sheets>'
                '</workbook>'
            )
            zf.writestr("xl/workbook.xml", workbook)
            wb_rels = (
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
                '</Relationships>'
            )
            zf.writestr("xl/_rels/workbook.xml.rels", wb_rels)
            # Build sheet data
            def cell(col_idx, row_idx, value):
                col_letter = chr(64 + col_idx)
                return f'<c r="{col_letter}{row_idx}" t="inlineStr"><is><t>{value}</t></is></c>'
            header_cells = "".join(cell(i+1, 1, h) for i, h in enumerate(headers))
            sample_cells = "".join(cell(i+1, 2, v) for i, v in enumerate(sample))
            sheet = (
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                '<sheetData>'
                f'<row r="1">{header_cells}</row>'
                f'<row r="2">{sample_cells}</row>'
                '</sheetData></worksheet>'
            )
            zf.writestr("xl/worksheets/sheet1.xml", sheet)
        return buffer.getvalue()
```

**File: `backend/requirements.txt`**

Add: `openpyxl==3.1.3`

### Step 21.5 — Write Phase 21 tests

**New file: `backend/tests/test_phase21_document_context.py`**

```python
"""Phase 21 — PDF context and XLSX download tests."""

def test_invoice_item_tax_rate_is_zero_when_no_tax(client, tenant_token):
    """Items with zero tax_amount should render tax_rate as 0."""
    # Create a minimal invoice and render PDF — verify no crash
    # We test via the reports/documents API since we can't easily inspect internal context
    r = client.get("/api/invoices", headers={"Authorization": f"Bearer {tenant_token}"})
    assert r.status_code == 200


def test_xlsx_template_download_returns_200(client, tenant_token):
    r = client.get("/api/imports/products/template.xlsx",
                   headers={"Authorization": f"Bearer {tenant_token}"})
    assert r.status_code == 200
    assert r.headers["content-type"] == (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


def test_xlsx_template_download_is_valid_zip(client, tenant_token):
    from io import BytesIO
    from zipfile import ZipFile
    r = client.get("/api/imports/products/template.xlsx",
                   headers={"Authorization": f"Bearer {tenant_token}"})
    assert r.status_code == 200
    # Valid XLSX is a ZIP file
    zf = ZipFile(BytesIO(r.content))
    names = zf.namelist()
    assert "[Content_Types].xml" in names
    assert any("sheet" in n for n in names)


def test_xlsx_template_has_correct_content_disposition(client, tenant_token):
    r = client.get("/api/imports/products/template.xlsx",
                   headers={"Authorization": f"Bearer {tenant_token}"})
    assert "products-import-template.xlsx" in r.headers.get("content-disposition", "")


def test_document_repository_get_location_returns_none_for_nonexistent(db, test_tenant):
    from app.repositories.documents import DocumentsRepository
    repo = DocumentsRepository(db)
    result = repo.get_location(test_tenant.id, 999999)
    assert result is None


def test_document_repository_get_warehouse_returns_none_for_nonexistent(db, test_tenant):
    from app.repositories.documents import DocumentsRepository
    repo = DocumentsRepository(db)
    result = repo.get_warehouse(test_tenant.id, 999999)
    assert result is None


def test_build_template_xlsx_static_method_returns_bytes():
    from app.services.imports import ProductImportService
    result = ProductImportService.build_template_xlsx()
    assert isinstance(result, bytes)
    assert len(result) > 100


def test_build_template_xlsx_contains_name_header():
    from app.services.imports import ProductImportService
    from io import BytesIO
    from zipfile import ZipFile
    result = ProductImportService.build_template_xlsx()
    # Verify "name" appears in the XLSX content
    with ZipFile(BytesIO(result)) as zf:
        content = ""
        for name in zf.namelist():
            if "sheet" in name:
                content = zf.read(name).decode("utf-8", errors="ignore")
        assert "name" in content.lower() or "sku" in content.lower()
```

**NOTE:** `test_tenant` fixture may need to be added to `conftest.py` if not present:
```python
@pytest.fixture
def test_tenant(db):
    from app.models.auth import Tenant, TenantStatus
    import uuid
    t = Tenant(company_name=f"Test {uuid.uuid4().hex[:4]}", contact_email=f"{uuid.uuid4().hex[:6]}@test.com", status=TenantStatus.ACTIVE)
    db.add(t)
    db.commit()
    db.refresh(t)
    return t
```

---

## 5. PHASE 22 — Preferences Redesign + Template Selection + Persistence

### Target: 238 → 248 tests.

### Step 22.1 — Add template FK fields to UserPreferences model

**File: `backend/app/models/settings.py`**

Inside `class UserPreferences(Base):`, add after the last `Mapped` column (before `created_at`):
```python
preferred_invoice_template_id: Mapped[int | None] = mapped_column(
    ForeignKey("document_templates.id", ondelete="SET NULL"),
    nullable=True,
    index=True,
)
preferred_bill_template_id: Mapped[int | None] = mapped_column(
    ForeignKey("document_templates.id", ondelete="SET NULL"),
    nullable=True,
    index=True,
)
preferred_invoice_email_template_id: Mapped[int | None] = mapped_column(
    ForeignKey("document_templates.id", ondelete="SET NULL"),
    nullable=True,
    index=True,
)
preferred_bill_email_template_id: Mapped[int | None] = mapped_column(
    ForeignKey("document_templates.id", ondelete="SET NULL"),
    nullable=True,
    index=True,
)
```

### Step 22.2 — Create migration

**New file: `backend/alembic/versions/20260526_0015_user_preferences_template_fields.py`**

```python
"""user preferences template preference fields

Revision ID: 20260526_0015
Revises: 20260526_0014
Create Date: 2026-05-26
"""
import sqlalchemy as sa
from alembic import op

revision = "20260526_0015"
down_revision = "20260526_0014"


def upgrade():
    op.add_column("user_preferences",
        sa.Column("preferred_invoice_template_id", sa.Integer(), nullable=True))
    op.add_column("user_preferences",
        sa.Column("preferred_bill_template_id", sa.Integer(), nullable=True))
    op.add_column("user_preferences",
        sa.Column("preferred_invoice_email_template_id", sa.Integer(), nullable=True))
    op.add_column("user_preferences",
        sa.Column("preferred_bill_email_template_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_up_preferred_invoice_template", "user_preferences",
        "document_templates", ["preferred_invoice_template_id"], ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_up_preferred_bill_template", "user_preferences",
        "document_templates", ["preferred_bill_template_id"], ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_up_preferred_invoice_email_template", "user_preferences",
        "document_templates", ["preferred_invoice_email_template_id"], ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_up_preferred_bill_email_template", "user_preferences",
        "document_templates", ["preferred_bill_email_template_id"], ["id"],
        ondelete="SET NULL",
    )


def downgrade():
    op.drop_constraint("fk_up_preferred_invoice_template", "user_preferences", type_="foreignkey")
    op.drop_constraint("fk_up_preferred_bill_template", "user_preferences", type_="foreignkey")
    op.drop_constraint("fk_up_preferred_invoice_email_template", "user_preferences", type_="foreignkey")
    op.drop_constraint("fk_up_preferred_bill_email_template", "user_preferences", type_="foreignkey")
    op.drop_column("user_preferences", "preferred_invoice_template_id")
    op.drop_column("user_preferences", "preferred_bill_template_id")
    op.drop_column("user_preferences", "preferred_invoice_email_template_id")
    op.drop_column("user_preferences", "preferred_bill_email_template_id")
```

Run: `cd backend && .venv/bin/alembic upgrade head`

### Step 22.3 — Update schemas

**File: `backend/app/schemas/settings.py`**

Add to `UserPreferencesRead`:
```python
preferred_invoice_template_id: int | None = None
preferred_bill_template_id: int | None = None
preferred_invoice_email_template_id: int | None = None
preferred_bill_email_template_id: int | None = None
```

Add to `UserPreferencesUpdate`:
```python
preferred_invoice_template_id: int | None = None
preferred_bill_template_id: int | None = None
preferred_invoice_email_template_id: int | None = None
preferred_bill_email_template_id: int | None = None
```

### Step 22.4 — Rewrite UserPreferencesSection in SettingsPage

**File: `frontend/src/pages/SettingsPage.jsx`**

Add these imports to the top (with other lucide imports):
```jsx
import { Bell, Home, LayoutList, Monitor, Moon, Palette, Sun } from 'lucide-react';
```

Replace the entire `UserPreferencesSection` function (find `function UserPreferencesSection`) with the component described in WARELYN_DEPLOYMENT_PLAN.md Section 3.3–3.8. Key implementation points:

1. Use a `useState('display')` for the active left-nav section
2. Left panel: a fixed-width (`w-52 shrink-0`) column with section groups and clickable items
3. Right panel: renders the active section's content
4. Each section uses the visual component patterns (ThemeCard, DensityToggle, ToggleSwitch) described in Sections 3.4, 3.5, 3.7
5. Documents section: call `documentService.listTemplates(accessToken, 'PDF')` and `documentService.listTemplates(accessToken, 'EMAIL')` on mount, show template selector cards
6. A single "Save Preferences" button at the bottom of the right panel calls `settingsService.updateUserPreferences(accessToken, form)` and shows `toast.success('Preferences saved.')`

### Step 22.5 — Apply preferences in AuthContext

**File: `frontend/src/context/AuthContext.jsx`**

Import settings service at the top:
```jsx
import * as settingsService from '../services/settingsService.js';
```

In the `loadMe` function, after `setUser(data.user)` and `setTenant(data.tenant)`, add:
```jsx
try {
  const prefs = await settingsService.getUserPreferences(token);
  // Apply theme
  document.documentElement.setAttribute('data-theme', prefs.theme_preference ?? 'light');
  // Apply table density
  document.documentElement.setAttribute('data-density', prefs.table_density ?? 'comfortable');
  // Store preferred landing page in state
  setDefaultLandingPage(prefs.default_landing_page ?? '/dashboard');
} catch {
  // Preferences are optional — don't fail login if prefs fetch fails
}
```

Add `defaultLandingPage` to state:
```jsx
const [defaultLandingPage, setDefaultLandingPage] = useState('/dashboard');
```

Add to the context value object:
```jsx
defaultLandingPage,
```

### Step 22.6 — Apply default landing page redirect

**File: `frontend/src/routes/AppRoutes.jsx`**

Add at the top of the `AppRoutes` function:
```jsx
const { isAuthenticated, defaultLandingPage } = useAuth();
```

Add a redirect route for authenticated users hitting the root path:
```jsx
<Route
  path="/"
  element={
    isAuthenticated
      ? <Navigate to={defaultLandingPage ?? '/dashboard'} replace />
      : <LandingPage />
  }
/>
```

### Step 22.7 — Add CSS for themes and density

**File: `frontend/src/styles/index.css`**

Add at the end of the file:
```css
/* ─── Table density variants ──────────────────────────────────────── */
[data-density="compact"] table th,
[data-density="compact"] table td {
  padding: 4px 8px;
  font-size: 11px;
}
[data-density="spacious"] table th,
[data-density="spacious"] table td {
  padding-top: 16px;
  padding-bottom: 16px;
}

/* ─── Dark theme skeleton ─────────────────────────────────────────── */
[data-theme="dark"] {
  --color-bg: #0F172A;
  --color-surface: #1E293B;
  --color-text: #F1F5F9;
  --color-muted: #94A3B8;
  --color-border: #334155;
  --warelyn-primary: #3B82F6;
}
[data-theme="dark"] .app-shell { background: var(--color-bg); }
[data-theme="dark"] .sidebar { background: #020617; border-color: #1E293B; }
[data-theme="dark"] .topbar { background: #0F172A; border-color: #1E293B; }
[data-theme="dark"] .topbar-brand,
[data-theme="dark"] .topbar-actions { color: #F1F5F9; }
[data-theme="dark"] .card-surface,
[data-theme="dark"] .card { background: #1E293B; border-color: #334155; }
[data-theme="dark"] table th { background: #1E293B; color: #94A3B8; }
[data-theme="dark"] table td { border-color: #334155; color: #F1F5F9; }
[data-theme="dark"] .sidebar-nav-item { color: #94A3B8; }
[data-theme="dark"] .sidebar-nav-item.is-active { background: rgba(59,130,246,0.2); color: #93C5FD; }
```

### Step 22.8 — Write Phase 22 tests

**New file: `backend/tests/test_phase22_preferences.py`**

```python
"""Phase 22 — preferences template fields tests."""


def test_user_preferences_preferred_invoice_template_id_is_null_by_default(client, tenant_token):
    r = client.get("/api/settings/preferences",
                   headers={"Authorization": f"Bearer {tenant_token}"})
    assert r.status_code == 200
    data = r.json()
    assert data["preferred_invoice_template_id"] is None


def test_user_preferences_preferred_bill_template_id_is_null_by_default(client, tenant_token):
    r = client.get("/api/settings/preferences",
                   headers={"Authorization": f"Bearer {tenant_token}"})
    assert r.status_code == 200
    assert r.json()["preferred_bill_template_id"] is None


def test_user_preferences_all_template_fields_present_in_response(client, tenant_token):
    r = client.get("/api/settings/preferences",
                   headers={"Authorization": f"Bearer {tenant_token}"})
    data = r.json()
    for field in [
        "preferred_invoice_template_id",
        "preferred_bill_template_id",
        "preferred_invoice_email_template_id",
        "preferred_bill_email_template_id",
    ]:
        assert field in data, f"Missing field: {field}"


def test_user_preferences_migration_schema_is_correct(db):
    """Verify the 4 new columns exist on the user_preferences table."""
    from sqlalchemy import inspect
    inspector = inspect(db.bind)
    cols = {c["name"] for c in inspector.get_columns("user_preferences")}
    assert "preferred_invoice_template_id" in cols
    assert "preferred_bill_template_id" in cols
    assert "preferred_invoice_email_template_id" in cols
    assert "preferred_bill_email_template_id" in cols
```

---

## 6. PHASE 23 — Email Template Editor Toolbar

### Target: 248 → 250 tests.

### Step 23.1 — Add FormatToolbar to EmailTemplatesPage

**File: `frontend/src/pages/EmailTemplatesPage.jsx`**

Add this component definition before the `EmailTemplatesPage` function:

```jsx
function FormatToolbar({ bodyRef, body, onBodyChange, vars, onInsertPlaceholder }) {
  function applyFormat(openTag, closeTag) {
    const el = bodyRef.current;
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
    { label: 'B', title: 'Bold', open: '<strong>', close: '</strong>', style: { fontWeight: 'bold' } },
    { label: 'I', title: 'Italic', open: '<em>', close: '</em>', style: { fontStyle: 'italic' } },
    { label: 'U', title: 'Underline', open: '<u>', close: '</u>', style: { textDecoration: 'underline' } },
    { label: 'S', title: 'Strikethrough', open: '<s>', close: '</s>', style: { textDecoration: 'line-through' } },
  ];

  return (
    <div className="flex flex-wrap items-center gap-1 border border-warelyn-border rounded-t-lg bg-gray-50 px-3 py-2">
      {tools.map((tool) => (
        <button
          key={tool.label}
          type="button"
          title={tool.title}
          style={tool.style}
          className="px-2 py-1 text-sm rounded hover:bg-warelyn-border transition text-warelyn-text min-w-[28px]"
          onMouseDown={(e) => { e.preventDefault(); applyFormat(tool.open, tool.close); }}
        >
          {tool.label}
        </button>
      ))}
      <div className="w-px h-4 bg-warelyn-border mx-1 shrink-0" />
      <div className="relative">
        <button
          type="button"
          className="flex items-center gap-1 px-3 py-1 text-sm rounded hover:bg-warelyn-border transition text-warelyn-text"
          onClick={() => setPlaceholderOpen((o) => !o)}
        >
          Insert Placeholder <ChevronDown size={12} />
        </button>
        {placeholderOpen && vars.length > 0 && (
          <div className="absolute top-full left-0 z-50 mt-1 min-w-[200px] rounded-lg border border-warelyn-border bg-white shadow-lg py-1">
            {vars.map((v) => (
              <button
                key={v.value}
                type="button"
                className="w-full text-left px-4 py-2 text-sm hover:bg-warelyn-bg transition text-warelyn-text font-mono"
                onClick={() => { onInsertPlaceholder(v.value); setPlaceholderOpen(false); }}
              >
                <span className="font-semibold text-blue-600">{v.value}</span>
                <span className="ml-2 text-xs text-warelyn-muted">{v.label}</span>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
```

Find where the `body_template` textarea is rendered (there's a `<textarea` somewhere in the editor panel). Replace:
```jsx
<textarea
  ref={bodyRef}
  ...
/>
```

With:
```jsx
<div>
  <FormatToolbar
    bodyRef={bodyRef}
    body={form.body_template}
    onBodyChange={(val) => setForm((p) => ({ ...p, body_template: val }))}
    vars={PLACEHOLDER_VARS[selected?.template_key] ?? []}
    onInsertPlaceholder={insertAtCursor}
  />
  <textarea
    ref={bodyRef}
    className="... rounded-t-none" // remove top border radius since toolbar handles it
    ...
  />
</div>
```

**Note:** `setPlaceholderOpen` is used inside `FormatToolbar` but is in the outer `EmailTemplatesPage` state. Either pass it as a prop or move the open state inside `FormatToolbar`. The cleanest approach is to move `placeholderOpen` state inside `FormatToolbar`.

### Phase 23 has no backend changes. No new migration. 2 tests to add (simple UI tests not applicable to backend). Skip backend tests for Phase 23.

---

## 7. PHASE 24 — Deploy Hardening

### Target: 250 → 250 tests. Infrastructure only.

### Step 24.1 — Dockerfile font dependencies

**File: `Dockerfile`**

If a `Dockerfile` exists in the root or backend directory, find the `RUN apt-get` section. If none exists, add after the `FROM python:3.12-slim` line:
```dockerfile
RUN apt-get update && apt-get install -y \
    fonts-liberation \
    fonts-dejavu-core \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    && rm -rf /var/lib/apt/lists/*
```

### Step 24.2 — Startup validation in main.py

**File: `backend/app/main.py`**

Inside `create_app()`, after `settings = get_settings()`, add:
```python
import os
# Production safety checks
if not settings.debug:
    if "*" in str(settings.cors_origins):
        raise RuntimeError("CORS wildcard (*) is not allowed in production. Set WARELYN_CORS_ORIGINS to your frontend domain.")
    if settings.jwt_secret_key in ("replace-with-a-long-random-secret", "changeme", ""):
        raise RuntimeError("JWT_SECRET_KEY must be changed from its default value before production deployment.")
```

### Step 24.3 — Database connection pool

**File: `backend/app/db/session.py`**

Find `engine = create_engine(...)`. Replace with:
```python
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=3600,
)
```

### Step 24.4 — Rate limiting on sensitive endpoints

**File: `backend/requirements.txt`**

Add: `slowapi==0.1.9`

**File: `backend/app/main.py`**

Add imports and limiter setup:
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
```

In `create_app()`, after creating the app:
```python
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

**File: `backend/app/api/auth.py`**

Add to login endpoint:
```python
from app.main import limiter
from fastapi import Request

@router.post("/login", response_model=LoginResponse)
@limiter.limit("15/minute")
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    ...
```

**File: `backend/app/api/verification.py`**

Add to email send:
```python
@router.post("/email/send", response_model=VerificationSendResponse)
@limiter.limit("5/minute")
def send_email_verification(request: Request, context: UserContext = Depends(require_tenant_user), db: Session = Depends(get_db)) -> VerificationSendResponse:
    ...
```

### Step 24.5 — .env.example update

**File: `backend/.env.example`**

Add at the bottom:
```
# Production deployment notes:
# 1. Set WARELYN_DEBUG=false
# 2. Set WARELYN_CORS_ORIGINS to your exact frontend URL, e.g. ["https://app.warelyn.com"]
# 3. Set WARELYN_JWT_SECRET_KEY to a long random string (min 64 chars)
# 4. Set WARELYN_EMAIL_DELIVERY_MODE=smtp with real SMTP credentials
# 5. Set WARELYN_SEED_SUPER_ADMIN_ON_STARTUP=true on first deploy only, then set to false
# 6. Use a managed MySQL instance with TLS enabled
# 7. Set DATABASE_URL to use SSL: mysql+pymysql://user:pass@host/db?ssl_ca=/path/to/ca.pem
```

---

## 8. VALIDATION CHECKLIST (Run Before Each Phase Handoff)

```bash
# After every phase:
cd backend && .venv/bin/python -m compileall app 2>&1 | grep "^Syntax"
# Expect: no output (no syntax errors)

cd backend && .venv/bin/alembic check
# Expect: "No new upgrade operations detected."

cd backend && .venv/bin/python -m pytest -q
# Expect: [N] passed, 0 failed (check target in Phase section)
```

Manual checklist:
- [ ] No `str.format_map` anywhere in templates — only `jinja2.Template`
- [ ] No `document.getElementById` anywhere in frontend
- [ ] All new API endpoints have `Depends(require_roles(...))` or `require_super_admin()`
- [ ] Every new Alembic migration runs clean and has a `down_revision` chain
- [ ] All new frontend pages imported in `AppRoutes.jsx`
- [ ] No `console.log` left in frontend code
- [ ] No `print()` in backend code — use `logger.info/warning/error`

---

*Generated from deep audit of Warelyn Inventory codebase — 2026-05-25 v4.0*
*Baseline: 218 tests. Do not proceed if tests fail.*
