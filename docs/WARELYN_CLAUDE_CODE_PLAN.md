# Warelyn — Claude Code Implementation Plan
**Project:** Warelyn Inventory SaaS  
**Plan type:** Phased, prompt-ready sessions for Claude Code  
**Based on:** Codebase scan (May 2026) + Business Workflow/RBAC/Currency analysis

---

## How to Use This Plan

1. Start a **new Claude Code session** for each phase.
2. **Run the skill invocations** listed at the top of each phase first — they orient Claude Code before it touches code.
3. **Paste the implementation prompt** for that phase.
4. **Run verification** at the end using `/warelyn-test-runner`.
5. If anything fails, invoke `/warelyn-debug-runbook` before moving to the next phase.
6. Never skip a phase. Never claim a phase complete unless both backend tests and frontend build pass.

---

## Confirmed Codebase State (From Scan)

### What already exists ✅
| Area | Status |
|---|---|
| FastAPI backend with models, services, repos, schemas, APIs | ✅ Solid |
| Alembic migrations (18 versions up to Phase 20) | ✅ Solid |
| `UserRole` enum: all 6 roles including VIEWER in both FE + BE | ✅ Confirmed |
| `require_roles()` dependency on all API routes | ✅ Solid |
| Frontend `permissions.js` with `ROUTE_ACCESS` and `ACTION_ACCESS` | ✅ Exists |
| `RoleGuard` component | ✅ Exists |
| `TenantSettings.currency` field (String(3), default `"USD"`) | ✅ In DB already |
| Events outbox (`publish_event`) | ✅ Stub exists, never called |
| Full sales, purchase, fulfillment, returns, picking/packing, putaway | ✅ Solid |
| Document templates, PDF service, email service | ✅ Solid |
| Notification model and API | ✅ Exists |

### What is MISSING ❌
| Gap | Evidence |
|---|---|
| `formatMoney()` has no currency symbol or code | `formatters.js` — plain `Intl.NumberFormat`, no `style:'currency'` |
| No `TenantSettingsContext` | Not found in zip |
| No `currencies.js` registry | Not found in zip |
| No `CurrencySelect` component | Not found in zip |
| No `workflow_tasks` or `workflow_events` tables | No model or migration found |
| Outbox `publish_event` never called from any service | `sales.py`, `purchasing.py` have no import of outbox |
| No `My Tasks` page | No page file found |
| `DashboardPage` is role-generic | Single file, no role branching |
| No currency snapshot on invoices or bills | `documents.py` model has no `currency_code` column |
| Reports have no `currency_code` metadata | `reports.py` service confirmed |

---

## Phase Overview

| Phase | Focus | Key Skills |
|---|---|---|
| **1** | Currency foundation | `pyright-lsp`, `typescript-lsp`, `/warelyn-api-contract-check`, `/warelyn-test-runner` |
| **2** | Currency in documents + reports | `/warelyn-db-migration-check`, `/warelyn-test-runner` |
| **3** | Workflow task engine | `/warelyn-db-migration-check`, `/warelyn-test-runner`, `postman` |
| **4** | Sales workflow automation | `/warelyn-workflow-audit`, `/warelyn-test-runner` |
| **5** | Purchase workflow automation | `/warelyn-workflow-audit`, `/warelyn-test-runner` |
| **6** | My Tasks page + role dashboards | `/frontend:react-patterns`, `/dev-tools:ux-audit`, `/warelyn-test-runner` |
| **7** | RBAC audit + cleanup | `/warelyn-rbac-audit`, `/warelyn-security-review`, `semgrep` |
| **8** | Testing hardening | `/warelyn-test-runner`, `/dev-tools:vitest`, `playwright` |

---

---

# Phase 1 — Currency Foundation

## Skills to invoke first (before writing any code)

```
/dev-tools:project-health
/warelyn-api-contract-check
```

`project-health` gives a current state snapshot. `api-contract-check` identifies any existing currency-related frontend/backend mismatches before you add new code.

## What to build
- `backend/app/utils/currency.py` — supported currencies registry + validation helpers
- `backend/app/schemas/settings.py` — Pydantic currency validator
- `backend/app/api/settings.py` — `GET /settings/currencies` endpoint
- `frontend/src/lib/currencies.js` — mirrored currency registry
- `frontend/src/context/TenantSettingsContext.jsx` — context propagating tenant currency app-wide
- `frontend/src/components/ui/CurrencySelect.jsx` — currency dropdown component
- `frontend/src/utils/formatters.js` — currency-aware `formatMoney(value, currencyCode)`
- `frontend/src/pages/SettingsPage.jsx` — add `CurrencySelect` to company settings form

## Implementation prompt

```
You are working inside the Warelyn Inventory SaaS repository.
Act as warelyn-currency-localization-specialist.

## Context

Warelyn is a FastAPI + React SaaS. Backend at `backend/`, frontend at `frontend/`.

TenantSettings already has a `currency` field (String(3), default "USD") in `backend/app/models/settings.py`. The DB column exists — no migration needed for settings.

The frontend `formatters.js` has `formatMoney()` but it is NOT currency-aware. It uses plain Intl.NumberFormat with no style:'currency'. This must be fixed.

## Backend Tasks

1. Create `backend/app/utils/currency.py`:
   - `SUPPORTED_CURRENCIES` dict: key = ISO 4217 code, value = {name, symbol, decimal_places}
   - Include: USD, EUR, GBP, INR, JPY, CAD, AUD, CHF, CNY, AED, SGD, BRL, MXN, ZAR, NGN, KES, IDR, MYR, PHP, THB, SEK, NOK, DKK, NZD, HKD, PKR, EGP, TRY, SAR, QAR
   - `validate_currency_code(code: str) -> bool`
   - `get_currency_info(code: str) -> dict | None`

2. Update `backend/app/schemas/settings.py`:
   - Import `validate_currency_code`
   - Add Pydantic field_validator on `currency` that rejects unsupported codes with a clear message

3. Update `backend/app/services/settings.py`:
   - Verify currency validation is triggered on save via schema validation

4. Add `GET /settings/currencies` to `backend/app/api/settings.py`:
   - Returns [{code, name, symbol, decimal_places}] for all supported currencies
   - Accessible to all authenticated tenant roles (read_roles)

## Frontend Tasks

5. Create `frontend/src/lib/currencies.js`:
   - Same ~30 currencies as backend
   - Export `CURRENCIES` array: [{code, name, symbol, decimalPlaces}]
   - Export `getCurrencyInfo(code)` helper

6. Create `frontend/src/context/TenantSettingsContext.jsx`:
   - Calls `GET /api/settings` on mount
   - Exposes: tenantSettings, currency (code string, default "USD"), currencyInfo (symbol/decimals object), refreshSettings()
   - Wrap the authenticated layout (MainLayout) with this provider

7. Update `frontend/src/utils/formatters.js`:
   - Update formatMoney(value, currencyCode = 'USD', options = {}) to use:
     new Intl.NumberFormat(undefined, { style: 'currency', currency: currencyCode, minimumFractionDigits: options.minimumFractionDigits ?? 2, maximumFractionDigits: options.maximumFractionDigits ?? 2 }).format(number)
   - Backward compat: if currencyCode is invalid, fall back to plain number formatting with no symbol

8. Create `frontend/src/components/ui/CurrencySelect.jsx`:
   - Props: value, onChange, disabled, className
   - Lists from CURRENCIES
   - Display format: "USD — US Dollar"

9. Update the settings page (find where company settings are saved):
   - Add CurrencySelect next to the timezone field
   - Send selected currency code to backend on save

## Verification

Run:
/warelyn-test-runner

Then manually verify the new endpoint works:
/warelyn-api-contract-check
```

---

---

# Phase 2 — Currency in Documents and Reports

## Skills to invoke first

```
/warelyn-db-migration-check
```

Run this before writing the migration so you know the current state of `invoices` and `bills` tables and can confirm the columns don't already exist.

## What to build
- Alembic migration adding `currency_code` to `invoices` and `bills`
- Model, schema, and service updates for document currency snapshots
- PDF/email template variables `{{currency_code}}` and `{{currency_symbol}}`
- Report service `currency_code` metadata on all monetary responses

## Implementation prompt

```
You are working inside the Warelyn Inventory SaaS repository.
Act as warelyn-currency-localization-specialist and warelyn-database-migration-specialist.

## Context

Phase 1 is complete. Tenant has a currency field. Frontend has TenantSettingsContext and currency-aware formatMoney.

Now invoices and bills need to snapshot the currency at creation time, and reports need to carry currency metadata.

## Backend Tasks

1. Create migration `backend/alembic/versions/YYYYMMDD_0019_document_currency_snapshot.py`:
   - Add `currency_code VARCHAR(3) NOT NULL DEFAULT 'USD'` to invoices table
   - Add `currency_code VARCHAR(3) NOT NULL DEFAULT 'USD'` to bills table
   - Proper downgrade

2. Update `backend/app/models/documents.py`:
   - Add `currency_code: Mapped[str]` (String(3), nullable=False, default="USD") to Invoice model
   - Add same to Bill model

3. Update `backend/app/schemas/documents.py`:
   - Expose `currency_code` in InvoiceRead and BillRead
   - Add optional `currency_code` to InvoiceCreate and BillCreate (defaults to tenant currency)

4. Update `backend/app/services/documents.py`:
   - In create_invoice(): auto-populate currency_code from tenant settings if not in request
   - In create_bill(): same
   - Fetch tenant settings via settings repository
   - This snapshot is immutable — never overwrite after creation

5. Update PDF template variable building (documents.py or pdf_service.py):
   - Add currency_code and currency_symbol to template variable context
   - Look up symbol from backend/app/utils/currency.py

6. Update `backend/app/services/reports.py`:
   - Add currency_code to all report response objects that contain monetary values
   - Source it from tenant settings

## Frontend Tasks

7. Update InvoiceDetailPage and BillDetailPage:
   - Pass doc.currency_code into formatMoney(value, doc.currency_code) everywhere money is displayed
   - Do NOT use tenant's current currency for historical documents

8. Update all report pages:
   - Use formatMoney(value, reportData.currency_code) for monetary values
   - Fall back to TenantSettingsContext currency if report response doesn't include it yet

## Verification

Run:
/warelyn-db-migration-check
/warelyn-test-runner
```

---

---

# Phase 3 — Workflow Task Engine

## Skills to invoke first

```
/warelyn-db-migration-check
/warelyn-workflow-audit
```

`db-migration-check` confirms the current migration state before adding new tables. `workflow-audit` documents the current gaps in workflow handoffs — this gives you the full picture of what the task engine needs to support.

## What to build
- Migration: `workflow_events` and `workflow_tasks` tables
- `backend/app/models/workflow.py`
- `backend/app/schemas/workflow.py`
- `backend/app/repositories/workflow.py`
- `backend/app/services/workflow.py`
- `backend/app/api/workflow.py`
- Register in `router.py`

## Implementation prompt

```
You are working inside the Warelyn Inventory SaaS repository.
Act as warelyn-backend-fastapi-specialist and warelyn-database-migration-specialist.

## Context

There is a minimal event outbox at backend/app/events/outbox.py — publish_event(db, tenant_id, event_type, payload) — but it is never called from any service.

There are NO workflow_tasks or workflow_events tables. Build them now.

Roles: TENANT_ADMIN, INVENTORY_MANAGER, SALES_STAFF, PURCHASE_STAFF, VIEWER, SUPER_ADMIN.

## Migration

1. Create `backend/alembic/versions/YYYYMMDD_0020_workflow_task_engine.py`:

workflow_events table:
- id SERIAL PRIMARY KEY
- tenant_id INTEGER NOT NULL FK→tenants CASCADE
- event_type VARCHAR(100) NOT NULL
- entity_type VARCHAR(100) NOT NULL
- entity_id INTEGER NOT NULL
- actor_user_id INTEGER FK→users SET NULL
- payload_json JSONB
- created_at TIMESTAMPTZ NOT NULL DEFAULT now()
- INDEX on (tenant_id, event_type, created_at)

workflow_tasks table:
- id SERIAL PRIMARY KEY
- tenant_id INTEGER NOT NULL FK→tenants CASCADE
- workflow_type VARCHAR(100) NOT NULL
- entity_type VARCHAR(100) NOT NULL
- entity_id INTEGER NOT NULL
- step_key VARCHAR(100) NOT NULL
- title VARCHAR(255) NOT NULL
- description TEXT
- assigned_role VARCHAR(50) NOT NULL
- assigned_to_user_id INTEGER FK→users SET NULL
- status VARCHAR(30) NOT NULL DEFAULT 'OPEN'
- priority VARCHAR(20) NOT NULL DEFAULT 'NORMAL'
- action_url VARCHAR(500)
- created_by INTEGER FK→users SET NULL
- completed_by INTEGER FK→users SET NULL
- created_at TIMESTAMPTZ NOT NULL DEFAULT now()
- due_at TIMESTAMPTZ
- completed_at TIMESTAMPTZ
- metadata_json JSONB
- INDEX on (tenant_id, assigned_role, status)
- INDEX on (tenant_id, assigned_to_user_id, status)
- INDEX on (tenant_id, entity_type, entity_id)

## Models

2. Create `backend/app/models/workflow.py`:
   - WorkflowEvent and WorkflowTask models
   - Add both to backend/app/models/__init__.py

## Schemas

3. Create `backend/app/schemas/workflow.py`:
   - WorkflowTaskRead — all fields for API responses
   - WorkflowTaskCreate — internal service use
   - WorkflowTaskComplete — {notes: str | None}
   - WorkflowEventRead — for audit views

## Repository

4. Create `backend/app/repositories/workflow.py` — WorkflowRepository:
   - create_task(tenant_id, data: dict) -> WorkflowTask
   - get_tasks_for_role(tenant_id, role, status=None) -> list[WorkflowTask]
   - get_tasks_for_user(tenant_id, user_id, status=None) -> list[WorkflowTask]
   - get_task(tenant_id, task_id) -> WorkflowTask | None
   - complete_task(tenant_id, task_id, user_id) -> WorkflowTask
   - cancel_tasks_for_entity(tenant_id, entity_type, entity_id)
   - has_open_task(tenant_id, entity_type, entity_id, step_key) -> bool  ← prevents duplicates
   - log_event(tenant_id, event_type, entity_type, entity_id, actor_user_id, payload)

## Service

5. Create `backend/app/services/workflow.py` — WorkflowService:
   - create_task(...) — calls has_open_task first; skips if duplicate
   - complete_task(tenant_id, task_id, user_id)
   - cancel_entity_tasks(tenant_id, entity_type, entity_id)
   - get_my_tasks(tenant_id, user, status_filter) — returns tasks for user's role OR direct assignment
   - log_event(tenant_id, event_type, entity_type, entity_id, actor_user_id, payload)

## API

6. Create `backend/app/api/workflow.py`:
   - GET /workflow/my-tasks?status=OPEN — all tenant roles except VIEWER
   - POST /workflow/tasks/{task_id}/complete — role must match assigned_role OR be TENANT_ADMIN
   - GET /workflow/tasks/{task_id} — task detail
   - GET /workflow/events?entity_type=&entity_id= — TENANT_ADMIN only

7. Register in `backend/app/api/router.py`

## Verification

Run:
/warelyn-db-migration-check
/warelyn-test-runner

Then test the new endpoints manually:
/warelyn-api-contract-check
```

---

---

# Phase 4 — Sales Workflow Automation

## Skills to invoke first

```
/warelyn-workflow-audit
```

This audits the current sales workflow and produces the exact list of gaps. Read the output before touching any service file — it tells you exactly which state transitions are missing task creation.

## What to build
Wire `WorkflowService` calls into `sales.py`, `fulfillment.py`, `documents.py`, `returns.py` at each state transition.

## Implementation prompt

```
You are working inside the Warelyn Inventory SaaS repository.
Act as warelyn-backend-fastapi-specialist.

## Context

Phase 3 complete. WorkflowService exists with create_task(), complete_task(), cancel_entity_tasks(), log_event(), and has_open_task() (duplicate guard).

The sales flow:
1. SalesService.confirm_sales_order() — confirms order
2. Picking via PickTask model in fulfillment service
3. Packing via package records
4. SalesService.commit_fulfillment() — commits fulfillment
5. Invoice via documents service

## Instructions

Read these files completely before making any changes:
- backend/app/services/sales.py
- backend/app/services/fulfillment.py
- backend/app/services/documents.py
- backend/app/services/returns.py

Then make targeted additions only. Do not refactor existing logic.

## Wire workflow into sales transitions

In sales.py — confirm_sales_order(), after status → CONFIRMED:
  workflow = WorkflowService(self.db)
  workflow.log_event(tenant_id, "SALES_ORDER_CONFIRMED", "sales_order", order.id, actor_user_id, {"order_number": order.order_number})
  workflow.create_task(tenant_id, "SALES", "sales_order", order.id, "PICK_ORDER",
    title=f"Pick items for order {order.order_number}",
    description="Sales order confirmed. Pick and reserve required stock.",
    assigned_role="INVENTORY_MANAGER",
    actor_user_id=actor_user_id,
    action_url=f"/sales/{order.id}",
    priority="NORMAL")

In sales.py — cancel_sales_order(), after cancellation:
  WorkflowService(self.db).cancel_entity_tasks(tenant_id, "sales_order", order.id)

In sales.py — commit_fulfillment(), after fulfillment committed:
  workflow.log_event(tenant_id, "SALES_FULFILLMENT_COMMITTED", ...)
  workflow.create_task(..., step_key="CREATE_INVOICE", assigned_role="SALES_STAFF",
    title="Create and send invoice for fulfilled order",
    action_url=f"/invoices/new?sales_order_id={order_id}")

In documents.py — send_invoice() or mark-as-sent method:
  workflow.log_event(tenant_id, "INVOICE_SENT", ...)
  # complete any open CREATE_INVOICE task for this sales order

In returns.py — create/submit return method:
  workflow.log_event(tenant_id, "RETURN_SUBMITTED", ...)
  workflow.create_task(..., step_key="RETURN_QC", assigned_role="INVENTORY_MANAGER",
    title=f"Inspect returned items for return #{return_obj.id}",
    action_url=f"/returns/{return_obj.id}")

## Critical rules
- Import WorkflowService at top of each file
- Wrap ALL workflow calls in try/except — workflow failures must NEVER break the main operation
- Do not break any existing tests

## Tests to write

In backend/tests/test_sales_workflow.py:
1. Confirming a sales order creates exactly one OPEN PICK_ORDER task for INVENTORY_MANAGER
2. Confirming the same order twice does NOT create a second task (duplicate guard)
3. Cancelling a sales order cancels all open tasks for that order
4. Committing a fulfillment creates a CREATE_INVOICE task for SALES_STAFF

## Verification

Run:
/warelyn-test-runner
```

---

---

# Phase 5 — Purchase Workflow Automation

## Skills to invoke first

```
/warelyn-workflow-audit
```

Same as Phase 4 — run the audit on the purchase workflow first. Check the output section on purchase handoffs specifically before writing anything.

## What to build
Wire `WorkflowService` into `purchasing.py`, `operations.py` (putaway), `documents.py` (bill recording), and `jobs/` (low stock).

## Implementation prompt

```
You are working inside the Warelyn Inventory SaaS repository.
Act as warelyn-backend-fastapi-specialist.

## Context

Phase 4 complete. Sales workflow fires tasks correctly.

Purchase flow:
1. PO submitted → approval (if high value) or confirmation
2. Receipt committed → putaway task for INVENTORY_MANAGER
3. Putaway complete → bill task for PURCHASE_STAFF
4. Bill recorded → RECORD_BILL task completed

## Instructions

Read these files first:
- backend/app/services/purchasing.py
- backend/app/services/operations.py
- backend/app/services/inventory.py
- backend/app/jobs/

Then make targeted additions only.

## Wire workflow into purchase transitions

In purchasing.py — PO submit/confirm method:
  workflow.log_event(tenant_id, "PURCHASE_ORDER_SUBMITTED", ...)
  if order.total_value > 10000:  # high-value threshold
    workflow.create_task(..., step_key="APPROVE_PO", assigned_role="TENANT_ADMIN",
      title=f"Approve high-value PO {po.po_number}",
      priority="HIGH")
  else:
    workflow.log_event(tenant_id, "PURCHASE_ORDER_CONFIRMED", ...)

In purchasing.py — receipt commit method:
  workflow.log_event(tenant_id, "RECEIPT_COMMITTED", ...)
  workflow.create_task(..., step_key="PUTAWAY_STOCK", assigned_role="INVENTORY_MANAGER",
    title=f"Putaway received stock for PO {po.po_number}",
    action_url=f"/purchase-receipts/{receipt.id}")

In operations.py — putaway complete method:
  workflow.log_event(tenant_id, "PUTAWAY_COMPLETED", ...)
  # complete any open PUTAWAY_STOCK task for this receipt
  workflow.create_task(..., step_key="RECORD_BILL", assigned_role="PURCHASE_STAFF",
    title=f"Record bill for received PO {po.po_number}",
    action_url=f"/bills/new?purchase_order_id={po.id}")

In documents.py — create/record bill method:
  workflow.log_event(tenant_id, "BILL_RECORDED", ...)
  # complete any open RECORD_BILL task for this PO

In jobs/ — low stock detection:
  If not workflow.has_open_task(tenant_id, "product", product.id, "REORDER_STOCK"):
    workflow.create_task(..., step_key="REORDER_STOCK", assigned_role="PURCHASE_STAFF",
      title=f"Low stock: {product.name} below reorder point",
      priority="HIGH",
      action_url=f"/catalog/products/{product.id}")

## Critical rules
- Wrap ALL workflow calls in try/except
- has_open_task() duplicate guard is mandatory for low stock tasks
- Do not break existing tests

## Tests to write

In backend/tests/test_purchase_workflow.py:
1. Committing a receipt creates a PUTAWAY_STOCK task for INVENTORY_MANAGER
2. Completing putaway creates a RECORD_BILL task for PURCHASE_STAFF
3. Recording a bill completes the RECORD_BILL task
4. Low stock detection does NOT create a second REORDER_STOCK task if one is already open

## Verification

Run:
/warelyn-test-runner
```

---

---

# Phase 6 — My Tasks Page + Role Dashboards

## Skills to invoke first

```
/frontend:react-patterns
/dev-tools:project-health
```

`react-patterns` gives you the correct component and hook patterns for this codebase before you write any JSX. `project-health` confirms the frontend is in a clean state before adding new pages.

## What to build
- `frontend/src/services/workflowService.js`
- `frontend/src/pages/MyTasksPage.jsx`
- Route `/my-tasks` in `AppRoutes.jsx`
- "My Tasks" nav item with count badge in `SidebarNav.jsx`
- Role-specific task widgets in `DashboardPage.jsx`

## Implementation prompt

```
You are working inside the Warelyn Inventory SaaS repository.
Act as warelyn-frontend-react-specialist.

## Context

Phases 3–5 complete. Backend has:
- GET /workflow/my-tasks?status=OPEN
- POST /workflow/tasks/{task_id}/complete

## Study first (read before writing anything)

- frontend/src/pages/DashboardPage.jsx
- frontend/src/components/SidebarNav.jsx
- frontend/src/routes/AppRoutes.jsx
- frontend/src/lib/permissions.js
- frontend/src/pages/PurchasesPage.jsx  ← pattern reference for list pages

## Tasks

1. Create frontend/src/services/workflowService.js:
   - getMyTasks(status = 'OPEN') → GET /api/workflow/my-tasks?status={status}
   - completeTask(taskId) → POST /api/workflow/tasks/{taskId}/complete
   - getMyTaskCount() → GET /api/workflow/my-tasks?status=OPEN, returns count

2. Create frontend/src/pages/MyTasksPage.jsx:
   - Filterable list: All / Open / In Progress / Completed tabs
   - Each task card: title, entity type + ID, assigned role badge, priority badge,
     created date, due date (red text if overdue), "View" button → task.action_url
   - "Mark Complete" button on OPEN tasks (calls completeTask, refreshes list)
   - Priority badges: HIGH = red, NORMAL = blue, LOW = grey
   - Empty state: use empty-data.svg pattern matching existing empty states
   - Loading state: match existing skeleton/loader pattern

3. Add route /my-tasks in AppRoutes.jsx:
   - Lazy load MyTasksPage
   - Add to ROUTE_ACCESS in permissions.js: all roles except VIEWER

4. Update SidebarNav.jsx:
   - Add "My Tasks" nav item with inbox/task icon
   - Add a useMyTaskCount hook that polls getMyTaskCount() every 60s
   - Show count badge when count > 0 (match existing notification badge style)
   - Position below Dashboard in nav order
   - Hidden for VIEWER role (check with canAccessRoute or hasAnyRole)

5. Update DashboardPage.jsx — add "Pending Tasks" widget section:
   - TENANT_ADMIN: task counts grouped by assigned_role
     e.g. "3 for Inventory Manager · 1 for Sales Staff"
   - INVENTORY_MANAGER: their 5 highest-priority open tasks
   - SALES_STAFF: their 5 open tasks
   - PURCHASE_STAFF: their 5 open tasks
   - VIEWER: no task widget
   - Each item clickable → /my-tasks
   - "View all →" link at bottom of widget

## Style rules
- Use Warelyn's deep blue / emerald / soft gray palette
- Match card, badge, and table patterns exactly from existing list pages
- The task cards must feel native — not like a new third-party component

## Verification

Run:
/frontend:design-review
/dev-tools:ux-audit
/dev-tools:responsiveness-check
/warelyn-test-runner
```

---

---

# Phase 7 — RBAC Audit + Permission Cleanup

## Skills to invoke first — these ARE the phase

For this phase, the project skills do the heavy lifting. Invoke them in order:

```
/warelyn-rbac-audit
/warelyn-security-review
```

Then run the security plugins:
- `security-guidance` — on any API files changed
- `semgrep` — full security scan on backend/app/api/ and backend/app/dependencies/

After the audit output, fix mismatches and then use the implementation prompt below.

## What to build
- Fix all frontend/backend RBAC mismatches found by the audit
- Tighten `permissions.js` ROUTE_ACCESS and ACTION_ACCESS
- Add missing `require_roles()` to any unguarded endpoints
- VIEWER enforcement sweep across all pages
- Output `docs/WARELYN_PERMISSION_MATRIX.md`

## Implementation prompt

```
You are working inside the Warelyn Inventory SaaS repository.
Act as warelyn-rbac-security-auditor.

## Context

You have already run /warelyn-rbac-audit and /warelyn-security-review.
Now implement the fixes.

## Fix checklist

Backend — for every file in backend/app/api/:
- Every endpoint has explicit require_roles()
- No endpoint accepts any authenticated user without a role check
- VIEWER is never in writer_roles on any endpoint
- PURCHASE_STAFF is not in sales writer_roles
- SALES_STAFF is not in purchase writer_roles

Frontend — permissions.js:
- ROUTE_ACCESS matches backend require_roles() for every route
- ACTION_ACCESS covers every action buttons in the UI
- VIEWER not in any action that mutates data

Frontend — page sweep:
- Search all pages for: Create, Edit, Delete, Confirm, Cancel, Send, Approve, Submit buttons
- Every one must be wrapped in canPerformAction(user, 'action') check or <RoleGuard>
- VIEWER must never see a write button anywhere

## Output

Create docs/WARELYN_PERMISSION_MATRIX.md:
- Table: all routes + which roles can access them
- Table: all actions + which roles can perform them
- List of fixes applied this phase
- List of remaining known gaps

## Verification

Run:
/warelyn-rbac-audit   ← re-run after fixes to confirm clean
/warelyn-test-runner
```

---

---

# Phase 8 — Testing Hardening

## Skills to invoke first

```
/warelyn-test-runner
/dev-tools:vitest
```

`test-runner` shows the current test state. `vitest` sets up or audits the frontend test configuration before you add new tests.

## What to build
Tests for RBAC enforcement, currency validation, workflow transitions, and tenant isolation.

## Implementation prompt

```
You are working inside the Warelyn Inventory SaaS repository.
Act as warelyn-testing-qa-specialist.

## Context

All previous phases complete. Now add comprehensive test coverage.

Read existing tests in backend/tests/ first to match patterns exactly.

## RBAC Tests — backend/tests/test_rbac.py

POST /sales-orders:
  - VIEWER → 403
  - PURCHASE_STAFF → 403
  - SALES_STAFF → 201 ✅

POST /purchases:
  - VIEWER → 403
  - SALES_STAFF → 403
  - PURCHASE_STAFF → 201 ✅

GET /settings/users:
  - INVENTORY_MANAGER → 403
  - SALES_STAFF → 403
  - TENANT_ADMIN → 200 ✅

GET /admin/*:
  - TENANT_ADMIN → 403
  - SUPER_ADMIN → 200 ✅

POST /workflow/tasks/{id}/complete:
  - VIEWER → 403
  - Role matching assigned_role → 200 ✅
  - TENANT_ADMIN (override) → 200 ✅

## Currency Tests — backend/tests/test_currency.py

- validate_currency_code("USD") → True
- validate_currency_code("XYZ") → False
- validate_currency_code("") → False
- PATCH /settings with currency="XYZ" → 422
- Create invoice → currency_code snapshots tenant currency
- Update tenant currency after invoice creation → invoice currency_code unchanged

## Workflow Tests — backend/tests/test_workflow.py

- Confirm sales order → exactly one OPEN PICK_ORDER task for INVENTORY_MANAGER
- Confirm same order twice → still only one task (duplicate guard works)
- Cancel sales order → all open tasks for that order are CANCELLED
- Commit fulfillment → CREATE_INVOICE task for SALES_STAFF
- Commit receipt → PUTAWAY_STOCK task for INVENTORY_MANAGER
- Complete putaway → RECORD_BILL task for PURCHASE_STAFF
- GET /workflow/my-tasks as INVENTORY_MANAGER → only INVENTORY_MANAGER tasks
- GET /workflow/my-tasks as SALES_STAFF → no INVENTORY_MANAGER tasks
- POST /workflow/tasks/{id}/complete as VIEWER → 403

## Tenant Isolation Tests — backend/tests/test_tenant_isolation.py

- Tenant A cannot read Tenant B's sales orders
- Tenant A cannot complete Tenant B's workflow tasks
- Tenant A cannot read Tenant B's invoices
- Tenant A cannot read Tenant B's workflow events

## E2E (if playwright is configured)

Use playwright plugin to test:
1. Login as SALES_STAFF → confirm sales order → logout → login as INVENTORY_MANAGER → My Tasks shows the PICK_ORDER task
2. VIEWER logs in → My Tasks nav item is not visible → no create buttons visible on any page

## Final run

Run all tests:
/warelyn-test-runner

Report: pass count, fail count, fix any failures.
Do not close this phase with failing tests.
```

---

---

## Phase Dependency Order

```
Phase 1 (Currency foundation)
    ↓
Phase 2 (Currency in documents/reports)
    ↓
Phase 3 (Workflow task engine)
    ↓
Phase 4 (Sales workflow automation)
    ↓
Phase 5 (Purchase workflow automation)
    ↓
Phase 6 (My Tasks UI + dashboard widgets)
    ↓
Phase 7 (RBAC audit — safe to run in parallel after Phase 3)
    ↓
Phase 8 (Testing — always last)
```

## Quick Skill Reference

| When | Use |
|---|---|
| Starting any session | `/dev-tools:project-health` |
| Before writing backend code | `pyright-lsp` active |
| Before writing frontend code | `typescript-lsp` active, `/frontend:react-patterns` |
| Before any migration | `/warelyn-db-migration-check` |
| After any API change | `/warelyn-api-contract-check` |
| Before workflow phases | `/warelyn-workflow-audit` |
| Phase 7 RBAC work | `/warelyn-rbac-audit` + `/warelyn-security-review` + `semgrep` |
| End of every phase | `/warelyn-test-runner` |
| Any failure | `/warelyn-debug-runbook` |
| After Phase 6 UI | `/dev-tools:ux-audit` + `/frontend:design-review` + `/dev-tools:responsiveness-check` |
| Before commits | `/dev-tools:git-workflow` + `code-review` |