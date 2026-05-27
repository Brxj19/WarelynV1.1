# Warelyn Next-Phase Engineering Plan for Claude Opus

**Repository scanned:** `Warelyn-main` from uploaded zip `Warelyn-main (2).zip`  
**Generated for:** next execution pass by Claude Opus / coding agent  
**Primary goal:** make Warelyn production-grade for dashboard analytics, selected invoice/bill templates, role-based notifications, verification UX, backend wiring, UI correctness, and CI reliability.

---

## 0. Ready-to-paste Claude Opus prompt

```text
You are working inside the Warelyn repository. Read this file completely before editing. Do not rewrite the app from scratch. Work phase-by-phase and keep changes small, testable, and reversible.

Primary objectives:
1. Add real dashboard charts and analytics insights backed by deterministic backend data, not random/simulated metrics.
2. Fix invoice/bill PDF download so it always uses the user-selected template for the correct document type only.
3. Implement full end-to-end role-based notifications: event generation, recipient targeting, all/unread filters, mark one read, mark all read, clear one, clear all, and bell badge correctness.
4. Wire every UI action to a real backend path or remove/disable the UI if the backend feature is intentionally not available yet.
5. Harden email and phone verification: no re-verify button after verified, no OTP leaks in production, clear explanation of where OTP is sent, and a real/replaceable SMS provider abstraction.
6. Fix small UI correctness issues, route issues, loading/error states, and CI/test pipeline problems.

Execution rules:
- First inspect the referenced files and verify each finding before changing it.
- Preserve tenant isolation. Never trust tenant_id from the frontend when it can be derived from auth context.
- Preserve role checks. Super admin screens must not be visible through tenant layouts.
- Preserve inventory integrity. Stock mutations must go through the existing inventory engine/domain layer.
- Add or update tests for every backend behavior change and run the targeted commands listed in this file.
- After each phase, report files changed, tests run, and remaining risks.
```

---

## 1. Baseline scan results

### 1.1 Local validation performed

From repository root after extracting the uploaded zip:

```bash
cd /mnt/data/warelyn_scan/Warelyn-main/frontend
npm install --silent
npm run build
```

Result:

- Frontend build **passed**.
- Vite warned that the main JS chunk is large: `dist/assets/index-D3bpQC9y.js` is about `618.53 kB`, above the `500 kB` warning limit.
- This is not a functional failure, but it is a performance warning. Add route-level lazy imports/code splitting later.

Backend validation:

```bash
cd /mnt/data/warelyn_scan/Warelyn-main/backend
python3 -m venv .venv
. .venv/bin/activate
pip install -q -r requirements.txt
python -m compileall app
pytest -q
```

Result:

- `python -m compileall app` **passed**.
- `pytest -q` failed locally without `PYTHONPATH=.` because tests import `app.*` directly.
- `PYTHONPATH=. pytest -q` collected/runs tests but the full suite timed out after 300 seconds in this environment.
- Targeted suites passed:

```bash
PYTHONPATH=. pytest -q tests/test_documents.py
# 21 passed

PYTHONPATH=. pytest -q tests/test_notifications.py tests/test_verification.py
# 15 passed

PYTHONPATH=. pytest -q tests/test_reports.py tests/test_settings.py
# 16 passed
```

### 1.2 Immediate pipeline risk

`.github/workflows/ci.yml` currently runs backend tests as:

```yaml
working-directory: backend
run: python -m pytest
```

Because local execution needed `PYTHONPATH=.`, CI may fail depending on import path behavior. Also, `scripts/validate.sh` runs:

```bash
.venv/bin/python -m pytest
```

without setting `PYTHONPATH`.

**Fix:** make imports reliable by adding one of these:

1. Preferred: package backend properly with `pyproject.toml`/editable install and use `pip install -e .`; or
2. Minimal: set `PYTHONPATH: .` in the CI backend job and set `PYTHONPATH=. .venv/bin/python -m pytest` in `scripts/validate.sh`.

---

## 2. Critical bug matrix

| Area | Severity | Evidence | Required fix |
|---|---:|---|---|
| Dashboard analytics | High | `backend/app/services/reports.py` lines 291-308 generate `previous_kpis` using random variance. | Replace simulated previous-period metrics with real historical period queries or snapshots. Never show fake trends. |
| Dashboard charts | High | `frontend/src/pages/DashboardPage.jsx` has KPI cards/lists only; `package.json` has no charting dependency. | Add real chart datasets in backend and chart components in frontend. |
| Invoice/bill selected template | High | `DocumentsService.render_invoice_pdf`/`render_bill_pdf` read preferred IDs, but `DocumentTemplateService.render_by_key` does not validate that a preferred template belongs to the requested key/channel. | Enforce selected template purpose: invoice PDF cannot render bill PDF template; bill email cannot render invoice email template. Add tests. |
| Notification tenant scoping | High | `backend/app/repositories/notification.py` `list_for_user`, `unread_count`, `mark_all_read` filter only by user_id, not tenant_id. | Scope notification reads/counts/updates by tenant_id. Exclude cleared/deleted rows. |
| Notification feature gaps | High | Backend supports list, unread count, mark one read, mark all read only. No clear all/clear one, no role/event recipient system. | Add notification service/event bus, role-based dispatch, clear/archive endpoints, frontend tabs/actions. |
| Verification re-verify UX | High | `frontend/src/pages/SettingsPage.jsx` lines 373-375 and 393-395 show `Re-verify` even when already verified. | Hide verification action after verified or show disabled `Verified` button. |
| Phone OTP destination | High | `send_phone_verification` uses `SMSDevOutboxService`; no production SMS provider abstraction. Frontend says sent to phone but in dev it only appears via dev code/outbox. | Add provider abstraction and UI copy: production = SMS to phone; local dev = outbox/dev code only. |
| OTP leak risk | High | `backend/app/api/verification.py` returns `development_code` from email and phone send endpoints. | Return OTP only in dev/test mode behind config flag. Never in production. |
| Phone verification persistence | Medium/High | `send_phone_verification` creates OTP/outbox but has no explicit `db.commit()`. `get_db()` only closes session, no automatic commit. | Add explicit commit after OTP/outbox creation and tests verifying persistence across sessions. |
| Super admin route ambiguity | High | `frontend/src/routes/AppRoutes.jsx` includes `/admin` routes inside generic tenant `ProtectedRoute` and again inside `ProtectedRoute requiredRole="SUPER_ADMIN"`. | Remove admin routes from tenant `MainLayout`; keep only under `AdminLayout` + super-admin guard. |
| Broken settings landing paths | Medium | `frontend/src/pages/SettingsPage.jsx` uses `/sales/orders` and `/purchasing/orders`; actual routes are `/sales` and `/purchases`. | Fix options and add route existence guard/test. |
| Login preference application | Medium | `AuthContext.login` sets user/token but does not call `applyPreferences`; preferences only load on mount/loadMe. | Apply preferences immediately after login or call `loadMe(data.access_token)`. |
| Nonexistent frontend service call | Medium | `frontend/src/services/documentService.js` has `getTemplate(accessToken, id)` calling `GET /document-templates/{id}`, but backend only has list/patch/preview/preview-pdf. | Add backend GET endpoint or remove unused function. Prefer adding GET for editor/detail consistency. |
| Bundle size | Low/Medium | Vite build warns main chunk >500kB. | Lazy-load routes, heavy pages, and admin/report modules. |

---

## 3. Non-negotiable engineering rules

1. **No fake analytics.** If a metric cannot be computed accurately, return `null` and show “Not enough data yet.” Do not randomize.
2. **Tenant isolation everywhere.** All notification, template, invoice, bill, report, and verification queries must be tenant-scoped unless the user is super admin and the endpoint is explicitly platform-level.
3. **Role checks must be backend enforced.** Frontend route hiding is UX only, not security.
4. **Selected templates must be type-safe.** Invoice PDF template IDs must match PDF invoice template keys. Bill PDF template IDs must match PDF bill template keys. Email templates must match their purpose.
5. **No OTP in production responses.** `development_code` is allowed only in local/test mode behind a named setting.
6. **Every clickable UI action must either work or be disabled with a clear reason.** No silent no-ops.
7. **Each phase must include tests.** Backend tests for business logic, frontend build, and at least smoke-level UI verification.

---

## 4. Phase 0 — Stabilize validation and baseline checks

### Problem

The code compiles and targeted tests pass, but the default backend test command is fragile because `pytest` cannot import `app` unless `PYTHONPATH=.` is present locally. The full test suite also timed out during local scan.

### Target files

- `.github/workflows/ci.yml`
- `scripts/validate.sh`
- `backend/pyproject.toml` or new packaging file if choosing editable install
- `backend/tests/conftest.py`

### Tasks

1. Make backend imports deterministic.
   - Preferred: add backend packaging and install editable in CI.
   - Minimal: set `PYTHONPATH=.` for all pytest/alembic commands.
2. Add a timeout or split backend tests by suite in CI if full suite stays slow.
3. Investigate global full-suite slowdown:
   - Run `PYTHONPATH=. pytest -vv --durations=25`.
   - Check whether tests leave DB sessions, background tasks, or long fixtures open.
   - Compare standalone passing suite vs full-suite behavior.
4. Update `scripts/validate.sh` to fail fast with clear sections:

```bash
cd backend
python3 -m compileall app
PYTHONPATH=. .venv/bin/python -m pytest -q
PYTHONPATH=. .venv/bin/alembic upgrade head

cd ../frontend
npm run build

cd ..
docker compose config >/dev/null
git status --short
```

### Acceptance criteria

- `scripts/validate.sh` works from repo root on a fresh clone.
- CI backend job does not depend on implicit import path behavior.
- Full backend test run either completes or is intentionally split into reliable jobs.

---

## 5. Phase 1 — Real dashboard charts and analytics insights

### Current state

`frontend/src/pages/DashboardPage.jsx` currently displays KPI cards, pending actions, reconciliation, recent stock movements, low-stock items, and expiring batches. It loads:

```jsx
reportsService.getOperationalDashboard(accessToken, { compare_previous: true })
purchasingService.listPurchaseOrders(accessToken)
salesService.listSalesOrders(accessToken)
fulfillmentService.listPickTasks(accessToken)
returnsService.listSalesReturns(accessToken)
```

This creates mixed responsibility: some dashboard numbers come from the dashboard endpoint and some are derived client-side from separate list endpoints.

Backend `backend/app/services/reports.py` has:

```python
if compare_previous:
    # Generate simulated previous period KPIs based on current values with slight variance
    import random
    random.seed(tenant_id)
    ...
```

This is not acceptable for a business dashboard because it shows fake trend information.

### Required backend design

Add deterministic chart/insight support to `OperationalDashboard`.

Recommended response shape:

```json
{
  "period": {
    "key": "30d",
    "start_date": "2026-04-25",
    "end_date": "2026-05-25",
    "previous_start_date": "2026-03-26",
    "previous_end_date": "2026-04-24"
  },
  "kpis": {},
  "previous_kpis": {},
  "charts": {
    "stock_value_trend": [{ "date": "2026-05-01", "value": 12345.50 }],
    "stock_movements_by_day": [{ "date": "2026-05-01", "in": 10, "out": 5, "adjustment": 1 }],
    "order_funnel": [{ "stage": "Draft", "count": 4 }, { "stage": "Confirmed", "count": 7 }],
    "purchase_vs_sales": [{ "date": "2026-05-01", "purchase_qty": 12, "sales_qty": 9 }],
    "low_stock_by_warehouse": [{ "warehouse_name": "Main", "count": 3 }],
    "returns_qc_status": [{ "status": "INSPECTION_PENDING", "count": 2 }]
  },
  "insights": [
    {
      "severity": "warning",
      "title": "5 products are below reorder level",
      "message": "Open the low-stock report and generate reorder suggestions.",
      "action_label": "View low stock",
      "action_url": "/reports/low-stock"
    }
  ]
}
```

### Backend files to update

- `backend/app/api/reports.py`
- `backend/app/services/reports.py`
- `backend/app/schemas/reports.py`
- `backend/app/repositories/reports.py` or equivalent report repository
- `backend/tests/test_reports.py`

### Backend implementation notes

1. Add query params to dashboard endpoint:
   - `period`: `7d | 30d | 90d | custom`
   - `date_from`, `date_to` for custom range
   - optional `warehouse_id`
   - `compare_previous: bool`
2. Compute previous period using the same length as the selected period.
3. Use actual data from:
   - inventory ledger / stock movements
   - purchase orders and receipts
   - sales orders and fulfillments
   - returns and blocked stock
   - batch expiry and low-stock reports
4. If there is no previous-period data, return `previous_kpis: null` or fields as `null`; frontend should show “No previous period data.”
5. Do not query all rows and filter in Python for large datasets if SQL aggregation is possible. Use grouped SQL queries for time buckets.
6. Add indexes/migrations if needed for date-based chart queries.

### Frontend files to update

- `frontend/src/pages/DashboardPage.jsx`
- `frontend/src/services/reportsService.js`
- `frontend/src/components/ui/*` for chart cards if needed
- `frontend/package.json` if adding a chart library

### Frontend implementation notes

1. Add dashboard filters:
   - period dropdown: 7 days, 30 days, 90 days
   - optional warehouse filter if warehouse list is already available
2. Add chart cards:
   - Stock value trend
   - Stock movements by day
   - Purchase vs sales volume
   - Order funnel/status breakdown
   - Returns QC status
   - Low-stock by warehouse/category
3. Add analytics insight cards with action links.
4. Handle empty datasets gracefully with `EmptyState`.
5. Keep dashboard performance good: the dashboard should preferably use one backend endpoint rather than 5 separate list endpoints.

### Tests

Backend:

```bash
cd backend
PYTHONPATH=. pytest -q tests/test_reports.py
```

Add tests for:

- no fake/random previous KPI values
- previous-period values computed from seeded historical data
- chart datasets respect tenant_id
- chart datasets respect date range and warehouse filter
- empty data returns valid empty arrays, not 500

Frontend:

```bash
cd frontend
npm run build
```

Optional but recommended:

- Add component tests for dashboard empty/loading/error states.
- Add a mocked service test verifying chart rendering with API payload.

### Acceptance criteria

- No random or simulated analytics remain.
- Dashboard shows charts and insights based on backend data.
- Dashboard still works for a fresh tenant with no data.
- Tenant A never sees Tenant B dashboard values.

---

## 6. Phase 2 — Fix invoice/bill PDF download to always use selected template

### Current state

Frontend downloads:

```js
// frontend/src/services/documentService.js
export function downloadInvoicePdf(accessToken, id) {
  return downloadPath(`/invoices/${id}/pdf`, accessToken);
}

export function downloadBillPdf(accessToken, id) {
  return downloadPath(`/bills/${id}/pdf`, accessToken);
}
```

Backend PDF download uses the current actor ID:

```python
pdf = DocumentsService(db).render_invoice_pdf(context.tenant_id, invoice_id, context.user.id)
pdf = DocumentsService(db).render_bill_pdf(context.tenant_id, bill_id, context.user.id)
```

`DocumentsService.render_invoice_pdf` and `render_bill_pdf` read user preferences:

```python
preferred_id = self._get_user_preferred_template(actor_user_id, "preferred_invoice_template_id")
return self.template_service.render_by_key(tenant_id, "PDF", "PDF_INVOICE", context, preferred_id)
```

But `DocumentTemplateService.render_by_key` accepts a `preferred_template_id` without enforcing that the selected template belongs to the requested key family/channel. This can lead to wrong templates being used if a bad ID is saved or manually injected.

### Target files

- `backend/app/services/documents.py`
- `backend/app/api/documents.py`
- `backend/app/schemas/documents.py`
- `backend/app/services/settings.py`
- `backend/tests/test_documents.py`
- `backend/tests/test_settings.py`
- `frontend/src/pages/SettingsPage.jsx`
- `frontend/src/services/documentService.js`
- `frontend/src/pages/DocumentsPages.jsx`

### Required backend fixes

1. Add strict template-purpose validation.

Recommended helper:

```python
def _validate_preferred_template(template, expected_channel: str, expected_template_key_prefix: str) -> None:
    if template.channel != expected_channel:
        raise AppError("INVALID_TEMPLATE_PURPOSE", "Selected template is not valid for this document type.", 400)
    if not template.template_key.startswith(expected_template_key_prefix):
        raise AppError("INVALID_TEMPLATE_PURPOSE", "Selected template is not valid for this document type.", 400)
    if not template.is_active:
        raise AppError("TEMPLATE_INACTIVE", "Selected template is inactive.", 400)
```

2. Apply this in two places:
   - when saving user preferences in settings
   - when rendering a PDF/email as a defensive backend check
3. Add backend `GET /document-templates/{template_id}` or remove the frontend `getTemplate` function. Prefer adding the endpoint because editor/detail flows often need it.
4. Add debug-safe response headers for generated PDF to verify selected template in tests/manual QA:
   - `X-Warelyn-Template-Id`
   - `X-Warelyn-Template-Key`
   - Only if safe; do not expose sensitive template content.
5. Decide whether `invoice.pdf_bytes`/`bill.pdf_bytes` should be used.
   - Current rendering appears dynamic and not cached.
   - Either remove dead cache assumptions or implement generated PDF caching with invalidation when templates/preferences/doc fields change.

### Required frontend fixes

1. In Settings, keep filtering templates by exact purpose:

```js
const invoicePdfTemplates = pdfTemplates.filter((t) => t.template_key?.startsWith('PDF_INVOICE'));
const billPdfTemplates = pdfTemplates.filter((t) => t.template_key?.startsWith('PDF_BILL'));
```

2. Add a “Preview selected template” action near each selected template.
3. After saving preferences, show clear confirmation: “Invoice PDF template saved.”
4. In invoice/bill detail pages, when the user clicks Download PDF:
   - show loading state
   - catch errors and toast them
   - do not silently download if backend rejects template purpose
5. Consider showing the active selected template name near download buttons.

### Tests

Add backend tests:

1. User selected invoice PDF template is used for invoice downloads.
2. User selected bill PDF template is used for bill downloads.
3. Invoice PDF download rejects a bill PDF template ID if injected into preferences.
4. Bill PDF download rejects an invoice PDF template ID if injected into preferences.
5. Inactive selected template fails clearly or falls back only if that is the desired product decision. Prefer failing clearly.
6. Tenant A cannot use Tenant B template ID.
7. `GET /document-templates/{id}` returns only tenant-owned templates.

Run:

```bash
cd backend
PYTHONPATH=. pytest -q tests/test_documents.py tests/test_settings.py
cd ../frontend
npm run build
```

### Acceptance criteria

- Downloaded invoice PDF always uses selected invoice PDF template.
- Downloaded bill PDF always uses selected bill PDF template.
- Cross-purpose or cross-tenant template IDs cannot be used.
- UI makes the selected template visible and testable.

---

## 7. Phase 3 — Full role-based notification system

### Current state

Backend API supports only:

- `GET /notifications`
- `GET /notifications/unread-count`
- `POST /notifications/{notification_id}/read`
- `POST /notifications/read-all`

Frontend bell supports:

- list notifications
- unread badge
- mark one read
- mark all read
- 30 second polling

Missing:

- role-based notification dispatch
- clear/delete/archive one notification
- clear all
- all/unread/cleared filtering
- event-driven creation across inventory/purchase/sales/returns/documents/imports
- tenant-scoped counts/updates
- honoring user notification preferences
- action links/deep links
- priority/severity and category filters

### Existing risks

`backend/app/repositories/notification.py` currently filters by user only:

```python
select(Notification).where(Notification.user_id == user_id)
```

`tenant_id` is accepted as a parameter but ignored in `list_for_user`. `unread_count` and `mark_all_read` also ignore tenant_id.

### Target files

Backend:

- `backend/app/models/communication.py`
- new migration in `backend/alembic/versions/*`
- `backend/app/schemas/communication.py`
- `backend/app/repositories/notification.py`
- `backend/app/api/notifications.py`
- new `backend/app/services/notifications.py`
- event insertion points in:
  - `backend/app/services/documents.py`
  - `backend/app/services/purchasing.py`
  - `backend/app/services/sales.py`
  - `backend/app/services/fulfillment.py`
  - `backend/app/services/imports.py`
  - inventory/report/reorder services where low-stock and reorder events are produced
- `backend/tests/test_notifications.py`

Frontend:

- `frontend/src/components/NotificationCenter.jsx`
- `frontend/src/services/notificationService.js`
- `frontend/src/pages/SettingsPage.jsx`
- topbar/layout components where bell is used

### Database/model changes

Add fields to `Notification`:

```python
priority: str | None                  # LOW, NORMAL, HIGH, URGENT
action_url: str | None                # frontend deep link
audience_role: str | None             # optional role that caused targeting
cleared_at: datetime | None           # user cleared it from active list
delivered_at: datetime | None         # optional future email/in-app delivery tracking
```

Optional but useful:

```python
dedupe_key: str | None                # avoid duplicate spam for same event
metadata_json: JSON | None            # compact extra data
```

Add indexes:

- `(tenant_id, user_id, is_read, cleared_at, created_at)`
- `(tenant_id, category, created_at)`
- optional unique `(tenant_id, user_id, dedupe_key)` if deduping is required

### Backend API additions

Add/modify endpoints:

```http
GET /notifications?status=all|unread|read|cleared&category=&limit=&offset=
GET /notifications/unread-count
POST /notifications/{id}/read
POST /notifications/{id}/unread
POST /notifications/read-all
POST /notifications/{id}/clear
POST /notifications/clear-all
```

Response for count should exclude cleared notifications:

```json
{ "count": 0 }
```

For `read-all` and `clear-all`, return updated count:

```json
{ "success": true, "unread_count": 0 }
```

### Notification service design

Create `backend/app/services/notifications.py` with methods like:

```python
class NotificationService:
    def notify_user(...): ...
    def notify_roles(tenant_id, roles, title, message, category, type="INFO", entity_type=None, entity_id=None, action_url=None, dedupe_key=None): ...
    def notify_tenant_admins(...): ...
```

Recipient selection:

- Fetch active users for tenant with matching roles.
- Respect `UserPreferences.notification_in_app_enabled` for in-app notification creation.
- If `notification_email_enabled` is true and the event should email, enqueue email/send via template later.
- Do not notify inactive users.
- Do not notify users from other tenants.

### Event trigger map

Implement the first pass using service-layer calls after successful commit or before commit inside the same transaction where safe.

| Event | Recipients | Category | Type | Action URL |
|---|---|---|---|---|
| Low stock detected/new reorder suggestion | `TENANT_ADMIN`, `INVENTORY_MANAGER`, maybe `PURCHASE_STAFF` | INVENTORY | WARNING | `/reports/low-stock` or `/reports/reorder-suggestions` |
| Purchase order submitted | `TENANT_ADMIN`, `PURCHASE_STAFF`, `INVENTORY_MANAGER` | PURCHASE | INFO | `/purchases/{id}` |
| Purchase receipt committed | `TENANT_ADMIN`, `INVENTORY_MANAGER`, `PURCHASE_STAFF` | PURCHASE | SUCCESS | `/purchase-receipts/{id}` |
| Sales order confirmed | `TENANT_ADMIN`, `SALES_STAFF`, `INVENTORY_MANAGER` | SALES | INFO | `/sales/{id}` |
| Pick task created/assigned | `INVENTORY_MANAGER`, relevant staff if assignment exists | INVENTORY | INFO | `/pick-tasks/{id}` |
| Fulfillment committed | `TENANT_ADMIN`, `SALES_STAFF`, `INVENTORY_MANAGER` | SALES | SUCCESS | `/sales-fulfillments/{id}` |
| Sales return submitted | `TENANT_ADMIN`, `SALES_STAFF` | RETURNS | INFO | `/returns/{id}` |
| Return QC pending | `INVENTORY_MANAGER` | RETURNS | WARNING | `/returns/{id}/inspect` |
| Return processed | `TENANT_ADMIN`, `SALES_STAFF`, `INVENTORY_MANAGER` | RETURNS | SUCCESS | `/returns/{id}` |
| Invoice sent/paid/voided | `TENANT_ADMIN`, `SALES_STAFF` | SALES | INFO/SUCCESS/WARNING | `/invoices/{id}` |
| Bill sent/paid/voided | `TENANT_ADMIN`, `PURCHASE_STAFF` | PURCHASE | INFO/SUCCESS/WARNING | `/bills/{id}` |
| Product import validation failed | actor + `TENANT_ADMIN` | SYSTEM | ERROR | `/catalog/products/import` |
| Email verified | actor only | VERIFICATION | SUCCESS | `/settings` |
| Phone verified | actor only | VERIFICATION | SUCCESS | `/settings` |

### Frontend notification UX

Update `NotificationCenter.jsx`:

1. Add tabs:
   - All
   - Unread
   - Cleared, optional hidden behind “History”
2. Add actions:
   - Mark one read
   - Mark all read
   - Clear one
   - Clear all
3. Bell badge rules:
   - show badge only when `unread_count > 0`
   - after mark one read, optimistically decrement if the item was unread
   - after mark all read, immediately set count to 0
   - after clear unread item, decrement count
   - after clear all, set count to 0 and remove active list items
4. Add action navigation:
   - if `notification.action_url`, clicking the notification navigates there
   - mark as read on click before navigation
5. Add robust loading/error states inside popover.
6. Do not poll when `accessToken` is missing.

### Tests

Backend tests to add/update:

```bash
cd backend
PYTHONPATH=. pytest -q tests/test_notifications.py
```

Test cases:

1. Tenant-scoped listing excludes notifications from other tenants.
2. `unread-count` excludes read and cleared notifications.
3. Mark one read sets `is_read=True` and `read_at`.
4. Mark all read only affects current tenant/current user.
5. Clear one sets `cleared_at` and removes it from default active list.
6. Clear all clears current user's active notifications only.
7. Role dispatch creates notifications for the expected roles only.
8. User preference `notification_in_app_enabled=False` prevents in-app notification creation.
9. Inactive users are not notified.
10. Event trigger creates expected notification after invoice/bill/order/return actions.

Frontend:

```bash
cd frontend
npm run build
```

Optional component tests:

- badge disappears after mark all read
- clear all empties active list
- unread tab filters correctly

### Acceptance criteria

- Notifications are generated by real backend events.
- Notifications are role-based.
- Bell badge disappears immediately when all notifications are read/cleared.
- Clear all and clear individual work.
- No cross-tenant notification leakage.

---

## 8. Phase 4 — Email and phone verification hardening

### Current state

Backend:

- Email verification sends through email service and returns a `development_code`.
- Phone verification uses `SMSDevOutboxService` and returns a `development_code`.
- Verification status exists.
- Confirmation sets `email_verified_at` or `phone_verified_at`.

Frontend:

- Settings shows `Re-verify` even after verified.
- Verify pages do not first check whether the value is already verified.
- Verify pages show `development_code` if backend returns it.

### Target files

Backend:

- `backend/app/api/verification.py`
- `backend/app/services/verification.py`
- `backend/app/services/sms.py`
- `backend/app/core/config.py`
- `backend/app/models/communication.py`
- `backend/tests/test_verification.py`

Frontend:

- `frontend/src/pages/SettingsPage.jsx`
- `frontend/src/pages/VerifyEmailPage.jsx`
- `frontend/src/pages/VerifyPhonePage.jsx`
- `frontend/src/services/verificationService.js`

### Backend tasks

1. Add already-verified guards:

```python
if context.user.email_verified_at:
    return {
        "success": True,
        "already_verified": True,
        "message": "Email is already verified."
    }
```

Same for phone.

2. Add explicit commit in phone send flow.

Current `get_db()` only closes the session; it does not auto-commit. Make `send_phone_verification` commit after OTP/outbox creation.

3. Hide `development_code` by environment.

Add config setting:

```python
expose_dev_otp: bool = False
environment: str = "development"
```

Return development code only when:

```python
settings.environment in {"development", "test"} and settings.expose_dev_otp
```

4. Add SMS provider abstraction.

Recommended interface:

```python
class SMSProvider:
    def send_verification_code(self, phone: str, message: str) -> SMSProviderResult: ...
```

Implement:

- `DevOutboxSMSProvider`: stores in `sms_outbox`
- placeholder `TwilioSMSProvider`/`MSG91SMSProvider` behind environment variables

5. Add resend cooldown and attempt limits if not already strong enough:
   - Do not allow unlimited resend spam.
   - Return structured error `OTP_RESEND_COOLDOWN`.

6. Expire/supersede older OTPs when new one is sent. Verify this is already done in `create_otp`; strengthen tests if needed.

### Frontend tasks

1. In `SettingsPage.jsx`, remove re-verify button after verified.

Replace:

```jsx
<Button>{status?.email_verified ? 'Re-verify' : 'Verify Now'}</Button>
```

with:

```jsx
{status?.email_verified ? (
  <Button size="sm" variant="secondary" disabled>Verified</Button>
) : (
  <Link to="/verify-email"><Button size="sm">Verify Now</Button></Link>
)}
```

Do the same for phone.

2. In `VerifyEmailPage.jsx` and `VerifyPhonePage.jsx`:
   - call `getVerificationStatus` on mount
   - if already verified, show success state and link back to settings
   - if no phone exists, show “No phone number on file” and link to profile/settings
3. Improve OTP destination copy:
   - Email: “We sent the code to your registered email address.”
   - Phone: “We sent the code by SMS to your registered phone number.”
   - Local/dev: if `development_code` exists, label it clearly as “Local development only.”
4. After successful verification, refresh settings status or navigate with a success toast.

### Tests

Backend:

```bash
cd backend
PYTHONPATH=. pytest -q tests/test_verification.py
```

Add tests:

1. Verified email send endpoint returns already verified/no-op and does not create another OTP.
2. Verified phone send endpoint returns already verified/no-op and does not create another OTP.
3. `development_code` absent when `expose_dev_otp=False`.
4. Phone send commits OTP and SMS outbox across a new DB session.
5. No phone returns structured `NO_PHONE` error.
6. Resend cooldown works if implemented.

Frontend:

```bash
cd frontend
npm run build
```

Acceptance criteria:

- After email is verified, Settings shows Verified and no Re-verify action.
- After phone is verified, Settings shows Verified and no Re-verify action.
- User clearly knows where the OTP goes.
- Production responses never expose OTP codes.
- Phone verification can be replaced with a real SMS provider without changing API routes.

---

## 9. Phase 5 — Wire every UI action to backend and fix broken frontend/backend contracts

### Current broken/misaligned contracts found

1. `frontend/src/services/documentService.js` calls:

```js
GET /document-templates/{id}
```

but backend has no corresponding GET endpoint.

2. `frontend/src/routes/AppRoutes.jsx` duplicates admin routes under both generic tenant route and super-admin route.

3. `frontend/src/pages/SettingsPage.jsx` uses landing paths that do not exist:

```js
/sales/orders       // actual route: /sales
/purchasing/orders  // actual route: /purchases
```

4. `AuthContext.login` does not apply preferences immediately after login.

5. Download logic is duplicated and inconsistent across services.

6. Some direct `fetch` calls bypass `apiRequest` global error handling.

### Target files

- `frontend/src/routes/AppRoutes.jsx`
- `frontend/src/context/AuthContext.jsx`
- `frontend/src/services/apiClient.js`
- `frontend/src/services/documentService.js`
- `frontend/src/services/catalogService.js`
- `frontend/src/services/reportsService.js`
- `frontend/src/pages/SettingsPage.jsx`
- all list/detail/form pages under `frontend/src/pages/*`
- backend API modules corresponding to service calls

### Tasks

#### 5.1 Create a frontend-backend route contract audit

Create a small script:

```text
scripts/audit_frontend_backend_contracts.py
```

Purpose:

- extract frontend service endpoint strings
- list backend FastAPI routes from `app.api.router`
- normalize dynamic segments like `:id`, `{id}`
- report possible frontend calls without backend match

This does not need to be perfect. It should catch obvious mismatches like `GET /document-templates/{id}`.

#### 5.2 Fix route guard structure

In `AppRoutes.jsx`:

- Remove `/admin` routes from the generic `ProtectedRoute` + `MainLayout` block.
- Keep admin routes only under `ProtectedRoute requiredRole="SUPER_ADMIN"` + `AdminLayout`.
- Make sure super admin visiting `/dashboard` redirects to `/admin`.
- Make sure tenant user visiting `/admin` gets not found or permission state, not wrong layout.

#### 5.3 Fix settings landing page options

Replace:

```js
{ value: '/sales/orders', label: 'Sales Orders' }
{ value: '/purchasing/orders', label: 'Purchase Orders' }
```

with:

```js
{ value: '/sales', label: 'Sales Orders' }
{ value: '/purchases', label: 'Purchase Orders' }
```

Also validate default landing path before saving. If it is invalid, reject with a UI error and backend validation error.

#### 5.4 Apply preferences immediately after login

In `AuthContext.login`, after setting token/user, call:

```js
await applyPreferences(data.access_token);
```

or call `await loadMe(data.access_token)` to ensure server state and preferences are fresh.

#### 5.5 Centralize blob downloads

Add to `apiClient.js`:

```js
export async function downloadBlob(path, { accessToken } = {}) { ... }
```

Then update:

- `documentService.downloadInvoicePdf`
- `documentService.downloadBillPdf`
- `reportsService.downloadReportCsv`
- `catalogService.downloadProductsCsv`
- import template downloads if present

#### 5.6 UI action checklist

For every page, verify:

- Create button calls backend and handles validation errors.
- Edit/save button calls backend and updates local state.
- Delete/cancel/void buttons show confirmation if destructive.
- Download/export buttons show loading and errors.
- Empty tables use `EmptyState`.
- API errors show `ErrorState` or toast.
- Buttons are disabled while request is in progress.
- Forms display backend validation messages where possible.

Suggested pages to audit first:

- `DocumentsPages.jsx`
- `SettingsPage.jsx`
- `ProductImportPage.jsx`
- `DashboardPage.jsx`
- `PurchasesPage.jsx` and purchase detail/receive pages
- `SalesPage.jsx` and sales detail/pick/package/fulfill pages
- `ReturnsPage.jsx` and return inspect/process pages
- report pages and CSV exports

### Tests

```bash
cd frontend
npm run build
```

Backend targeted tests after route additions:

```bash
cd backend
PYTHONPATH=. pytest -q tests/test_documents.py tests/test_settings.py
```

Add script run:

```bash
python scripts/audit_frontend_backend_contracts.py
```

Acceptance criteria:

- No known frontend service points to a missing backend endpoint.
- Admin route access is correct by role.
- Settings landing pages all point to real routes.
- Preferences apply immediately after login.
- Blob downloads behave consistently.

---

## 10. Phase 6 — Smallest UI components and production polish

### Scope

This phase focuses on the “smallest to smallest UI components” request. The goal is not a redesign; it is to make interactions reliable and professional.

### Components to inspect

- `frontend/src/components/ui/Button.jsx`
- `frontend/src/components/ui/Card.jsx`
- `frontend/src/components/ui/EmptyState.jsx`
- `frontend/src/components/ui/ErrorState.jsx`
- `frontend/src/components/ui/LoadingState.jsx`
- `frontend/src/components/ui/TableShell.jsx`
- `frontend/src/components/ui/Badge.jsx`
- `frontend/src/components/NotificationCenter.jsx`
- `frontend/src/layouts/MainLayout.jsx`
- `frontend/src/layouts/AdminLayout.jsx`
- all forms in `frontend/src/pages/*FormPage.jsx`

### UI polish checklist

1. Buttons:
   - disabled state visible
   - loading state visible
   - no double submit
2. Forms:
   - required fields marked
   - backend validation errors displayed
   - success toasts consistent
   - cancel/back action available
3. Tables:
   - empty state
   - loading state
   - error state
   - long text truncation
   - responsive overflow
4. Popovers/dropdowns:
   - close on outside click
   - keyboard escape if possible
   - accessible labels/titles
5. Navigation:
   - active route state correct
   - no dead links
   - no routes that 404 from settings/default landing
6. Reports:
   - filters disabled during loading
   - CSV export errors surfaced
7. Documents:
   - PDF download loading state
   - send email loading state
   - status transitions disable invalid actions
8. Verification:
   - verified users cannot accidentally re-trigger verification
   - no phone on file is handled gracefully
9. Notifications:
   - unread badge disappears after read/clear
   - all/individual actions work
   - action URLs navigate
10. Responsive layout:
   - dashboard cards stack cleanly on mobile/tablet
   - report tables remain usable

### Acceptance criteria

- No obvious clickable dead controls.
- No silent failures on critical actions.
- UI communicates loading/error/success states consistently.
- Frontend build passes.

---

## 11. Phase 7 — Testing strategy and QA flows

### Backend test command set

Run after each backend-heavy phase:

```bash
cd backend
PYTHONPATH=. pytest -q tests/test_documents.py tests/test_notifications.py tests/test_verification.py tests/test_reports.py tests/test_settings.py
```

Before final merge:

```bash
cd backend
PYTHONPATH=. pytest -q
PYTHONPATH=. alembic upgrade head
```

### Frontend test/build command set

```bash
cd frontend
npm run build
```

Add frontend tests if the stack supports it. If no test runner exists, add a minimal Vitest setup later, but do not block urgent bug fixes on test framework migration.

### Manual QA scenario checklist

#### Dashboard

1. Create tenant, products, warehouses, stock movements, sales orders, purchase orders, returns.
2. Open dashboard.
3. Verify charts display real data.
4. Change period filter.
5. Verify previous trend changes based on real previous period data.
6. Fresh tenant shows empty chart states, not crashes.

#### Invoice/Bill templates

1. Create two invoice PDF templates with visually distinct content.
2. Select template A in Settings.
3. Download invoice PDF and verify template A.
4. Select template B.
5. Download same invoice and verify template B.
6. Repeat for bills.
7. Try injecting wrong template ID via API and verify backend rejects it.

#### Notifications

1. Login as tenant admin and inventory manager.
2. Trigger low stock/reorder event.
3. Verify both roles receive notifications.
4. Login as viewer; verify viewer does not receive write-operation notifications unless intended.
5. Mark one read; verify badge decrements.
6. Mark all read; verify badge disappears.
7. Clear one and clear all; verify active list updates.
8. Click notification action; verify navigation.

#### Email verification

1. User not verified sees “Verify Now.”
2. Send code.
3. Confirm code.
4. Return to Settings; button is gone/disabled as “Verified.”
5. Direct visit `/verify-email`; page says already verified.

#### Phone verification

1. User with no phone sees no send action.
2. User with phone sends code.
3. In development, verify where the code is visible.
4. In production-like config, response does not contain `development_code`.
5. Confirm code; Settings shows Verified and no Re-verify.

#### Routes/preferences

1. Set default landing to Sales Orders.
2. Logout/login.
3. Verify landing goes to `/sales`.
4. Set default landing to Purchase Orders.
5. Logout/login.
6. Verify landing goes to `/purchases`.
7. Tenant user cannot access `/admin`.
8. Super admin sees admin layout only.

---

## 12. Suggested implementation order

Use this exact order to minimize breakage:

1. **Phase 0:** Fix validation/import path and CI reliability.
2. **Phase 5 quick fixes:** route duplication, settings bad paths, login preferences, missing document template GET endpoint.
3. **Phase 2:** selected invoice/bill template validation and tests.
4. **Phase 4:** verification no re-verify + OTP safety + phone provider abstraction.
5. **Phase 3:** notifications role-based service and UI actions.
6. **Phase 1:** dashboard charts and analytics.
7. **Phase 6:** UI polish sweep.
8. **Phase 7:** final full QA and regression.

Reasoning:

- Route/settings/template/verification bugs are concrete and smaller.
- Notification engine touches many services, so do it after contracts are stable.
- Dashboard analytics is larger and should be implemented after the reporting layer is understood.

---

## 13. File-by-file notes for Claude

### `backend/app/services/reports.py`

- Remove random previous KPI generation.
- Add real chart builders.
- Keep expensive aggregation out of frontend.

### `backend/app/schemas/reports.py`

- Extend `OperationalDashboard` with `period`, `charts`, and `insights`.
- Use explicit Pydantic models instead of `dict[str, Any]` where possible.

### `frontend/src/pages/DashboardPage.jsx`

- Add filters and charts.
- Reduce separate list calls where backend dashboard can provide counts.
- Preserve current KPI cards but connect trend icons to real previous data only.

### `backend/app/services/documents.py`

- Validate preferred template purpose and tenant.
- Add tests around `render_invoice_pdf` and `render_bill_pdf`.
- Consider returning selected template metadata headers from PDF endpoints.

### `backend/app/api/documents.py`

- Add `GET /document-templates/{template_id}` or remove frontend caller.
- For PDF endpoints, consider adding safe template headers.

### `frontend/src/pages/SettingsPage.jsx`

- Remove `Re-verify` button when already verified.
- Fix default landing paths.
- Template selection should be clear, previewable, and save confirmation should be visible.

### `backend/app/repositories/notification.py`

- Tenant-scope all list/count/update queries.
- Add clear one/clear all support.
- Exclude cleared notifications from active lists and unread count.

### `backend/app/api/notifications.py`

- Add missing endpoints.
- Return updated unread count after mutating actions.

### `frontend/src/components/NotificationCenter.jsx`

- Add tabs/actions/clear all.
- Optimistically update unread count.
- Do not poll without token.
- Navigate on action URL.

### `backend/app/api/verification.py`

- Add already verified guards.
- Add explicit commit to phone send.
- Remove production OTP exposure.

### `frontend/src/pages/VerifyEmailPage.jsx` and `VerifyPhonePage.jsx`

- Check verification status on mount.
- Show already verified state.
- Clarify OTP destination.

### `frontend/src/routes/AppRoutes.jsx`

- Remove admin routes from tenant `MainLayout` block.
- Keep super-admin routes under `AdminLayout` only.

### `frontend/src/context/AuthContext.jsx`

- Apply preferences immediately after login.

---

## 14. Definition of done

The next phase is complete only when all are true:

- Frontend build passes.
- Backend compile passes.
- Targeted backend tests pass.
- CI config can run tests without manual `PYTHONPATH` surprises.
- Invoice/bill PDFs use selected templates and reject wrong template purpose.
- Notifications support role-based creation, mark read, mark all read, clear one, clear all, and badge correctness.
- Email/phone verification does not show re-verify once verified.
- Production OTP responses do not leak codes.
- Dashboard charts use real backend data, not random/simulated values.
- Admin routes are not mounted under tenant layout.
- Settings default landing pages point to existing routes.
- All major UI actions have loading/error/success handling.

---

## 15. Final commands before handing back

Run from repo root:

```bash
cd backend
python -m compileall app
PYTHONPATH=. pytest -q tests/test_documents.py tests/test_notifications.py tests/test_verification.py tests/test_reports.py tests/test_settings.py
PYTHONPATH=. alembic upgrade head

cd ../frontend
npm run build

cd ..
docker compose config >/dev/null
git status --short
```

If full backend tests are fixed:

```bash
cd backend
PYTHONPATH=. pytest -q
```

When reporting back, include:

```text
Changed files:
- ...

Tests run:
- ...

Manual QA performed:
- ...

Remaining risks:
- ...
```
