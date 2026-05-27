# Warelyn Inventory — Complete Phase-by-Phase Repair & Build Plan

**Document version:** 2026-05-25 (Rev 2 — includes Jinja2 templates, gallery UI, provided HTML templates)
**Audit baseline:** 91 backend tests, Phases 1–14 code present
**Stack:** React + Vite + Tailwind CSS / FastAPI + SQLAlchemy + Alembic + MySQL
**PDF rendering:** WeasyPrint (replaces `build_simple_pdf` stub)
**Template engine:** Jinja2 (replaces `str.format_map` — critical engine change)

---

## 0. True Codebase Audit (Current State)

### Backend — What Exists

| Module | File | Status | Notes |
|--------|------|--------|-------|
| Auth | `api/auth.py`, `services/auth.py` | ✅ Complete | Register, login, refresh, me, logout |
| Admin | `api/admin.py`, `services/admin.py`, `repositories/admin.py` | ✅ Complete | Platform summary, health, tenant CRUD |
| Audit Logs | `api/audit.py`, `services/audit.py`, `repositories/audit.py` | ✅ Complete | List, create, tenant + admin views |
| Settings | `api/settings.py`, `services/settings.py`, `repositories/settings.py` | ✅ Complete | TenantSettings + UserPreferences |
| Notifications | `api/notifications.py`, `repositories/notification.py` | ✅ Complete | List, unread count, mark read |
| Verification | `api/verification.py`, `services/otp_service.py` | ✅ Complete | Email OTP + Phone OTP |
| Email Service | `services/email_service.py` | ✅ Complete | SMTP + log/dev mode |
| SMS Service | `services/sms_service.py` | ✅ Dev outbox | DB outbox, no real carrier |
| Documents (Invoice/Bill) | `api/documents.py`, `services/documents.py`, `repositories/documents.py` | ✅ Complete | CRUD, status transitions, send, number sequences |
| Document Templates | `services/documents.py → DocumentTemplateService` | 🔴 Engine broken | API complete; uses `str.format_map()` — incompatible with Jinja2 HTML templates |
| PDF Service | `services/pdf_service.py` | 🔴 Stub | `build_simple_pdf()` = raw text PDF, no tables, max 48 lines |
| Reports | `api/reports.py`, `services/reports.py` | ✅ Complete | 12 reports + CSV export |
| Product Import | `api/imports.py`, `services/imports.py` | ✅ Complete | CSV + XLSX (hand-rolled XML parser) |

### Frontend — What Exists

| Page / Component | Status | Notes |
|-----------------|--------|-------|
| Admin Dashboard, Tenants, Audit Logs, Platform Health | ✅ Complete | But uses same `MainLayout` as tenants |
| Settings Page | 🟡 Partial | Uses `document.getElementById` anti-pattern; no template editor links |
| Verification Pages | ✅ Complete | VerifyEmailPage, VerifyPhonePage |
| Notification Bell | ✅ Complete | Polls every 30s |
| Toast Provider | ✅ Wired | In `main.jsx`; no global API interceptor |
| Invoices / Bills Pages | ✅ Complete | List, detail, PDF download |
| Reports + CSV Export | ✅ Complete | SimpleReportPage with export button |
| Product Import | 🟡 Partial | Backend accepts XLSX; UI says "CSV only" |
| Admin Layout | 🔴 Missing | Admin routes nested inside tenant `MainLayout` |
| Email Template Editor | 🔴 Missing | No frontend page |
| PDF Template Gallery | 🔴 Missing | No frontend page |

---

## Critical Bug Catalogue

### BUG-001 — PDF Service Stub (Unusable Output)
**File:** `backend/app/services/pdf_service.py`
**Problem:** `build_simple_pdf()` writes raw PDF text operators with no CSS, no tables, no logo, max 48 lines. Invoice/bill PDFs produced by `render_invoice_pdf()` look like 1990s receipts.
**Fix:** Replace with `weasyprint.HTML(string=html).write_pdf()`. Add `weasyprint==62.3` to `requirements.txt`.

### BUG-002 — Template Engine Incompatibility (Critical)
**File:** `backend/app/services/documents.py → DocumentTemplateService._render()`
**Problem:** Current engine uses `template.format_map(SafeDict)` which only handles flat `{variable}` syntax. The provided real templates (`invoice.html`, `bill.html`, `document_email.html`, `otp_email.html`) use Jinja2 syntax:
- `{{ tenant.company_name }}` — nested object access (`.` notation)
- `{% for item in items %}` — loops
- `{% if tenant.phone %}` — conditionals
- `{{ document_kind|lower }}` — filters

These are 100% incompatible with `str.format_map()`. The templates will render broken or throw `KeyError`.
**Fix:** Replace `_render()` with `jinja2.Template(template_str).render(**context)`. Add `jinja2>=3.1.4` to `requirements.txt`.

### BUG-003 — Template Context is Flat (Incompatible with Provided Templates)
**File:** `backend/app/services/documents.py → _invoice_context()`, `_bill_context()`, `_base_template_context()`
**Problem:** Current context is a flat dict: `{"company_name": "...", "invoice_number": "...", "customer_name": "..."}`. The provided templates expect nested objects: `{{ tenant.company_name }}`, `{{ customer.name }}`, `{{ invoice.invoice_number }}`, `{% for item in items %}`.
**Fix:** Restructure all context-building methods to produce nested objects matching the provided template variable schema.

### BUG-004 — Template Auto-Seed Not Called in `render_by_key`
**File:** `backend/app/services/documents.py → DocumentTemplateService.render_by_key()`
**Problem:** `_ensure_defaults()` is only called in `list_templates()`. `render_by_key()` queries the DB directly and throws `DOCUMENT_TEMPLATE_NOT_FOUND` if no template exists. A new tenant verifying their email will hit a 404 error on their first action.
**Fix:** Add `self._ensure_defaults(tenant_id)` as the first line of `render_by_key()`.

### BUG-005 — `DocumentTemplate` Missing `body_template_text` Column
**File:** `backend/app/models/documents.py`
**Problem:** Email templates need both an HTML version (for email clients that render HTML) and a plain-text fallback. The model only has `body_template` (HTML). The provided `document_email.txt` and `otp_email.txt` are the text versions that need to be stored and sent as the plain-text MIME part.
**Fix:** Add `body_template_text: Mapped[str | None] = mapped_column(Text, nullable=True)` to `DocumentTemplate`. New Alembic migration required.

### BUG-006 — Admin Routes Use Tenant Layout
**File:** `frontend/src/routes/AppRoutes.jsx`
**Problem:** All `/admin/*` routes are nested inside `<MainLayout>`. Super admin sees tenant navigation sidebar.
**Fix:** Create `AdminLayout.jsx` with distinct platform admin shell. Rewire admin routes.

### BUG-007 — Settings Form Uses `document.getElementById`
**File:** `frontend/src/pages/SettingsPage.jsx`
**Problem:** Reads form values via `document.getElementById(field).value`. React anti-pattern, unreliable on partial renders.
**Fix:** Convert to controlled state with `useState`.

### BUG-008 — No Global API Error → Toast Bridge
**File:** `frontend/src/services/apiClient.js`
**Problem:** 401/403/500 errors silently fail unless each page has explicit `try/catch → toast`.
**Fix:** Module-level `setGlobalErrorHandler` callback registered by each layout.

### BUG-009 — `NotificationService` Named in Wrong Module
**File:** `backend/app/repositories/notification.py`
**Problem:** Class named `NotificationService` lives in `repositories/` layer.
**Fix:** Rename to `NotificationRepository`. Update import in `api/notifications.py`.

### BUG-010 — Product Import UI Does Not Mention XLSX
**File:** `frontend/src/pages/ProductImportPage.jsx`, `frontend/src/components/imports/CSVImportDropzone.jsx`
**Problem:** UI says "CSV file" everywhere despite backend accepting `.xlsx`.
**Fix:** Update copy, accept types, and add XLSX template download.

---

## The Provided Templates — Contract

These are the canonical template files. All backend default templates and the frontend template editor must use exactly these as defaults.

### `otp_email.html` — Email Verification OTP
**Channel:** EMAIL | **Key:** EMAIL_VERIFICATION
**Jinja2 variables:**
| Variable | Type | Description |
|----------|------|-------------|
| `{{ purpose }}` | string | e.g. `"email verification"` |
| `{{ code }}` | string | The OTP code |
| `{{ ttl_minutes }}` | int | Expiry in minutes |

**Note:** Uses `{{ purpose|lower }}` filter. Must render with Jinja2.

### `document_email.html` — Invoice/Bill Email Notification
**Channel:** EMAIL | **Key:** INVOICE_SEND, BILL_SEND
**Jinja2 variables:**
| Variable | Type | Description |
|----------|------|-------------|
| `{{ title }}` | string | e.g. `"Invoice INV-00001"` |
| `{{ intro }}` | string | Opening sentence |
| `{{ document_kind }}` | string | `"Invoice"` or `"Bill"` |
| `{{ document_number }}` | string | e.g. `"INV-00001"` |
| `{{ notes }}` | string or None | Optional notes |
| `{{ sender_name }}` | string | Company name or user name |

**Note:** Uses `{{ document_kind|lower }}` filter and `{% if notes %}` block.

### `invoice.html` — Invoice PDF
**Channel:** PDF | **Key:** PDF_INVOICE
**Jinja2 context objects:**
| Object | Fields |
|--------|--------|
| `tenant` | `company_name`, `contact_email`, `phone`, `address` |
| `customer` | `name`, `email`, `phone`, `billing_address` |
| `invoice` | `invoice_number`, `invoice_date`, `due_date`, `subtotal`, `tax_amount`, `discount_amount`, `total_amount`, `notes` |
| `sales_order` | `so_number` (or None) |
| `items[]` | `product_name`, `warehouse_name`, `quantity`, `unit_price`, `tax_rate`, `total_price` |

### `bill.html` — Bill PDF
**Channel:** PDF | **Key:** PDF_BILL
**Jinja2 context objects:**
| Object | Fields |
|--------|--------|
| `tenant` | `company_name`, `contact_email`, `phone`, `address` |
| `vendor` | `name`, `email`, `phone`, `address` |
| `bill` | `bill_number`, `bill_date`, `due_date`, `subtotal`, `tax_amount`, `total_amount`, `notes` |
| `purchase_order` | `po_number` (or None) |
| `items[]` | `product_name`, `warehouse_name`, `quantity_ordered`, `unit_price`, `tax_rate`, `total_price` |

---

## Phase Plan

### PHASE 15 — Jinja2 Template Engine + PDF + Document Foundation

**Priority:** P0 (PDF is broken, template engine is broken — both block email verification and document download)
**Test target:** 91 → ~108
**Files changed:** 5 backend files + 1 requirements + 1 migration

#### 15.1 — Add Dependencies

**File: `backend/requirements.txt`**
Add:
```
jinja2>=3.1.4
weasyprint==62.3
```

#### 15.2 — New Migration: `body_template_text` Column

**New file:** `backend/alembic/versions/20260525_0013_document_template_text_column.py`

```python
def upgrade():
    op.add_column('document_templates',
        sa.Column('body_template_text', sa.Text(), nullable=True)
    )

def downgrade():
    op.drop_column('document_templates', 'body_template_text')
```

**File: `backend/app/models/documents.py`**
Add to `DocumentTemplate`:
```python
body_template_text: Mapped[str | None] = mapped_column(Text, nullable=True)
```

#### 15.3 — Fix BUG-002 + BUG-003: Replace Template Engine + Restructure Context

**File: `backend/app/services/documents.py`**

**Step A — Replace `_render()` method:**
```python
import jinja2

def _render(self, template_str: str | None, context: dict) -> str:
    if not template_str:
        return ""
    try:
        return jinja2.Template(template_str).render(**context)
    except jinja2.TemplateError:
        # Fallback: return template as-is rather than crash
        return template_str
```

**Step B — Update `DEFAULT_TEMPLATES` dict:**

Replace all current body_template strings with the exact content of the provided HTML files. Replace "Northstar Inventory" with "Warelyn Inventory" in all HTML defaults.

```python
# EMAIL_VERIFICATION
"body_template": """[full content of otp_email.html with "Northstar" → "Warelyn"]""",
"body_template_text": """[full content of otp_email.txt]""",

# INVOICE_SEND
"body_template": """[full content of document_email.html]""",
"body_template_text": """[full content of document_email.txt]""",

# BILL_SEND — same templates as INVOICE_SEND (document_kind will be "Bill")
"body_template": """[full content of document_email.html]""",
"body_template_text": """[full content of document_email.txt]""",

# PDF_INVOICE
"body_template": """[full content of invoice.html]""",
"body_template_text": None,

# PDF_BILL
"body_template": """[full content of bill.html]""",
"body_template_text": None,
```

**Step C — Restructure context builders to nested objects:**

Replace flat dict with Jinja2-compatible nested object dicts:

```python
def _base_template_context(self, tenant_id: int) -> dict:
    tenant = self.repository.get_tenant(tenant_id)
    settings = self.repository.get_tenant_settings(tenant_id)
    return {
        "tenant": {
            "company_name": (settings.company_display_name if settings else None) or (tenant.company_name if tenant else "Warelyn"),
            "contact_email": (settings.contact_email if settings else None) or (tenant.contact_email if tenant else ""),
            "phone": settings.phone if settings else None,
            "address": settings.address_line1 if settings else None,
            "logo_url": settings.document_logo_url if settings else None,
            "footer": settings.document_footer if settings else "Generated by Warelyn",
            "currency": settings.currency if settings else "USD",
        }
    }

def _invoice_context(self, invoice: Invoice) -> dict:
    customer = self.repository.get_customer(invoice.tenant_id, invoice.customer_id)
    so = self.repository.get_sales_order(invoice.sales_order_id) if invoice.sales_order_id else None
    items = [
        {
            "product_name": item.description or f"Product #{item.product_id}",
            "warehouse_name": "",           # populated if fulfillment has location
            "quantity": str(item.quantity),
            "unit_price": str(item.unit_price),
            "tax_rate": str(item.tax_rate or "0"),
            "total_price": str(item.line_total),
        }
        for item in (invoice.items or [])
    ]
    return {
        "invoice": {
            "invoice_number": invoice.invoice_number,
            "invoice_date": str(invoice.issue_date),
            "due_date": str(invoice.due_date) if invoice.due_date else None,
            "subtotal": str(invoice.subtotal_amount),
            "tax_amount": str(invoice.tax_amount),
            "discount_amount": str(invoice.discount_amount),
            "total_amount": str(invoice.total_amount),
            "notes": invoice.notes if hasattr(invoice, "notes") else None,
            # Email-template fields
            "title": f"Invoice {invoice.invoice_number}",
            "intro": f"Please find attached invoice {invoice.invoice_number}.",
            "document_kind": "Invoice",
            "document_number": invoice.invoice_number,
            "sender_name": "",             # filled from base context
        },
        "customer": {
            "name": customer.name if customer else f"Customer #{invoice.customer_id}",
            "email": customer.contact_email if customer else None,
            "phone": customer.phone if customer else None,
            "billing_address": None,
        },
        "sales_order": {"so_number": so.so_number} if so else None,
        "items": items,
    }

def _bill_context(self, bill: Bill) -> dict:
    vendor = self.repository.get_vendor(bill.tenant_id, bill.vendor_id)
    po = self.repository.get_purchase_order(bill.purchase_order_id) if bill.purchase_order_id else None
    items = [
        {
            "product_name": item.description or f"Product #{item.product_id}",
            "warehouse_name": "",
            "quantity_ordered": str(item.quantity),
            "unit_price": str(item.unit_cost),
            "tax_rate": "0",
            "total_price": str(item.line_total),
        }
        for item in (bill.items or [])
    ]
    return {
        "bill": {
            "bill_number": bill.bill_number,
            "bill_date": str(bill.issue_date),
            "due_date": str(bill.due_date) if bill.due_date else None,
            "subtotal": str(bill.subtotal_amount),
            "tax_amount": str(bill.tax_amount),
            "total_amount": str(bill.total_amount),
            "notes": None,
            # Email-template fields
            "title": f"Bill {bill.bill_number}",
            "intro": f"Please find attached bill {bill.bill_number}.",
            "document_kind": "Bill",
            "document_number": bill.bill_number,
            "sender_name": "",
        },
        "vendor": {
            "name": vendor.name if vendor else f"Vendor #{bill.vendor_id}",
            "email": vendor.contact_email if vendor else None,
            "phone": vendor.phone if vendor else None,
            "address": vendor.address if vendor else None,
        },
        "purchase_order": {"po_number": po.po_number} if po else None,
        "items": items,
    }
```

**Step D — Fix BUG-004: Add `_ensure_defaults` to `render_by_key`:**
```python
def render_by_key(self, tenant_id, channel, template_key, extra_context=None):
    self._ensure_defaults(tenant_id)   # ← ADD THIS LINE
    template = self.repository.get_template_by_key(tenant_id, channel, template_key)
    ...
```

**Step E — Update `_ensure_defaults` to persist `body_template_text`:**
```python
def _ensure_defaults(self, tenant_id: int) -> None:
    for (channel, key), payload in DEFAULT_TEMPLATES.items():
        existing = self.repository.get_template_by_key(tenant_id, channel, key)
        if existing is None:
            self.repository.create_template({
                "tenant_id": tenant_id,
                "channel": channel,
                "template_key": key,
                "name": payload["name"],
                "subject_template": payload["subject_template"],
                "body_template": payload["body_template"],
                "body_template_text": payload.get("body_template_text"),   # ← new field
                "is_active": payload["is_active"],
            })
    self.db.flush()
```

**Step F — Update `email_service.send_email` call to pass both HTML and text:**

In `verification.py` and `documents.py`, when sending email, pass both `body_html` and `body_text`:
```python
rendered = DocumentTemplateService(db).render_by_key(...)
send_email(
    to_email,
    rendered["subject"],
    body_text=rendered.get("text") or rendered["body"],  # plain-text fallback
    body_html=rendered["body"] if "<html" in rendered["body"] else None,
)
```

Update `render_by_key` return dict to include `"text"` key from `body_template_text`.

#### 15.4 — Replace PDF Service

**File: `backend/app/services/pdf_service.py`** (full replacement)

```python
from __future__ import annotations
import logging
logger = logging.getLogger(__name__)

try:
    import weasyprint
    _WEASYPRINT_AVAILABLE = True
except ImportError:
    _WEASYPRINT_AVAILABLE = False
    logger.warning("weasyprint not installed; PDF output will be degraded.")


def render_html_to_pdf(html: str) -> bytes:
    """Render an HTML string to PDF bytes using WeasyPrint."""
    if not _WEASYPRINT_AVAILABLE:
        return _fallback_pdf(html)
    return weasyprint.HTML(string=html).write_pdf()


def _fallback_pdf(html: str) -> bytes:
    """Minimal valid PDF when WeasyPrint is not available (dev only)."""
    import re
    text = re.sub(r'<[^>]+>', ' ', html).strip()[:2000]
    lines = [line.strip() for line in text.split('\n') if line.strip()][:40]
    return build_simple_pdf("Document", lines)


def build_simple_pdf(title: str, lines) -> bytes:
    """Legacy stub kept for compatibility. Use render_html_to_pdf() in production."""
    from typing import Iterable
    def _esc(v: str) -> str:
        return v.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    content_lines = ["BT", "/F1 18 Tf", "50 790 Td", f"({_esc(title)}) Tj", "/F1 10 Tf"]
    remaining = 760
    for line in list(lines)[:48]:
        content_lines += [f"50 {remaining} Td", f"({_esc(line)}) Tj"]
        remaining -= 14
    content_lines.append("ET")
    stream = "\n".join(content_lines).encode("latin-1", errors="replace")
    objects = [
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj",
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj",
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj",
        b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj",
        b"5 0 obj << /Length %d >> stream\n%s\nendstream endobj" % (len(stream), stream),
    ]
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = []
    for obj in objects:
        offsets.append(len(pdf))
        pdf.extend(obj + b"\n")
    xref_start = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode())
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets:
        pdf.extend(f"{offset:010d} 00000 n \n".encode())
    pdf.extend(f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_start}\n%%EOF".encode())
    return bytes(pdf)
```

Update `render_invoice_pdf()` and `render_bill_pdf()` in `documents.py`:
```python
def render_invoice_pdf(self, tenant_id: int, invoice_id: int) -> bytes:
    invoice = self.get_invoice(tenant_id, invoice_id)
    context = {**self._base_template_context(tenant_id), **self._invoice_context(invoice)}
    # Set sender_name from tenant context
    context["invoice"]["sender_name"] = context["tenant"]["company_name"]
    rendered = self.templates.render_by_key(
        tenant_id, DocumentTemplateChannel.PDF, DocumentTemplateKey.PDF_INVOICE, context
    )
    invoice.pdf_generated_at = _naive_utcnow()
    self.db.commit()
    return render_html_to_pdf(rendered["body"])
```

#### 15.5 — Update Document Schemas

**File: `backend/app/schemas/documents.py`**

Add `body_template_text` to `DocumentTemplateRead` and `DocumentTemplateUpdate`.

#### 15.6 — Tests

**File: `backend/tests/test_documents.py`** — add:
- `test_invoice_pdf_returns_valid_pdf_bytes`
- `test_bill_pdf_returns_valid_pdf_bytes`
- `test_email_verification_send_on_fresh_tenant_does_not_404`
- `test_invoice_template_renders_with_jinja2_for_loop`
- `test_bill_template_renders_vendor_name`
- `test_template_html_and_text_both_stored`
- `test_invoice_mark_paid_status_transition`
- `test_invoice_void_status_transition`

---

### PHASE 16 — Admin Layout + Super Admin UX

**Priority:** P1
**Test target:** ~108 → ~116
**Fixes:** BUG-006, BUG-009

#### 16.1 — Create `AdminLayout.jsx`

**New file:** `frontend/src/layouts/AdminLayout.jsx`

Design — visually distinct from `MainLayout`:
- Full `min-h-screen` two-panel layout
- Left sidebar: deep navy `bg-[#0F2460]` or `bg-warelyn-primary` variant
  - Warelyn logo at top in white
  - `PLATFORM ADMIN` badge label below logo (small caps, amber/gold color)
  - Navigation items: Platform Console, Tenants, Audit Logs, Platform Health
  - No inventory/sales/warehouse nav items
  - User name at bottom with logout button
- Top bar: dark navy stripe
  - "Warelyn Platform Console" text (left)
  - Logged-in user chip (right) — no bell, no QuickCreate, no RecentHistory, no topbar search
- Main content: `<Outlet />` with standard page padding

#### 16.2 — Wire Admin Routes to `AdminLayout`

**File:** `frontend/src/routes/AppRoutes.jsx`

```jsx
// Separate block for super admin — outside the MainLayout block
<Route element={<ProtectedRoute requiredRole="SUPER_ADMIN" />}>
  <Route element={<AdminLayout />}>
    <Route path="admin" element={<AdminDashboardPage />} />
    <Route path="admin/tenants" element={<TenantsPage />} />
    <Route path="admin/tenants/:id" element={<TenantDetailPage />} />
    <Route path="admin/audit-logs" element={<AuditLogsPage />} />
    <Route path="admin/platform-health" element={<PlatformHealthPage />} />
  </Route>
</Route>
```

#### 16.3 — Update `ProtectedRoute`

**File:** `frontend/src/routes/ProtectedRoute.jsx`

Add optional `requiredRole` prop. If `user.role !== requiredRole`, redirect to `/dashboard`.

#### 16.4 — Fix BUG-009: Rename `NotificationService` → `NotificationRepository`

**File:** `backend/app/repositories/notification.py` — rename class
**File:** `backend/app/api/notifications.py` — update import

---

### PHASE 17 — Settings Fix + Global Toast

**Priority:** P1
**Test target:** ~116 → ~122
**Fixes:** BUG-007, BUG-008

#### 17.1 — Fix Settings Page (BUG-007)

**File:** `frontend/src/pages/SettingsPage.jsx`

Replace `document.getElementById` with `useState`:
```jsx
const [form, setForm] = useState({
  company_display_name: settings?.company_display_name ?? '',
  contact_email: settings?.contact_email ?? '',
  // ... all fields
});
<Input
  value={form.company_display_name}
  onChange={e => setForm(p => ({...p, company_display_name: e.target.value}))}
/>
```

#### 17.2 — Global API Error Interceptor (BUG-008)

**File:** `frontend/src/services/apiClient.js`
```js
let _globalErrorHandler = null;
export function setGlobalErrorHandler(fn) { _globalErrorHandler = fn; }

// In apiRequest error branch:
if (_globalErrorHandler) {
  if (response.status === 401) {
    _globalErrorHandler('Session expired. Please log in again.', 'error');
  } else if (response.status === 403) {
    _globalErrorHandler('You do not have permission for this action.', 'error');
  } else if (response.status >= 500) {
    _globalErrorHandler(errorMessage, 'error');
  }
}
```

**Files:** `frontend/src/layouts/MainLayout.jsx` and `frontend/src/layouts/AdminLayout.jsx`
```jsx
import { setGlobalErrorHandler } from '../services/apiClient.js';
const toast = useToast();
useEffect(() => {
  setGlobalErrorHandler((msg, type) => toast[type]?.(msg));
  return () => setGlobalErrorHandler(null);
}, [toast]);
```

#### 17.3 — Settings Template Shortcut Cards

**File:** `frontend/src/pages/SettingsPage.jsx`

Add a "Templates" section with two cards linking to the template editors (built in Phase 17A/17B).

---

### PHASE 17A — Email Template Editor

**PRD alignment:** §16.1
**Priority:** P2
**Test target:** ~122 → ~130

#### 17A.1 — UI Design (from Screenshot Reference)

Based on the provided screenshots, the email template UI has two views:

**List view** (Screenshot 2 reference):
- Page title: "Email Templates" with description below
- Table with columns: NAME (with DEFAULT badge) | SUBJECT AND CONTENT (shows subject + "Show Mail Content" expandable)
- "+ New" button (reserved for future)

**Editor view** (Screenshot 3 reference):
- Modal or slide-over panel titled `"[Template Name] — Edit"`
- Fields:
  - Template Name (text input)
  - Subject (text input with `{{ variable }}` placeholders)
  - Body (rich text or monospace textarea)
  - **"Insert Placeholder" dropdown** — opens a dropdown menu with all available variables for that template type; clicking inserts `{{ variable_name }}` at cursor position
- Buttons: Save, Cancel, Preview

#### 17A.2 — Frontend: `EmailTemplatesPage.jsx`

**New file:** `frontend/src/pages/EmailTemplatesPage.jsx`

**Architecture:**
```jsx
// State
const [templates, setTemplates] = useState([]);  // fetched from GET /templates?channel=EMAIL
const [selected, setSelected] = useState(null);   // currently editing template
const [form, setForm] = useState({subject_template: '', body_template: '', body_template_text: ''});
const [preview, setPreview] = useState(null);     // rendered preview result

// Layout: table list on left, editor panel on right (desktop)
// On mobile: list view → tap → full editor view
```

**Variable placeholder map** (per template key):
```js
const PLACEHOLDER_VARS = {
  EMAIL_VERIFICATION: [
    { label: 'Verification Code', value: '{{ code }}' },
    { label: 'Purpose', value: '{{ purpose }}' },
    { label: 'Expires In (minutes)', value: '{{ ttl_minutes }}' },
  ],
  INVOICE_SEND: [
    { label: 'Title', value: '{{ title }}' },
    { label: 'Intro Text', value: '{{ intro }}' },
    { label: 'Document Kind', value: '{{ document_kind }}' },
    { label: 'Document Number', value: '{{ document_number }}' },
    { label: 'Notes', value: '{{ notes }}' },
    { label: 'Sender Name', value: '{{ sender_name }}' },
  ],
  BILL_SEND: [
    // same as INVOICE_SEND
  ],
};
```

**Insert Placeholder button:**
```jsx
function insertAtCursor(textareaRef, placeholder) {
  const el = textareaRef.current;
  const start = el.selectionStart;
  const end = el.selectionEnd;
  const value = el.value;
  const newValue = value.substring(0, start) + placeholder + value.substring(end);
  setForm(p => ({...p, body_template: newValue}));
  // Restore cursor after inserted text
  setTimeout(() => {
    el.selectionStart = el.selectionEnd = start + placeholder.length;
    el.focus();
  }, 0);
}
```

**Preview flow:**
1. User clicks "Preview"
2. Call `POST /templates/{id}/preview` with sample variable values
3. Show result in a modal: subject in header, body rendered in an `<iframe srcdoc={body}>` (for HTML) or `<pre>` (for text)

#### 17A.3 — Add Document Service Functions

**File:** `frontend/src/services/documentService.js`
```js
export function listTemplates(accessToken, channel) {
  return apiRequest(`/templates${channel ? `?channel=${channel}` : ''}`, { accessToken });
}
export function getTemplate(accessToken, id) {
  return apiRequest(`/templates/${id}`, { accessToken });
}
export function updateTemplate(accessToken, id, payload) {
  return apiRequest(`/templates/${id}`, {
    accessToken, method: 'PATCH', body: JSON.stringify(payload),
  });
}
export function previewTemplate(accessToken, id, variables) {
  return apiRequest(`/templates/${id}/preview`, {
    accessToken, method: 'POST', body: JSON.stringify({ variables }),
  });
}
```

#### 17A.4 — Routes + Navigation

**File:** `frontend/src/routes/AppRoutes.jsx`
```jsx
<Route path="settings/email-templates" element={<EmailTemplatesPage />} />
```

**File:** `frontend/src/components/navigation.js`
Add under Settings: `{ label: 'Email Templates', to: '/settings/email-templates', roles: ['TENANT_ADMIN'] }`

---

### PHASE 17B — PDF Template Gallery + Editor

**PRD alignment:** §16.4
**Priority:** P2
**Test target:** ~130 → ~136

#### 17B.1 — UI Design (from Screenshot Reference)

Based on Screenshot 1 (invoice template gallery):

**Gallery view:**
- Page title: "Invoice & Bill PDF Templates"
- Card grid (2–3 columns) — each card shows:
  - Scaled thumbnail preview of the PDF template rendered as HTML in a small `<iframe>` (scale: 0.3)
  - Template name below the card
  - `DEFAULT` badge (star icon + amber chip) on the active template
  - Hover state: "Edit" overlay button
- "+ New" button (reserved for future)

**Editor view** (slide-over or full page):
- Template name (input)
- HTML source textarea (large, monospace)
- Variable reference panel (collapsible list of all available Jinja2 variables)
- Live preview panel: renders the HTML with sample data in an `<iframe srcdoc>`
- "Download PDF Preview" button — calls `POST /templates/{id}/preview-pdf`
- Save / Reset to Default buttons

#### 17B.2 — Backend: PDF Preview Endpoint

**File:** `backend/app/api/documents.py`
```python
@router.post("/templates/{template_id}/preview-pdf")
def preview_template_pdf(
    template_id: int,
    request: DocumentTemplatePreviewRequest,
    context: UserContext = Depends(require_roles(*admin_roles)),
    db: Session = Depends(get_db),
) -> Response:
    pdf_bytes = DocumentsService(db).preview_template_pdf(
        context.tenant_id, template_id, request.variables or {}
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "inline; filename=preview.pdf"},
    )
```

**File:** `backend/app/services/documents.py`
```python
def preview_template_pdf(self, tenant_id: int, template_id: int, variables: dict) -> bytes:
    # Merge provided variables with sample data for missing variables
    sample = self._sample_pdf_invoice_context()
    context = {**sample, **variables}
    rendered = self.templates.preview_template(tenant_id, template_id, context)
    return render_html_to_pdf(rendered["body"])

def _sample_pdf_invoice_context(self) -> dict:
    """Returns realistic sample data for PDF preview."""
    return {
        "tenant": {
            "company_name": "Sample Company Ltd",
            "contact_email": "info@sample.com",
            "phone": "+1 555-0100",
            "address": "123 Business Ave, Suite 200",
            "logo_url": None,
            "footer": "Thank you for your business.",
            "currency": "USD",
        },
        "customer": {"name": "John Doe", "email": "john@example.com", "phone": "+1 555-0200", "billing_address": "456 Customer St"},
        "invoice": {
            "invoice_number": "INV-00001",
            "invoice_date": "2026-05-25",
            "due_date": "2026-06-25",
            "subtotal": "1,000.00",
            "tax_amount": "180.00",
            "discount_amount": "0.00",
            "total_amount": "1,180.00",
            "notes": "Net 30 payment terms.",
        },
        "sales_order": {"so_number": "SO-00001"},
        "items": [
            {"product_name": "Product A", "warehouse_name": "Main WH", "quantity": "10", "unit_price": "50.00", "tax_rate": "18", "total_price": "500.00"},
            {"product_name": "Product B", "warehouse_name": "Main WH", "quantity": "5",  "unit_price": "100.00", "tax_rate": "18", "total_price": "500.00"},
        ],
    }
```

#### 17B.3 — Frontend: `PdfTemplatesPage.jsx`

**New file:** `frontend/src/pages/PdfTemplatesPage.jsx`

**Gallery component:**
```jsx
// Thumbnail preview card using iframe
function TemplateCard({ template, isDefault, onEdit }) {
  return (
    <div className="group relative cursor-pointer rounded-xl border border-warelyn-border overflow-hidden hover:shadow-lg transition">
      {/* Scaled iframe preview */}
      <div className="relative h-64 overflow-hidden bg-gray-50">
        <iframe
          srcDoc={template.body_template}
          title={template.name}
          className="absolute top-0 left-0 w-full border-0"
          style={{ transform: 'scale(0.3)', transformOrigin: 'top left', width: '333%', height: '333%', pointerEvents: 'none' }}
        />
        {/* Hover overlay */}
        <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition flex items-center justify-center">
          <Button className="opacity-0 group-hover:opacity-100 transition" variant="primary" onClick={() => onEdit(template)}>
            Edit
          </Button>
        </div>
      </div>
      {/* Footer */}
      <div className="p-3 flex items-center gap-2">
        <span className="text-sm font-medium">{template.name}</span>
        {isDefault && (
          <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-700">
            ⭐ DEFAULT
          </span>
        )}
      </div>
    </div>
  );
}
```

#### 17B.4 — Routes + Navigation

**File:** `frontend/src/routes/AppRoutes.jsx`
```jsx
<Route path="settings/pdf-templates" element={<PdfTemplatesPage />} />
```

**File:** `frontend/src/services/documentService.js`
```js
export async function previewTemplatePdf(accessToken, id, variables) {
  const response = await fetch(`${API_BASE_URL}/templates/${id}/preview-pdf`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${accessToken}` },
    body: JSON.stringify({ variables }),
  });
  if (!response.ok) throw new Error('PDF preview failed.');
  return response.blob();
}
```

---

### PHASE 17C — XLSX Import UI Fix

**Priority:** P2
**Test target:** ~136 → ~140
**Fixes:** BUG-010

#### 17C.1 — Update Import UI Copy

**File:** `frontend/src/components/imports/CSVImportDropzone.jsx`
```jsx
accept=".csv,.xlsx,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
// Label: "Upload CSV or XLSX file"
// Helper: "Supported formats: CSV (.csv) and Excel (.xlsx)"
```

**File:** `frontend/src/pages/ProductImportPage.jsx`
- Title: "Import Products — CSV or XLSX"
- Add download row: "CSV Template" + "XLSX Template" buttons
- XLSX template URL: `GET /api/imports/products/template.xlsx`

#### 17C.2 — Backend: XLSX Template Endpoint

**File:** `backend/app/api/imports.py`
```python
@router.get("/template.xlsx")
def download_import_template_xlsx(
    context: UserContext = Depends(require_roles(*writer_roles)),
) -> Response:
    content = ProductImportService.build_template_xlsx()
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="products-import-template.xlsx"'},
    )
```

Add `build_template_xlsx()` static method to `ProductImportService` using the existing hand-rolled XML builder.

---

### PHASE 18 — Operational Completion

**Priority:** P2–P3
**Test target:** ~140 → ~170

#### 18.1 — Stock State Expansion

New Alembic migration adding 5 columns to `warehouse_stock`:
- `quantity_in_transit`, `quantity_qc_hold`, `quantity_damaged`, `quantity_expired`, `quantity_quarantine` — all `DECIMAL(15,4) DEFAULT 0.0000`

Update `InventoryEngine.blocked()`, `damaged()` to populate the correct column.
Add `InventoryEngine.expire_batch(batch_id, quantity)` method.
Update `WarehouseStockReportRow` schema with new fields.

#### 18.2 — Reorder Rules Persistence

New `reorder_rules` table: `min_quantity`, `max_quantity`, `safety_stock`, `lead_time_days`, `auto_create_po`, `is_active`.
Full CRUD: model → migration → repository → service → API.
Frontend: `ReorderRulesPage.jsx` linked from Purchases nav.

#### 18.3 — Putaway Tasks Foundation

New `putaway_tasks` table (status: PENDING → IN_PROGRESS → DONE).
Wire to purchasing service: on receipt commit in bin-tracked warehouses, create putaway tasks.
Frontend: `PutawayTasksPage.jsx`.

#### 18.4 — Cycle Counts Foundation

New `stock_count_sessions` + `stock_count_lines` tables.
Session workflow: DRAFT → IN_PROGRESS → SUBMITTED → RECONCILED.
Frontend: `CycleCountsPage.jsx` under Inventory.

#### 18.5 — Expiry Background Job

New `backend/app/jobs/expire_batches.py` using FastAPI `BackgroundTasks`.
Admin-only endpoint: `POST /admin/jobs/run-expiry-check`.

#### 18.6 — Events Outbox

New `outbox_events` table (event_type, payload_json, status PENDING/PROCESSED/FAILED).
New `backend/app/events/outbox.py` with `publish()` and `process_pending()`.

---

## Feature Delivery Checklist

| # | Feature | Backend | Frontend | Phase | Status |
|---|---------|---------|---------|-------|--------|
| 1 | Super Admin personalized screens | ✅ | 🔴 No AdminLayout | Phase 16 | Needs AdminLayout |
| 2 | Phone SMS verification | ✅ | ✅ | — | ✅ Done |
| 3 | Email verification | ✅ routes | 🔴 BUG-004 crash on new tenants | Phase 15 | Needs BUG-002/004 fix |
| 4 | In-app notifications | ✅ | ✅ | — | ✅ Done |
| 5 | Toast notifications (global) | ✅ | 🟡 No global interceptor | Phase 17 | Needs BUG-008 fix |
| 6 | Bill and invoice generation | ✅ | ✅ | — | ✅ Done |
| 7 | Bill/invoice PDF download | ✅ routes | 🔴 BUG-001 unusable output | Phase 15 | Needs BUG-001+002+003 fix |
| 8 | Report CSV export | ✅ | ✅ | — | ✅ Done |
| 9 | XLSX import | ✅ | 🟡 UI says CSV only | Phase 17C | Needs BUG-010 fix |
| 10 | Settings page | ✅ | 🟡 DOM anti-pattern | Phase 17 | Needs BUG-007 fix |
| 11 | Custom email templates + preview | ✅ API | 🔴 No editor page | Phase 17A | Needs new FE page |
| 12 | Custom PDF templates + preview | ✅ API | 🔴 No gallery/editor | Phase 17B | Needs FE gallery + PDF preview endpoint |

---

## Recommended Phase Order

```
Phase 15  →  Jinja2 engine + WeasyPrint PDF + HTML templates + plain-text email  (BUG-001–005)
Phase 16  →  Admin Layout + Super Admin UX                                        (BUG-006, BUG-009)
Phase 17  →  Settings fix + Global toast interceptor                              (BUG-007, BUG-008)
Phase 17A →  Email Template Editor (list view + WYSIWYG + Insert Placeholder)    (Feature #11)
Phase 17B →  PDF Template Gallery + Editor (card thumbnails + PDF preview)        (Feature #12)
Phase 17C →  XLSX Import UI fix + template download                               (Feature #9, BUG-010)
Phase 18  →  Operational Completion (stock states, reorder, putaway, cycle counts, jobs)
```

---

## Complete File Change Map

### Phase 15

| File | Change |
|------|--------|
| `backend/requirements.txt` | Add `jinja2>=3.1.4`, `weasyprint==62.3` |
| `backend/alembic/versions/20260525_0013_document_template_text_column.py` | **NEW** — add `body_template_text` column |
| `backend/app/models/documents.py` | Add `body_template_text` column to `DocumentTemplate` |
| `backend/app/services/pdf_service.py` | Full replacement — `render_html_to_pdf()` + WeasyPrint |
| `backend/app/services/documents.py` | `_render()` → Jinja2; `DEFAULT_TEMPLATES` → provided HTML files; restructure `_invoice_context()`, `_bill_context()`, `_base_template_context()` to nested objects; fix `render_by_key()` auto-seed; update `render_invoice_pdf()` and `render_bill_pdf()` to call `render_html_to_pdf()`; update `_ensure_defaults()` to persist `body_template_text` |
| `backend/app/schemas/documents.py` | Add `body_template_text` to template schemas |
| `backend/app/api/verification.py` | Pass both HTML and text to `send_email()` |
| `backend/tests/test_documents.py` | +8 new tests |

### Phase 16

| File | Change |
|------|--------|
| `frontend/src/layouts/AdminLayout.jsx` | **NEW** |
| `frontend/src/routes/AppRoutes.jsx` | Rewire admin routes to AdminLayout |
| `frontend/src/routes/ProtectedRoute.jsx` | Add `requiredRole` prop |
| `frontend/src/pages/AdminDashboardPage.jsx` | Add recent tenants list |
| `frontend/src/styles/index.css` | Admin layout CSS additions |
| `backend/app/repositories/notification.py` | Rename class |
| `backend/app/api/notifications.py` | Update import |

### Phase 17

| File | Change |
|------|--------|
| `frontend/src/pages/SettingsPage.jsx` | Replace `getElementById` with controlled state |
| `frontend/src/services/apiClient.js` | Add `setGlobalErrorHandler` + error interception |
| `frontend/src/layouts/MainLayout.jsx` | Register global error handler |
| `frontend/src/layouts/AdminLayout.jsx` | Register global error handler |

### Phase 17A

| File | Change |
|------|--------|
| `frontend/src/pages/EmailTemplatesPage.jsx` | **NEW** — list + editor + Insert Placeholder |
| `frontend/src/services/documentService.js` | Add 4 template service functions |
| `frontend/src/routes/AppRoutes.jsx` | Add route |
| `frontend/src/components/navigation.js` | Add Settings sub-item |

### Phase 17B

| File | Change |
|------|--------|
| `backend/app/api/documents.py` | Add `POST /templates/{id}/preview-pdf` endpoint |
| `backend/app/services/documents.py` | Add `preview_template_pdf()` + `_sample_pdf_invoice_context()` |
| `frontend/src/pages/PdfTemplatesPage.jsx` | **NEW** — card gallery + editor + iframe preview |
| `frontend/src/services/documentService.js` | Add `previewTemplatePdf()` |
| `frontend/src/routes/AppRoutes.jsx` | Add route |

### Phase 17C

| File | Change |
|------|--------|
| `backend/app/api/imports.py` | Add `GET /imports/products/template.xlsx` |
| `backend/app/services/imports.py` | Add `build_template_xlsx()` static method |
| `frontend/src/components/imports/CSVImportDropzone.jsx` | Accept types + copy |
| `frontend/src/pages/ProductImportPage.jsx` | Title + XLSX template download |

### Phase 18

| File | Change |
|------|--------|
| 5 new Alembic migrations | stock_state_expansion, reorder_rules, putaway_tasks, cycle_counts, outbox_events |
| 3 new model files | `models/reorder_rules.py`, `models/putaway.py`, `models/cycle_count.py` |
| `backend/app/models/inventory.py` | +5 state columns to WarehouseStock |
| `backend/app/domain/inventory/engine.py` | Updated blocked/damaged/expire methods |
| `backend/app/events/outbox.py` | **NEW** |
| `backend/app/jobs/expire_batches.py` | **NEW** |
| 3 new repository files | reorder_rules, putaway, cycle_count |
| 3 new service files | reorder_rules, putaway, cycle_count |
| 3 new API files | reorder_rules, putaway, cycle_counts |
| `backend/app/api/router.py` | Include 3 new routers |
| `backend/app/models/__init__.py` | Export new models |
| 3 new frontend pages | ReorderRulesPage, PutawayTasksPage, CycleCountsPage |
| 3 new frontend services | reorderService, putawayService, cycleCountService |
| `frontend/src/routes/AppRoutes.jsx` | +3 routes |
| `frontend/src/components/navigation.js` | +3 nav items |

---

## Test Count Progression

| After Phase | Min Tests | Notes |
|-------------|-----------|-------|
| Phase 14 baseline | 91 | Current state |
| Phase 15 | 108 | +17: Jinja2 render, PDF bytes, template auto-seed, text column, status transitions |
| Phase 16 | 116 | +8: admin role guard, layout redirect, notification repo rename |
| Phase 17 | 122 | +6: settings save, global toast, 401 intercept |
| Phase 17A | 130 | +8: template list, update, preview, insert placeholder |
| Phase 17B | 136 | +6: PDF preview endpoint, sample context, gallery load |
| Phase 17C | 140 | +4: XLSX template download, import UI accept |
| Phase 18 | 170 | +30: stock states, reorder CRUD, putaway, cycle count, expiry job |

---

## Architecture Rules (Non-Negotiable)

1. **No stock mutations outside `InventoryEngine`**
2. **`tenant_id` comes from `UserContext`, never from request body**
3. **Jinja2 for all template rendering** — no `str.format_map`, no f-string injection
4. **Alembic migration for every DB change**
5. **`db.commit()` only in service layer, never in repositories**
6. **No `document.getElementById` in React** — controlled state only
7. **Role check on every endpoint**
8. **All API calls go through `services/*.js`** — no `fetch()` in pages
9. **Test count must never decrease**
10. **Template HTML stored in DB** — `DEFAULT_TEMPLATES` seeds on first use, tenant can override
