# WARELYN INVENTORY — CLAUDE SONNET 4.6 BUILD INSTRUCTIONS

**Read this entire file before writing any code, migration, or test.**

This is the single source of truth for building Warelyn Inventory. It includes exact implementation steps, the critical Jinja2 engine migration, the provided HTML templates, the UI design spec from screenshots, and all architectural rules.

---

## 0. Project Identity

**Product:** Warelyn Inventory — multi-tenant inventory and warehouse SaaS
**Stack:** Python 3.12 + FastAPI + SQLAlchemy 2.0 + Alembic + MySQL (backend) / React 18 + Vite + Tailwind CSS 3 (frontend)
**PDF library:** WeasyPrint (renders HTML+CSS → PDF bytes)
**Template engine:** Jinja2 (CRITICAL — replaces the broken `str.format_map` approach)
**Dev email:** SMTP to Mailpit/MailHog on port 1025 or `log` mode
**Dev SMS:** In-memory DB outbox (no real carrier)

---

## 1. Rules That Must Never Be Violated

| Rule | Consequence of violation |
|------|--------------------------|
| All stock mutations go through `InventoryEngine` in `backend/app/domain/inventory/engine.py` | Inventory numbers become wrong — the core product value is destroyed |
| `tenant_id` comes from `UserContext`, never from request body | Tenant isolation security hole |
| Jinja2 for all template rendering — no `str.format_map()`, no f-string injection | Templates with `{% for %}` and `{{ obj.field }}` will break or crash |
| Alembic migration for every DB schema change | DB won't have the column/table in production |
| `db.commit()` only in service layer, never in repositories | Double-commit or missing-commit bugs |
| No `document.getElementById` in any React file | React state becomes stale and unreliable |
| Role check on every new API endpoint | Authorization bypass |
| All API calls go through `frontend/src/services/*.js` | Untestable, duplicated fetch logic in pages |
| Test count must never decrease from current baseline of 91 | Regression without notification |
| Template HTML/Jinja2 bodies stored in `document_templates` DB table | Tenant customization requires DB-stored templates, not hardcoded strings |

---

## 2. Files That Must Never Be Renamed or Deleted

These files are imported across the codebase. Changing them cascades into import errors:
- `backend/app/domain/inventory/engine.py`
- `backend/app/core/security.py`
- `backend/app/core/exceptions.py`
- `backend/app/db/session.py`
- `backend/app/dependencies/auth.py`
- `frontend/src/context/AuthContext.jsx`
- `frontend/src/services/apiClient.js`
- `frontend/src/hooks/useToast.jsx`
- `frontend/src/app/main.jsx`

---

## 3. Template System — Critical Understanding

### The Problem with the Current Code

`backend/app/services/documents.py → DocumentTemplateService._render()` currently uses:
```python
def _render(self, template: str, context: dict) -> str:
    normalized = SafeDict(str)
    for k, v in context.items(): normalized[k] = "" if v is None else str(v)
    return template.format_map(normalized)
```

This **only works with flat `{variable}` syntax**. It cannot handle:
- `{{ tenant.company_name }}` (dot notation — nested objects)
- `{% for item in items %}` (loops)
- `{% if tenant.phone %}` (conditionals)
- `{{ document_kind|lower }}` (filters)

### The Fix

Replace `_render()` entirely with Jinja2:
```python
import jinja2

def _render(self, template_str: str | None, context: dict) -> str:
    if not template_str:
        return ""
    try:
        return jinja2.Template(template_str).render(**context)
    except jinja2.TemplateError:
        return template_str  # return as-is on error rather than crash
```

Add to `requirements.txt`: `jinja2>=3.1.4`

### The Context Structure Must Match the Templates

The provided HTML templates use nested objects. The context builders must produce nested dicts:

**For invoice PDF and email (invoice.html, document_email.html):**
```python
context = {
    "tenant": {
        "company_name": "...",
        "contact_email": "...",
        "phone": "...",
        "address": "...",
        "logo_url": "...",         # from TenantSettings.document_logo_url
        "footer": "...",           # from TenantSettings.document_footer
        "currency": "USD",
    },
    "customer": {
        "name": "...",
        "email": "...",
        "phone": "...",
        "billing_address": "...",
    },
    "invoice": {
        "invoice_number": "INV-00001",
        "invoice_date": "2026-05-25",
        "due_date": "2026-06-25",      # or None
        "subtotal": "1000.00",
        "tax_amount": "180.00",
        "discount_amount": "0.00",
        "total_amount": "1180.00",
        "notes": None,
        # Email template extras:
        "title": "Invoice INV-00001",
        "intro": "Please find attached invoice INV-00001.",
        "document_kind": "Invoice",
        "document_number": "INV-00001",
        "sender_name": "<company_name>",
    },
    "sales_order": {"so_number": "SO-00001"},  # or None
    "items": [
        {
            "product_name": "Widget A",
            "warehouse_name": "Main WH",
            "quantity": "10",
            "unit_price": "100.00",
            "tax_rate": "18",
            "total_price": "1000.00",
        }
    ],
}
```

**For bill PDF and email (bill.html, document_email.html):**
```python
context = {
    "tenant": { ... },  # same as invoice
    "vendor": {
        "name": "...",
        "email": "...",
        "phone": "...",
        "address": "...",
    },
    "bill": {
        "bill_number": "BILL-00001",
        "bill_date": "2026-05-25",
        "due_date": "2026-06-25",
        "subtotal": "...",
        "tax_amount": "...",
        "total_amount": "...",
        "notes": None,
        # Email template extras:
        "title": "Bill BILL-00001",
        "intro": "Please find attached bill BILL-00001.",
        "document_kind": "Bill",
        "document_number": "BILL-00001",
        "sender_name": "<company_name>",
    },
    "purchase_order": {"po_number": "PO-00001"},  # or None
    "items": [
        {
            "product_name": "...",
            "warehouse_name": "...",
            "quantity_ordered": "10",    # NOTE: bill uses quantity_ordered (not quantity)
            "unit_price": "...",
            "tax_rate": "0",
            "total_price": "...",
        }
    ],
}
```

**For OTP email (otp_email.html):**
```python
context = {
    "code": "123456",
    "purpose": "email verification",    # used as {{ purpose|lower }}
    "ttl_minutes": 10,
}
```

**For document email (document_email.html, document_email.txt):**
The email templates use flat top-level variables (not nested). Pass these directly in the context:
```python
context = {
    "title": "Invoice INV-00001",
    "intro": "Please find attached your invoice.",
    "document_kind": "Invoice",          # used as {{ document_kind|lower }}
    "document_number": "INV-00001",
    "notes": None,
    "sender_name": "Company Name",
}
```

---

## 4. Provided Templates — Content

Store these exact HTML/text contents as the `body_template` and `body_template_text` of each `DocumentTemplate` record when seeding defaults. **Replace "Northstar Inventory" with "Warelyn Inventory"** in all email template HTML.

### `otp_email.html` → EMAIL_VERIFICATION `body_template`
HTML with: `{{ code }}`, `{{ purpose|lower }}`, `{{ ttl_minutes }}`

### `otp_email.txt` → EMAIL_VERIFICATION `body_template_text`
Plain text fallback with same variables.

### `document_email.html` → INVOICE_SEND and BILL_SEND `body_template`
HTML with: `{{ title }}`, `{{ intro }}`, `{{ document_kind|lower }}`, `{{ document_number }}`, `{% if notes %}{{ notes }}{% endif %}`, `{{ sender_name }}`

### `document_email.txt` → INVOICE_SEND and BILL_SEND `body_template_text`
Plain text fallback with same variables.

### `invoice.html` → PDF_INVOICE `body_template`
Full Jinja2 HTML with `{% for item in items %}`, nested object access.

### `bill.html` → PDF_BILL `body_template`
Full Jinja2 HTML with `{% for item in items %}`, nested object access.

---

## 5. Phase-by-Phase Build Instructions

### PHASE 15 — Jinja2 Engine + WeasyPrint PDF + HTML Templates

**Do these in this exact order:**

#### Step 1 — Add dependencies
`backend/requirements.txt`: add `jinja2>=3.1.4` and `weasyprint==62.3`

#### Step 2 — Add migration for `body_template_text`
Create `backend/alembic/versions/20260525_0013_document_template_text_column.py`:
```python
def upgrade():
    op.add_column('document_templates', sa.Column('body_template_text', sa.Text(), nullable=True))
def downgrade():
    op.drop_column('document_templates', 'body_template_text')
```

Add `body_template_text: Mapped[str | None] = mapped_column(Text, nullable=True)` to `DocumentTemplate` model.

#### Step 3 — Replace `pdf_service.py`
Write `render_html_to_pdf(html: str) -> bytes` using WeasyPrint.
Keep `build_simple_pdf()` as a legacy stub (call `render_html_to_pdf` with wrapped HTML).

#### Step 4 — Update `services/documents.py`
Four changes in one file:
1. Replace `_render()` with Jinja2 (shown above)
2. Replace `DEFAULT_TEMPLATES` entries with the provided HTML files (content in `docs/templates/`)
3. Restructure `_base_template_context()`, `_invoice_context()`, `_bill_context()` to nested object format (schema shown in §3 above)
4. Add `self._ensure_defaults(tenant_id)` as first line of `render_by_key()`
5. Update `render_invoice_pdf()` and `render_bill_pdf()` to call `render_html_to_pdf(rendered["body"])`
6. Update `_ensure_defaults()` to persist `body_template_text` field
7. Update `render_by_key()` return to include `"text"` key from `body_template_text`

#### Step 5 — Update `api/verification.py`
When calling `send_email()`, pass both `body_html` (rendered HTML) and `body_text` (rendered text from `rendered["text"]`).

#### Step 6 — Update `schemas/documents.py`
Add `body_template_text: str | None` to `DocumentTemplateRead` and `DocumentTemplateUpdate`.

#### Step 7 — Write tests
See §7 below for test list.

---

### PHASE 16 — Admin Layout + Super Admin UX

#### Step 1 — Create `AdminLayout.jsx`
`frontend/src/layouts/AdminLayout.jsx`:
- Deep navy left sidebar (bg-[#0F2460] or bg-slate-900) with:
  - Warelyn logo (white variant)
  - "PLATFORM ADMIN" badge (amber text, small caps)
  - Nav: Platform Console, Tenants, Audit Logs, Platform Health
  - No tenant nav items
  - Logout at bottom
- Top bar: dark navy with "Warelyn Platform Console" text + user chip
- No bell, no QuickCreate, no RecentHistory, no topbar search
- Registers global error handler via `setGlobalErrorHandler` (from Phase 17 — add placeholder if Phase 17 not yet done)
- `<Outlet />` as main content

#### Step 2 — Rewire routes in `AppRoutes.jsx`
Move all `/admin/*` routes out of `<MainLayout>` into `<AdminLayout>` with `requiredRole="SUPER_ADMIN"` check on `<ProtectedRoute>`.

#### Step 3 — Update `ProtectedRoute.jsx`
Add `requiredRole` prop. If set and `user.role !== requiredRole`, redirect to `/dashboard`.

#### Step 4 — Fix `NotificationRepository` naming
`repositories/notification.py`: rename class `NotificationService` → `NotificationRepository`
`api/notifications.py`: update import and all usages

---

### PHASE 17 — Settings Fix + Global Toast

#### Step 1 — Fix `SettingsPage.jsx`
Replace every `document.getElementById` with controlled React state:
```jsx
const [form, setForm] = useState(buildFormState(settings));
function handleChange(field) {
  return (e) => setForm(p => ({...p, [field]: e.target.type === 'checkbox' ? e.target.checked : e.target.value}));
}
async function handleSave() {
  const updated = await settingsService.updateTenantSettings(accessToken, form);
  setSettings(updated);
  toast.success('Settings saved successfully.');
}
```

#### Step 2 — Add global error handler to `apiClient.js`
```js
let _globalErrorHandler = null;
export function setGlobalErrorHandler(fn) { _globalErrorHandler = fn; }

// In apiRequest, after throwing the error:
if (_globalErrorHandler) {
  if (response.status === 401) {
    _globalErrorHandler('Session expired. Please log in again.', 'error');
  } else if (response.status === 403) {
    _globalErrorHandler('Access denied.', 'error');
  } else if (response.status >= 500) {
    _globalErrorHandler(errorMessage, 'error');
  }
}
```

#### Step 3 — Register handler in both layouts
In `MainLayout.jsx` AND `AdminLayout.jsx`:
```jsx
import { setGlobalErrorHandler } from '../services/apiClient.js';
const toast = useToast();
useEffect(() => {
  setGlobalErrorHandler((msg, type) => toast[type]?.(msg));
  return () => setGlobalErrorHandler(null);
}, [toast]);
```

#### Step 4 — Add template shortcut cards to `SettingsPage.jsx`
Add at the bottom: two Card links to `/settings/email-templates` and `/settings/pdf-templates`.

---

### PHASE 17A — Email Template Editor

**UI reference:** Screenshots 2 and 3 show a Zoho Books-style email notification template UI.

#### Frontend page: `EmailTemplatesPage.jsx`

**Layout:**
```
┌─────────────────────────────────────────────────────────┐
│ Email Templates                                         │
│ Sent when specific events occur in your workspace.      │
├──────────────────────┬──────────────────────────────────┤
│ NAME       │ DEFAULT │ SUBJECT AND CONTENT              │
│────────────┼─────────┼──────────────────────────────────│
│ Email      │ DEFAULT │ Verify your Warelyn email        │
│ Verific.   │         │ [Show Mail Content ▼]            │
│────────────┼─────────┼──────────────────────────────────│
│ Invoice    │ DEFAULT │ Invoice {{ document_number }} …  │
│ Email      │         │ [Show Mail Content ▼]            │
│────────────┼─────────┼──────────────────────────────────│
│ Bill Email │ DEFAULT │ Bill {{ document_number }} …     │
│            │         │ [Show Mail Content ▼]            │
└──────────────────────┴──────────────────────────────────┘
```

When user clicks a row (or "Edit" on the row), open a right-side slide-over or a modal:

**Editor modal** (matches Screenshot 3):
```
Template Name: [_______________________]
Subject*:      [{{ document_number }} from {{ sender_name }}]
               ┌──────────────────────────────────────────────────┐
               │ B I U S | 16px | Arial | ... [Insert Placeholder▾]│
               ├──────────────────────────────────────────────────┤
               │ <textarea with body content>                     │
               │                                                  │
               └──────────────────────────────────────────────────┘
[Preview] [Save] [Cancel]
```

**"Insert Placeholder" dropdown** — shows available variables for the selected template:
```
EMAIL_VERIFICATION:    {{ code }}, {{ purpose }}, {{ ttl_minutes }}
INVOICE_SEND:          {{ title }}, {{ intro }}, {{ document_kind }}, {{ document_number }}, {{ notes }}, {{ sender_name }}
BILL_SEND:             same as INVOICE_SEND
```

Clicking a placeholder inserts it at the textarea cursor position.

**Preview modal:**
- Calls `POST /templates/{id}/preview` with sample values
- Shows a two-tab modal: "HTML Preview" (iframe srcdoc) and "Text Preview" (pre tag)

#### Service functions (add to `documentService.js`):
```js
export function listTemplates(accessToken, channel) { ... }
export function getTemplate(accessToken, id) { ... }
export function updateTemplate(accessToken, id, payload) { ... }
export function previewTemplate(accessToken, id, variables) { ... }
```

#### Route + nav:
- Route: `settings/email-templates` → `<EmailTemplatesPage />`
- Nav item: under Settings, TENANT_ADMIN role only

---

### PHASE 17B — PDF Template Gallery + Editor

**UI reference:** Screenshot 1 shows a Zoho Books-style invoice template gallery with card thumbnails.

#### Frontend page: `PdfTemplatesPage.jsx`

**Gallery layout:**
```
┌──────────────────────────────────────────────────────────┐
│ PDF Templates                                    [+ New] │
├────────────────────┬───────────────────┬─────────────────┤
│  ┌──────────────┐  │  ┌─────────────┐  │  ┌───────────┐  │
│  │  [iframe     │  │  │  [iframe    │  │  │  New      │  │
│  │   preview    │  │  │   preview   │  │  │  Template │  │
│  │   @ 0.3x]    │  │  │   @ 0.3x]   │  │  │           │  │
│  └──────────────┘  │  └─────────────┘  │  │  + New    │  │
│  Invoice PDF       │  Bill PDF         │  └───────────┘  │
│  ⭐ DEFAULT        │  ⭐ DEFAULT        │                 │
└────────────────────┴───────────────────┴─────────────────┘
```

**`TemplateCard` component:**
```jsx
function TemplateCard({ template, onEdit }) {
  return (
    <div className="group relative cursor-pointer overflow-hidden rounded-xl border border-warelyn-border hover:shadow-lg transition">
      <div className="relative h-64 overflow-hidden bg-gray-50">
        <iframe
          srcDoc={template.body_template}
          title={template.name}
          className="absolute top-0 left-0 border-0 pointer-events-none"
          style={{
            width: '333%',
            height: '333%',
            transform: 'scale(0.3)',
            transformOrigin: 'top left',
          }}
        />
        <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition flex items-center justify-center">
          <Button
            className="opacity-0 group-hover:opacity-100 transition"
            variant="primary"
            onClick={() => onEdit(template)}
          >
            Edit Template
          </Button>
        </div>
      </div>
      <div className="p-3 flex items-center gap-2">
        <span className="text-sm font-semibold text-warelyn-text">{template.name}</span>
        <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-700">
          ⭐ DEFAULT
        </span>
      </div>
    </div>
  );
}
```

**Editor side panel (opens on "Edit Template" click):**
- Template name (input)
- HTML body textarea (large, `font-mono`, syntax hint comment at top)
- Jinja2 variable reference: collapsible section listing all available variables
- Live HTML preview: `<iframe srcdoc={renderedHtml}>` (re-renders on textarea change with 500ms debounce)
- "Download PDF Preview" button → calls `POST /templates/{id}/preview-pdf` → downloads blob
- "Save" and "Reset to Default" buttons

#### Backend: `POST /templates/{id}/preview-pdf`
See Phase Plan §17B.2 for full implementation.

#### Service function (add to `documentService.js`):
```js
export async function previewTemplatePdf(accessToken, id, variables = {}) {
  const res = await fetch(`${API_BASE_URL}/templates/${id}/preview-pdf`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${accessToken}` },
    body: JSON.stringify({ variables }),
  });
  if (!res.ok) throw new Error('PDF preview failed.');
  return res.blob();
}
```

---

### PHASE 17C — XLSX Import UI Fix

#### `CSVImportDropzone.jsx`
Change accept attribute: `.csv,.xlsx,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
Change label: "Upload CSV or XLSX file"
Change helper: "Supported: .csv and .xlsx (Excel). Max 10 MB."

#### `ProductImportPage.jsx`
- Page title: "Import Products — CSV or XLSX"
- Add template download row with two buttons: "Download CSV Template" and "Download XLSX Template"
- XLSX download: `GET /api/imports/products/template.xlsx`

#### `backend/app/api/imports.py`
Add XLSX template download endpoint. Use the existing hand-rolled XML writer in `imports.py` to produce a valid XLSX with correct headers row.

---

### PHASE 18 — Operational Completion

For each of these sub-features, follow the standard pattern: migration → model → repository → service → API → router registration → frontend page → tests.

- **Stock State Expansion:** 5 new columns on `warehouse_stock`. Update `InventoryEngine` methods.
- **Reorder Rules:** Full CRUD table. `ReorderRulesPage.jsx`.
- **Putaway Tasks:** New table + workflow. Wire to receipt commit. `PutawayTasksPage.jsx`.
- **Cycle Counts:** Session + lines tables. DRAFT → RECONCILED workflow. `CycleCountsPage.jsx`.
- **Expiry Job:** `backend/app/jobs/expire_batches.py`. Admin trigger endpoint.
- **Outbox Events:** `backend/app/events/outbox.py`. Foundation for async dispatch.

---

## 6. How to Do Common Tasks

### Adding a new backend model

1. Create/update the model in `backend/app/models/*.py`
2. Import + add to `__all__` in `backend/app/models/__init__.py`
3. Create migration: `cd backend && .venv/bin/alembic revision --autogenerate -m "description"`
4. Review generated file — verify column types, nullable, indexes
5. Run: `.venv/bin/alembic upgrade head`
6. Write tests before service logic

### Adding a new API endpoint

1. Add route to appropriate `backend/app/api/*.py`
2. Always add: `context: UserContext = Depends(require_roles(*roles))` or `require_super_admin()`
3. Always add: `db: Session = Depends(get_db)`
4. Always delegate to service: `return SomeService(db).method(...)`
5. Add Pydantic schema in `backend/app/schemas/*.py`
6. If new router file: include in `backend/app/api/router.py`

### Adding a new frontend page

1. Create `frontend/src/pages/NewPage.jsx` as named export
2. Import in `AppRoutes.jsx`
3. Add `<Route path="..." element={<NewPage />} />`
4. If it belongs in sidebar: add to `navigation.js`
5. All state: `useState`. All API calls: `useEffect`. Always show `LoadingState` and `ErrorState`.

### Writing tests

Use `conftest.py` fixtures: `db`, `client`, `super_admin_token`, `tenant_token`.
```python
def test_something(client, tenant_token):
    response = client.get("/api/path", headers={"Authorization": f"Bearer {tenant_token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["field"] == expected
```

---

## 7. Test Requirements Per Phase

### Phase 15 (target: 91 → 108, +17 tests)
- `test_invoice_pdf_endpoint_returns_pdf_content_type`
- `test_bill_pdf_endpoint_returns_pdf_bytes_with_length`
- `test_render_invoice_html_contains_invoice_number`
- `test_render_bill_html_contains_bill_number`
- `test_render_invoice_jinja2_for_loop_produces_items`
- `test_render_email_verification_uses_jinja2_code_variable`
- `test_email_verification_send_on_fresh_tenant_does_not_404`
- `test_template_auto_seed_on_render_by_key`
- `test_body_template_text_is_stored_in_db`
- `test_invoice_send_email_uses_html_template`
- `test_invoice_mark_paid_status_transition`
- `test_invoice_void_status_transition`
- `test_bill_mark_paid_status_transition`
- `test_bill_pdf_endpoint_returns_valid_pdf_bytes`
- `test_template_update_persists_to_db`
- `test_template_preview_renders_with_provided_variables`
- `test_jinja2_filter_lower_works_in_document_kind`

### Phase 16 (+8 tests)
- `test_admin_route_requires_super_admin_role`
- `test_tenant_user_cannot_access_admin_dashboard`
- `test_super_admin_can_access_admin_dashboard`
- `test_notification_repository_list_returns_for_user`
- `test_notification_repository_unread_count`
- `test_notification_mark_read`
- `test_notification_mark_all_read`
- `test_tenant_list_is_accessible_to_super_admin`

### Phase 17 (+6 tests)
- `test_settings_update_saves_all_fields`
- `test_user_preferences_update_saves_theme`
- `test_401_is_returned_for_expired_token`
- `test_403_is_returned_for_wrong_role`
- `test_settings_get_returns_defaults_for_new_tenant`
- `test_preferences_get_returns_defaults_for_new_user`

### Phase 17A (+8 tests)
- `test_list_email_templates_returns_only_email_channel`
- `test_get_template_returns_correct_template`
- `test_update_template_subject_persists`
- `test_update_template_body_persists`
- `test_preview_template_renders_variables`
- `test_preview_template_with_missing_variable_does_not_crash`
- `test_template_required_admin_role`
- `test_list_templates_auto_seeds_defaults`

### Phase 17B (+6 tests)
- `test_list_pdf_templates_returns_only_pdf_channel`
- `test_preview_pdf_template_returns_pdf_bytes`
- `test_preview_pdf_template_uses_sample_data_for_missing_vars`
- `test_preview_pdf_template_with_custom_html`
- `test_invoice_pdf_uses_stored_html_template`
- `test_bill_pdf_uses_stored_html_template`

### Phase 17C (+4 tests)
- `test_xlsx_template_download_returns_valid_xlsx`
- `test_xlsx_template_has_correct_headers_row`
- `test_import_endpoint_accepts_xlsx_file`
- `test_import_xlsx_produces_same_rows_as_csv`

---

## 8. Validation Before Declaring a Phase Complete

Run all of these before saying a phase is done:

```bash
# All tests must pass
cd backend && .venv/bin/python -m pytest -q

# No syntax errors
cd backend && .venv/bin/python -m compileall app

# Migrations are clean
cd backend && .venv/bin/alembic check
```

And verify manually:
- [ ] All new endpoints have role checks
- [ ] All new migrations run clean with `alembic upgrade head`
- [ ] All new frontend pages are imported in `AppRoutes.jsx`
- [ ] No `document.getElementById` in any React file
- [ ] No `str.format_map` or f-string template rendering — only Jinja2
- [ ] No direct stock mutations outside `engine.py`
- [ ] Toast error handling on all frontend mutation operations
- [ ] `LoadingState` and `ErrorState` shown in all data-fetching pages

---

## 9. Design System Reference

### Tailwind Tokens
```
text-warelyn-primary / bg-warelyn-primary  →  #1E3A8A
text-warelyn-accent  / bg-warelyn-accent   →  #10B981
text-warelyn-muted                         →  #64748B
text-warelyn-danger                        →  #EF4444
text-warelyn-warning                       →  #F59E0B
border-warelyn-border                      →  #E2E8F0
bg-warelyn-surface                         →  #FFFFFF
bg-warelyn-bg                              →  #F8FAFC
```

### Existing UI Components (always use these, never reinvent)
`Button`, `Card/CardBody/CardHeader`, `Input`, `Badge/StatusBadge`, `LoadingState`, `ErrorState`, `EmptyState`, `TableShell`, `ScreenToolbar`, `PageHeader`, `RecordDetailShell`, `ConfirmationModal`, `WorkflowProgress`

### Icons
`lucide-react` — import individual icons: `import { Download, Mail, Receipt } from 'lucide-react'`

---

## 10. API Error Format

Backend errors always use this format (from `app/core/exceptions.py`):
```json
{ "error": { "code": "SNAKE_CASE_CODE", "message": "Human-readable message" } }
```

Frontend `apiClient.js` extracts: `payload?.error?.message ?? 'API request failed.'`

---

## 11. Phase Order and Test Targets

```
Phase 15  → Jinja2 engine + WeasyPrint PDF + HTML templates     → 108 tests
Phase 16  → Admin Layout + role guards + notification rename     → 116 tests
Phase 17  → Settings controlled state + global toast            → 122 tests
Phase 17A → Email Template Editor (list + WYSIWYG + placeholder) → 130 tests
Phase 17B → PDF Template Gallery + Editor + preview endpoint    → 136 tests
Phase 17C → XLSX import UI fix + template download              → 140 tests
Phase 18  → Stock states, reorder, putaway, cycle counts, jobs  → 170 tests
```

Each phase must hit its test target before moving to the next phase.

---

*Generated from full codebase audit + provided HTML templates + screenshot reference — 2026-05-25 Rev 2.*
*Do not modify unless you have re-audited the codebase and re-reviewed the template files.*
