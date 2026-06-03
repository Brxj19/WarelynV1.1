# Warelyn Inventory

**Inventory that moves with your business.**

Warelyn Inventory is a production-style inventory and warehouse operations platform for growing businesses to manage products, warehouses, stock movements, purchases, sales, returns, reports, and team operations from one SaaS workspace.

## Current Status

This repository has completed **Phase 14 - Communication, Verification, and Notifications Foundation**.

Related commits:

- Implementation: `dbd9752 implement Warelyn auth and tenant foundation`
- Planning alignment: `0137f69 update backlog with auth and tenant foundation phase`

The current implementation provides:

- FastAPI backend scaffold with health endpoint, settings, middleware, exception handling, database session setup, and Alembic foundation.
- `Tenant`, `User`, and `RefreshToken` models with roles, statuses, password hashing, JWT access tokens, JWT refresh tokens, login, registration, logout, refresh, and `auth/me` backend foundation.
- Tenant-scoped category, brand, vendor, customer, product, warehouse, and warehouse location master data APIs.
- Tenant-scoped `InventoryEngine`, stock ledger, warehouse stock projection, stock reservation foundation, idempotency, and reconciliation dry-run APIs.
- CSV product import with upload, validation, preview, commit, cancel, duplicate checks, tenant isolation, and barcode-ready product search.
- Tenant-scoped purchase orders, purchase order items, purchase receipts, partial receiving, and receipt commit through `InventoryEngine.stock_in()`.
- Batch, expiry, and serial traceability records for tracked products, with ledger references created by `InventoryEngine.stock_in()`.
- Tenant-scoped sales orders, explicit location-level sales reservation, reservation release, and fulfillment deduction through `InventoryEngine`.
- Tenant-scoped pick tasks, pick task items, explicit serial allocation during picking, optional batch allocation, packages, and package items.
- Tenant-scoped sales returns, return QC inspection, sellable return restock through `InventoryEngine.return_restock()`, and non-sellable blocked return stock records.
- Read-only reports for inventory summary, warehouse/location stock, stock movements, low stock, reorder suggestions, valuation, batch expiry, serial status, blocked stock, reconciliation, and operational dashboard KPIs.
- React + Vite + Tailwind frontend scaffold with layouts, catalog and warehouse pages, UI primitives, routing, and API client wrapper.
- Frontend auth shell with login, registration, protected routes, auth state, and authenticated dashboard placeholder.
- Product import UI with CSV dropzone, preview table, import modes, and reusable scanner-friendly barcode input.
- Purchase order, receiving, and receipt detail screens with warehouse/location receiving and committed stock impact.
- Purchase receiving fields for batch number, expiry, warranty, and serial capture on tracked products.
- Sales order, sales confirmation allocation, fulfillment draft, and fulfillment commit screens.
- Picking queue, pick task detail, sales pick, sales package, and package detail screens.
- Sales returns list, return creation, return detail, and QC/process screens.
- Reports pages and backend-driven operational dashboard widgets.
- Northstar-inspired Warelyn frontend polish with a dark topbar, white grouped sidebar, logo-backed branding, compact cards, clean table shells, standardized status/loading/empty/error states, and confirmation modals for stock-affecting workflow actions.
- Phase 11 hardening with additional regression tests, deployment readiness documentation, validation script, and minimal CI workflow.
- Phase 12 PRD gap audit and roadmap merge document.
- Phase 13 super admin console, settings foundation, and audit logs.
- Phase 14 communication, verification, and notifications foundation:
  - SMTP-based email service with MailHog dev server.
  - SMS dev outbox (no real provider integration).
  - OTP (one-time password) service with hashed code storage, expiry, consumption tracking, attempt limiting, and supersede-on-resend.
  - Email verification endpoint (send + confirm).
  - Phone verification endpoint (send + confirm).
  - Verification status API.
  - In-app notification model, service, and API.
  - Frontend toast notification system (success/error/warning/info).
  - Frontend notification center with bell icon and unread badge.
- Frontend verification pages and settings integration.
- MailHog SMTP service in Docker Compose for local email development.
- FAQ assistant popup plus standalone `/faq` page for tenant users.
- MySQL, backend, and frontend development services in Docker Compose.

Not implemented yet:

- Real SMS provider integration (Twilio, etc.).
- Real email provider integration (SendGrid, Mailgun, SES).
- Email/PDF template management.
- XLSX import and import column mapping UI.
- Vendor bills, supplier payments, invoice accounting, and purchase PDFs.
- Carrier shipment, invoice accounting, payment collection, refund accounting, credit notes, or carrier return pickup workflows.
- FEFO auto-allocation, expiry background jobs, package-mandatory fulfillment, and full mobile scanner workflow.
- Advanced role/user management screens.
- Forecasting, automatic purchase order creation, and supplier ordering automation.

## Next Phase

Next recommended phase: Phase 15 invoices/bills/PDFs or another approved phase.

Before adding later workflows, keep tenant context backend-derived from authenticated users and avoid passing arbitrary tenant IDs from normal tenant APIs. All stock mutation must continue through `InventoryEngine`; reports are read-only, query-based, and must not mutate stock, create ledger entries, or create purchase orders. Frontend pages must keep authoritative stock values backend-driven.

## Tech Stack

- Frontend: React, Vite, Tailwind CSS.
- Backend: Python, FastAPI, Pydantic Settings.
- Database: MySQL.
- ORM and migrations: SQLAlchemy, Alembic.
- Tests: Pytest.
- Local orchestration: Docker Compose.

## Folder Structure

```text
.
  docs/                         Planning and architecture docs
  logo/                         Brand assets
  backend/
    app/
      api/                      Root API router, health, auth, catalog, warehouse, inventory, import, purchase routes
      core/                     Settings, middleware, exceptions, security helpers
      db/                       SQLAlchemy Base and session setup
      dependencies/             Current user, role, tenant dependencies
      domain/                   Inventory engine domain logic
      models/                   Auth, tenant, catalog, warehouse, inventory, import, purchase models
      repositories/             Auth, tenant, catalog, warehouse, inventory, import, purchase DB access layer
      schemas/                  Auth, catalog, warehouse, inventory, import, purchase request/response schemas
      services/                 Auth, catalog, warehouse, inventory, import, purchase business services
      utils/                    Shared backend utilities
      main.py                   FastAPI app factory
    alembic/                    Migration environment
    tests/                      Backend tests
  frontend/
    src/
      app/                      React entry and app shell
      components/ui/            Reusable UI primitives
      layouts/                  App and auth layouts
      pages/                    Dashboard, auth, catalog, warehouse, purchase, sales, returns, and report pages
      routes/                   Route declarations
      services/                 Frontend API client wrappers
      hooks/                    Custom React hooks (useToast)
      context/                  React context providers (auth, toast)
      styles/                   Tailwind and app styles
```

## Local Setup

For step-by-step local and Docker instructions, see [runbook.md](./runbook.md).

Prerequisites:

- Python 3.11+
- Node.js 20+
- Docker and Docker Compose
- MySQL 8 if running without Docker

Backend setup:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Frontend setup:

```bash
cd frontend
npm install
cp .env.example .env
```

## Backend Commands

```bash
cd backend
.venv/bin/python -m compileall app
.venv/bin/python -m pytest
.venv/bin/alembic upgrade head
.venv/bin/python -m app.utils.seed_super_admin
.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Full validation helper:

```bash
./scripts/validate.sh
```

Deployment readiness notes are in `docs/DEPLOYMENT_READINESS.md`. `docker-compose.yml` is development-only and uses local credentials, bind mounts, and reload/dev servers.

Health check:

```bash
curl http://localhost:8000/api/health
```

Expected response:

```json
{
  "status": "ok",
  "service": "Warelyn Inventory API"
}
```

Auth endpoints:

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/refresh`
- `GET /api/auth/me`
- `POST /api/auth/logout`

Catalog endpoints:

- `GET|POST /api/catalog/categories`
- `PATCH /api/catalog/categories/{category_id}`
- `GET|POST /api/catalog/brands`
- `PATCH /api/catalog/brands/{brand_id}`
- `GET|POST /api/catalog/vendors`
- `PATCH /api/catalog/vendors/{vendor_id}`
- `GET|POST /api/catalog/customers`
- `PATCH /api/catalog/customers/{customer_id}`
- `GET|POST /api/catalog/products` with optional `?search=` by name, SKU, or barcode
- `PATCH /api/catalog/products/{product_id}`

Product import endpoints:

- `POST /api/imports/products/upload`
- `GET /api/imports/products/{job_id}`
- `GET /api/imports/products/{job_id}/rows`
- `POST /api/imports/products/{job_id}/validate`
- `POST /api/imports/products/{job_id}/commit`
- `POST /api/imports/products/{job_id}/cancel`

Purchase endpoints:

- `GET|POST /api/purchase-orders`
- `GET|PATCH /api/purchase-orders/{po_id}`
- `POST /api/purchase-orders/{po_id}/submit`
- `POST /api/purchase-orders/{po_id}/cancel`
- `POST /api/purchase-orders/{po_id}/close`
- `GET|POST /api/purchase-orders/{po_id}/receipts`
- `GET|PATCH /api/purchase-receipts/{receipt_id}`
- `POST /api/purchase-receipts/{receipt_id}/commit`
- `POST /api/purchase-receipts/{receipt_id}/cancel`

Sales endpoints:

- `GET|POST /api/sales-orders`
- `GET|PATCH /api/sales-orders/{order_id}`
- `POST /api/sales-orders/{order_id}/confirm`
- `POST /api/sales-orders/{order_id}/cancel`
- `POST /api/sales-orders/{order_id}/close`
- `GET|POST /api/sales-orders/{order_id}/fulfillments`
- `GET|PATCH /api/sales-fulfillments/{fulfillment_id}`
- `POST /api/sales-fulfillments/{fulfillment_id}/commit`
- `POST /api/sales-fulfillments/{fulfillment_id}/cancel`

Picking and packing endpoints:

- `GET /api/pick-tasks`
- `POST /api/sales-orders/{order_id}/pick-tasks`
- `GET /api/sales-orders/{order_id}/pick-tasks`
- `GET /api/pick-tasks/{pick_task_id}`
- `PATCH /api/pick-tasks/{pick_task_id}`
- `POST /api/pick-tasks/{pick_task_id}/start`
- `POST /api/pick-tasks/{pick_task_id}/pick`
- `POST /api/pick-tasks/{pick_task_id}/cancel`
- `POST /api/sales-orders/{order_id}/packages`
- `GET /api/sales-orders/{order_id}/packages`
- `GET /api/packages/{package_id}`
- `PATCH /api/packages/{package_id}`
- `POST /api/packages/{package_id}/pack`
- `POST /api/packages/{package_id}/cancel`

Warehouse endpoints:

- `GET|POST /api/warehouses`
- `PATCH /api/warehouses/{warehouse_id}`
- `GET|POST /api/warehouses/{warehouse_id}/locations`
- `PATCH /api/warehouses/{warehouse_id}/locations/{location_id}`

Inventory endpoints:

- `GET /api/inventory/stock`
- `GET /api/inventory/ledger`
- `GET /api/inventory/batches`
- `GET /api/inventory/batches/{batch_id}`
- `GET /api/inventory/serials`
- `GET /api/inventory/serials/{serial_id}`
- `GET /api/inventory/reconciliation/dry-run`
- `POST /api/inventory/stock-in`
- `POST /api/inventory/stock-out`
- `POST /api/inventory/adjust`
- `POST /api/inventory/reserve`
- `POST /api/inventory/reservations/{id}/release`
- `POST /api/inventory/reservations/{id}/deduct`
- `POST /api/inventory/transfer`

Report endpoints:

- `GET /api/dashboard/operations`
- `GET /api/reports/inventory-summary`
- `GET /api/reports/warehouse-stock`
- `GET /api/reports/location-stock`
- `GET /api/reports/stock-movements`
- `GET /api/reports/low-stock`
- `GET /api/reports/reorder-suggestions`
- `GET /api/reports/product-valuation`
- `GET /api/reports/batch-expiry`
- `GET /api/reports/serial-status`
- `GET /api/reports/blocked-stock`
- `GET /api/reports/reconciliation`

Required backend environment variables are listed in `backend/.env.example`, including JWT settings, SMTP settings, OTP settings, and optional super admin seed settings. Production deployments must override the example JWT secret, database credentials, CORS origins, debug setting, and super admin bootstrap values.

The email service uses `WARELYN_SMTP_*` settings. In development, it defaults to localhost:1025 (MailHog). When MailHog is not available, email delivery fails with a clean structured error. Tests use mock OTP services and do not require MailHog.

## Frontend Commands

```bash
cd frontend
npm install
npm run dev
npm run build
```

## Docker Commands

```bash
docker compose config
docker compose up --build
docker compose down
```

Development URLs:

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- MySQL: `localhost:3307`
- MailHog: `http://localhost:8025` (dev email viewer)

## Architecture Rules

- Routers stay thin and handle HTTP only.
- Services own business workflows.
- Repositories own database access.
- Backend enforces tenant isolation.
- Tenant ID for normal tenant business APIs must come from the authenticated user context, not arbitrary frontend input.
- `InventoryEngine` will be the only stock mutation path once inventory workflows begin.
- Phase 2 inventory mutation endpoints require idempotency keys and location-level stock dimensions.
- Product import does not call `InventoryEngine` because it does not mutate stock.
- Purchase receipt commit calls `InventoryEngine.stock_in()` and does not directly update stock tables.
- Sales confirmation and fulfillment call reservation/deduction methods on `InventoryEngine` and do not directly update stock tables.
- Frontend pages stay thin and call service/API wrappers.
- Frontend never calculates authoritative stock.
- OTP codes are hashed at rest using SHA-256; plaintext codes are never stored.
- OTPs expire after `WARELYN_OTP_EXPIRE_MINUTES` (default 10).
- Resending a verification code supersedes the previous active OTP.
- In-app notifications are user-scoped with tenant isolation.
- Toast notifications auto-dismiss after 4.5 seconds.
