# Warelyn V2 Module Boundaries

Source of truth: `docs/WARELYN_REAL_WORLD_V2_PRD.md`.

## Current Repo State

- This checkout has a runnable FastAPI backend under `backend/` and React/Vite frontend under `frontend/`.
- Phase 0 foundation, Phase 1A auth/tenant foundation, Phase 1B catalog/warehouse foundation, Phase 2 InventoryEngine/stock ledger foundation, Phase 3 product import/barcode-ready catalog, Phase 4 purchase receiving workflow, Phase 5 batch/expiry/serial tracking foundation, Phase 6 sales reservation/fulfillment foundation, Phase 7 picking/packing/serial allocation foundation, Phase 8 returns QC/blocked stock foundation, Phase 9 reports/reorder/dashboard foundation, Phase 10 frontend workflow polish, Phase 11 regression/deployment readiness, Phase 12 PRD gap audit, Phase 13 super admin settings/audit logs, and Phase 14 communication/verification/notifications foundation are implemented.
- Current implemented business foundations include tenant-scoped products, warehouses, warehouse locations, warehouse stock projection, stock ledger entries, stock reservations, idempotency keys, reconciliation dry-run, product import jobs, product import rows, purchase orders, purchase receipts, inventory batches, inventory serials, sales orders, sales fulfillments, pick tasks, pick task items, packages, package items, sales returns, return QC inspections, blocked return stock, read-only operational reports, super admin settings, audit logs, OTP verifications, SMS outbox, and notifications.
- The structure below remains the target direction for future modules; some current paths are flatter while the codebase is built progressively.

## Target Backend Folder Structure

```text
backend/app/
  api/
    routers/
      auth.py
      tenants.py
      catalog.py
      warehouses.py
      inventory.py
      purchasing.py
      receiving.py
      sales.py
      fulfillment.py
      returns.py
      documents.py
      reports.py
      imports.py
      notifications.py
      audit.py
  core/
    config.py
    database.py
    errors.py
    security.py
    permissions.py
    pagination.py
    idempotency.py
  domain/
    inventory/
      engine.py
      ledger.py
      reservation_service.py
      allocation_service.py
      picking_strategy.py
      reconciliation.py
      exceptions.py
    purchasing/
      purchase_order_service.py
      receiving_service.py
    sales/
      sales_order_service.py
      fulfillment_service.py
      return_service.py
    catalog/
      product_service.py
      import_service.py
    documents/
      pdf_service.py
      email_document_service.py
  repositories/
    base.py
    product_repository.py
    warehouse_repository.py
    stock_repository.py
    order_repository.py
    report_repository.py
  models/
  schemas/
  events/
    event_bus.py
    event_types.py
    outbox.py
  jobs/
    expire_batches.py
    reorder_suggestions.py
    send_email.py
    cleanup_otp.py
  services/
    email_service.py
    sms_service.py
    otp_service.py
  cli/
    seed_from_csv.py
    reconcile_inventory.py
    create_demo_data.py
```

## Target Frontend Folder Structure

```text
frontend/src/
  app/
    routes.jsx
    providers.jsx
  api/
    client.js
    authApi.js
    catalogApi.js
    warehouseApi.js
    inventoryApi.js
    purchasingApi.js
    salesApi.js
    reportsApi.js
    importsApi.js
  modules/
    auth/
    dashboard/
    catalog/
    warehouses/
    inventory/
    purchasing/
    sales/
    fulfillment/
    returns/
    documents/
    reports/
    admin/
  components/
    common/
    layout/
    forms/
    tables/
    feedback/
    scanner/
  hooks/
  stores/
  utils/
  styles/
```

## Separation Of Concerns Rules

- Routers handle HTTP concerns only: paths, request schemas, current user, dependencies, service calls, response schemas.
- Services coordinate business workflows, permissions beyond route-level checks, transactions, events, audit logs, and repository calls.
- Repositories own database access, tenant filters, row locks, query shape, and persistence details.
- Domain engines enforce business invariants that must not be duplicated across services.
- Models define persistence shape, constraints, indexes, and relationships; they do not own workflow decisions.
- Schemas define public request/response contracts; they do not import ORM query logic or domain algorithms.
- Events record side effects; jobs process asynchronous or scheduled work such as expired stock and reorder suggestions.
- Frontend pages orchestrate UI state and call hooks/services; they do not own backend business decisions.
- Frontend API clients are grouped by module and hide transport details from pages and reusable components.
- Reusable UI components are presentation-first and must not know inventory workflow rules.
- Regression tests and deployment scripts must validate existing behavior only; they must not introduce alternate stock mutation paths or background business workflows.

## Backend Boundaries

### Routers

Routers may:

- Define endpoint paths and HTTP methods.
- Parse and validate request schemas.
- Read authenticated user and tenant context.
- Call one service or explicit use-case method.
- Convert known domain errors into structured API errors.
- Return response schemas.

Routers must not:

- Directly mutate stock.
- Contain pricing, reservation, allocation, picking, receiving, or return QC calculations.
- Build complex ORM queries inline.
- Bypass tenant isolation checks.
- Emit audit logs without the service/domain workflow that caused them.

### Services

Services may:

- Coordinate one business use case such as confirm order, receive purchase order, commit import, or complete return QC.
- Validate permissions and workflow transitions.
- Open and commit database transactions through the app's chosen transaction pattern.
- Call repositories and domain engines.
- Emit domain events, notifications, and audit logs.
- Enforce idempotency for critical actions.

Services must not:

- Reimplement stock math owned by `InventoryEngine`.
- Return raw database models directly to API callers unless the router/schema layer is designed for that.
- Hide cross-tenant reads or writes behind convenience helpers.

### Repositories

Repositories may:

- Encapsulate SQLAlchemy queries and persistence operations.
- Apply tenant filters by default for tenant-owned data.
- Use row locks where stock or workflow state can be concurrently mutated.
- Return model objects or persistence DTOs to services.

Repositories must not:

- Decide business workflow transitions.
- Decide whether a stock mutation is allowed.
- Create ledger entries without being called by `InventoryEngine` or its collaborators.

### Models

Models may:

- Define tables, columns, relationships, indexes, and constraints.
- Represent tenant-owned persistence with `tenant_id` where required.
- Carry enum fields for workflow state.

Models must not:

- Contain HTTP concerns.
- Contain user-interface concerns.
- Mutate inventory quantities through model helper methods that bypass `InventoryEngine`.

### Schemas

Schemas may:

- Validate input shape.
- Define response shape.
- Document API contracts.
- Carry explicit action request objects such as `ReceivePurchaseRequest` or `ReserveStockRequest`.

Schemas must not:

- Import repositories.
- Query the database.
- Calculate true available stock.

## Frontend Boundaries

### Pages

Pages may:

- Compose module-level UI.
- Read route params.
- Call module hooks or API services.
- Render loading, empty, error, and success states.
- Present confirmation dialogs for destructive or stock-changing actions.

Pages must not:

- Calculate authoritative stock numbers.
- Decide whether stock can be reserved, deducted, restocked, or transferred.
- Embed raw API URLs throughout the component tree.
- Duplicate workflow state machines that belong on the backend.

### Components

Components may:

- Render forms, tables, cards, status badges, scanner inputs, and shared layout.
- Receive data and callbacks through props.
- Provide reusable interaction patterns.

Components must not:

- Call unrelated module APIs directly.
- Know tenant authorization rules beyond displaying already-authorized actions.
- Contain inventory mutation rules.

### API Clients

API clients may:

- Centralize endpoint paths by module.
- Attach auth headers and request IDs through a shared client.
- Normalize transport errors into frontend-friendly errors.
- Keep request and response shapes close to backend schemas.

API clients must not:

- Patch over backend workflow bugs with frontend-only calculations.
- Silently swallow failed stock-changing requests.

## Tenant Isolation Rules

- Every tenant-owned table must include `tenant_id` unless there is a documented exception for global platform data.
- Every tenant-owned repository query must filter by tenant context by default.
- Natural keys such as SKU, barcode, warehouse code, and location code must be unique per tenant, not globally, unless explicitly required.
- Backend permissions remain authoritative even if frontend hides actions by role.
- Audit logs must include tenant context for tenant actions.
- Cross-tenant reads are platform-admin-only and must be explicit in service method names and authorization checks.
- Tests for every module must include at least one cross-tenant access denial case.

## Auth And Tenant Foundation Boundary

`Phase 1A - Auth and Tenant Foundation` is a prerequisite for all tenant-owned business modules.

This phase owns:

- Tenant model, tenant status, and tenant admin registration.
- User model, roles, statuses, and password hashing.
- JWT access tokens, JWT refresh tokens, refresh token hashing, refresh, logout, login, and `auth/me`.
- Backend protected dependencies: `get_current_user`, `get_current_user_context`, `require_roles()`, `require_tenant_user()`, and `require_super_admin()`.
- Frontend auth shell, protected routes, guest route behavior, and role-aware navigation foundation.

Product CRUD, warehouse CRUD, inventory engine, stock ledger, purchase workflow, sales workflow, returns workflow, and reports must wait for this phase because they need backend-derived tenant context, active tenant/user checks, and role enforcement. Tenant users must not pass arbitrary `tenant_id` for normal business APIs; routers and services should derive tenant scope from the authenticated user context.

## InventoryEngine Ownership Rules

- `InventoryEngine` is the only backend module allowed to change stock quantities or stock state.
- Stock in/out, adjustment, reservation, reservation release, reserved deduction, transfer, purchase receiving, sales delivery, sellable return restock, and future expired stock, quarantine, and reconciliation fixes must call `InventoryEngine`.
- Product import is catalog-only in Phase 3 and must not call `InventoryEngine`, create stock projection rows, create ledger entries, or create reservations.
- Purchase receipt commit is the only purchase workflow in Phase 4 that mutates stock, and it must call `InventoryEngine.stock_in()`.
- Phase 5 batch quantity updates, serial creation, and ledger `batch_id`/`serial_id` references are owned by `InventoryEngine.stock_in()`.
- Purchasing may persist draft receipt tracking fields, but it must not create `inventory_batches`, create `inventory_serials`, or update batch/serial quantities directly.
- `warehouse_stock` remains location-level in Phase 5; do not add batch or serial stock projection writes outside the engine.
- Phase 6 sales confirmation must reserve stock through `InventoryEngine.reserve_stock()` only; sales cancellation/close must release through `InventoryEngine.release_reservation()` only; fulfillment commit must deduct through `InventoryEngine.deduct_reserved_stock()` only.
- Sales services may coordinate order and fulfillment state, but must not directly mutate `warehouse_stock`, `stock_reservations`, or `stock_ledger_entries` outside the engine path.
- Phase 8 accepted sellable returns must restock through `InventoryEngine.return_restock()` only. Blocked, damaged, and scrapped returns create `blocked_return_stock` and must not increase sellable `warehouse_stock`.
- Every `InventoryEngine` sellable stock quantity mutation must create a stock ledger entry. Non-sellable return records are not ledger projection entries.
- Important stock mutations must create audit logs and notifications where appropriate.
- Services may orchestrate inventory use cases, but they must delegate stock math and persistence updates to `InventoryEngine`.
- Frontend screens may preview expected stock impact, but the backend response is the source of truth after mutation.
- Reports are read-only query workflows. They must not call `InventoryEngine` mutation methods, update stock projection, create stock ledger entries, or create purchase orders.

## Anti-Patterns To Avoid

- Building V2 as independent CRUD screens without workflow ownership.
- Updating `warehouse_stock` directly from routers, repositories, models, scripts, or frontend requests.
- Treating `warehouse_stock` as the only source of truth without immutable ledger entries.
- Calculating true available stock only in the frontend.
- Implementing tenant checks only in routers while repositories can still read cross-tenant rows.
- Mixing SQLAlchemy query logic into schemas or React components.
- Adding subscription, billing, payment, marketplace, carrier, forecasting, full accounting, or native mobile work during early V2 foundation phases.
- Rewriting the app from scratch instead of building progressively from verified boundaries.
- Adding migrations before the target models and workflow ownership are clear.
- Creating broad generic services that know every module's details.

## Future Module Ownership Table

| Module | Backend Owner | Frontend Owner | Primary Data | Stock Mutation Allowed | Notes |
|---|---|---|---|---|---|
| Auth | `api/routers/auth.py`, auth service, security core | `modules/auth`, `api/authApi.js` | users, tokens, OTP | No | Keep JWT and tenant context explicit. OTP verification service lives in `services/otp_service.py`. |
| Tenants/Admin | tenant service, permission core | `modules/admin` | tenants, users, roles | No | Platform admin access must be explicit. |
| Catalog | `domain/catalog`, product repository | `modules/catalog`, `api/catalogApi.js` | products, categories, brands, units | No | Product master does not represent stock location. |
| Product Import | import service, imports router | catalog/import page and import service | import jobs, import rows, products | No in Phase 3 | Preview/validation before commit; catalog-only CSV import. |
| Warehouses | warehouse service/repository | `modules/warehouses`, `api/warehouseApi.js` | warehouses, locations/bins | No direct mutation | Location movement uses inventory engine. |
| Inventory | `domain/inventory/engine.py`, stock repository | `modules/inventory`, `api/inventoryApi.js` | stock projection, ledger, batches, serials | Yes, only via `InventoryEngine` | Core correctness module. |
| Purchasing | purchasing and receiving services | purchase pages and purchasing service | purchase orders, purchase receipts | Via `InventoryEngine.stock_in()` in Phase 4+ | PO status alone must not increase stock; receipt tracking fields are forwarded to the engine; bills/accounting are future work. |
| Sales | sales order service | sales pages and sales service | sales orders, customers | Via reservation engine methods | Confirmation uses explicit location-level allocation; serial selection happens in picking. |
| Fulfillment | fulfillment service, picking strategy | sales fulfillment pages and service | sales fulfillments, pick tasks, packages | Via reservation/deduction engine methods | Picking and packing do not mutate stock; fulfillment commit deducts reserved stock. |
| Returns | return service | returns pages and returns service | sales returns, return QC, blocked return stock | Via return/QC engine methods | Sellable restock goes through the engine; blocked/damaged/scrapped returns remain non-sellable. |
| Documents | document services | `modules/documents` | invoices, bills, PDFs | No | Document generation must reflect committed workflow state. |
| Reports | report repository/service | `modules/reports`, `api/reportsApi.js` | projections, ledger, audit | No | Reports read ledger/projections; no mutation. |
| Notifications | notification service/jobs | feedback components, notification UI | notifications, outbox | No | Trigger from domain events or services. In-app notifications stored in `notifications` table with user-scoped isolation. |
| Audit | audit service/repository | audit tabs/activity views | audit logs | No | Critical workflows must record actor and tenant. |
