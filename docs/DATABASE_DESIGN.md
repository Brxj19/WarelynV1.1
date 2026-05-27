# Warelyn Database Design

Source of truth: `docs/WARELYN_REAL_WORLD_V2_PRD.md` plus current Alembic migrations.

## Current Phase

Phase 14 communication, verification, and notifications foundation is complete. Phase 14 adds OTP verification, SMS dev outbox, and notification tables.

Related commits:

- Implementation: `dbd9752 implement Warelyn auth and tenant foundation`
- Planning alignment: `0137f69 update backlog with auth and tenant foundation phase`

Carrier shipment, invoice accounting, payment collection, refund accounting, credit notes, vendor bill/accounting, FEFO allocation, expiry jobs, full mobile scanner workflow, report snapshot tables, and advanced charting tables are not implemented yet. Product import is catalog-only and does not create stock projection, ledger, or reservation rows. Purchase receiving, sales fulfillment, and sellable return restock mutate stock only through `InventoryEngine`; picking, packing, reports, dashboards, and non-sellable return records do not mutate sellable stock.

Current implemented models:

- `Tenant`
- `User`
- `RefreshToken`
- `Category`
- `Brand`
- `Vendor`
- `Customer`
- `Product`
- `Warehouse`
- `WarehouseLocation`
- `WarehouseStock`
- `StockLedgerEntry`
- `StockReservation`
- `IdempotencyKey`
- `ImportJob`
- `ImportJobRow`
- `PurchaseOrder`
- `PurchaseOrderItem`
- `PurchaseReceipt`
- `PurchaseReceiptItem`
- `InventoryBatch`
- `InventorySerial`
- `SalesOrder`
- `SalesOrderItem`
- `SalesFulfillment`
- `SalesFulfillmentItem`
- `PickTask`
- `PickTaskItem`
- `Package`
- `PackageItem`
- `SalesReturn`
- `SalesReturnItem`
- `ReturnQCInspection`
- `BlockedReturnStock`
- `OTPVerification`
- `SMSOutbox`
- `Notification`

Next recommended work should remain deployment/readiness or explicitly approved product phases. All stock mutation must go through `InventoryEngine`.

Phase 9 added no tables or migrations. Phase 10, Phase 11, Phase 12, and Phase 13 also added no business tables or migrations. Reports and dashboard data are query-based over existing tenant-scoped tables.

Phase 14 adds three tables: `otp_verifications`, `sms_outbox`, and `notifications`.

## Migration Readiness

- Alembic migrations are ordered from auth/tenant foundation through returns QC/blocked stock foundation.
- `alembic upgrade head` must succeed against an empty MySQL database before deployment.
- Released migrations should be treated as append-only; do not rewrite shipped migration files.
- Tenant-owned tables should retain tenant-scoped indexes or unique constraints where business identity is tenant-specific.

## Tables

### `tenants`

Tenant workspace record.

Columns:

- `id` primary key
- `company_name` required
- `contact_email` required, indexed
- `phone` nullable
- `address` nullable
- `gst_number` nullable
- `business_type` nullable
- `status`: `ACTIVE`, `DISABLED`, `PENDING`, indexed
- `created_at`
- `updated_at`

### `users`

User identity record. Tenant users belong to one tenant. `SUPER_ADMIN` users have `tenant_id = null`.

Columns:

- `id` primary key
- `tenant_id` nullable foreign key to `tenants.id`, indexed
- `name` required
- `email` required, unique, indexed
- `phone` nullable
- `password_hash` required
- `role`: `SUPER_ADMIN`, `TENANT_ADMIN`, `INVENTORY_MANAGER`, `SALES_STAFF`, `PURCHASE_STAFF`, `VIEWER`, indexed
- `status`: `ACTIVE`, `DISABLED`, `INVITED`, indexed
- `email_verified_at` nullable
- `phone_verified_at` nullable
- `last_login_at` nullable
- `created_at`
- `updated_at`

### `refresh_tokens`

Stored refresh token records. Raw refresh tokens are never persisted; only SHA-256 token hashes are stored.

Columns:

- `id` primary key
- `user_id` required foreign key to `users.id`, indexed
- `token_hash` required, unique, indexed
- `expires_at` required, indexed
- `revoked_at` nullable
- `created_at`

### Catalog And Warehouse Master Data

Tenant-scoped master data tables added by `20260521_0002_catalog_warehouse_foundation.py`:

- `categories`: tenant, name, description, status, timestamps; unique `(tenant_id, name)`.
- `brands`: tenant, name, description, status, timestamps; unique `(tenant_id, name)`.
- `vendors`: tenant, name, email, phone, address, GST number, status, timestamps; unique `(tenant_id, name)`.
- `customers`: tenant, name, email, phone, address, GST number, status, timestamps; unique `(tenant_id, email)`.
- `products`: tenant, optional category/brand, name, SKU, barcode, description, unit, prices, reorder level, tracking flags, status, timestamps; unique `(tenant_id, sku)` and `(tenant_id, barcode)`.
- `warehouses`: tenant, name, code, address, status, timestamps; unique `(tenant_id, code)`.
- `warehouse_locations`: tenant, warehouse, optional parent location, code, name, barcode, location type, sort order, status, timestamps; unique `(tenant_id, warehouse_id, code)` and `(tenant_id, warehouse_id, barcode)`.

### Inventory Foundation

Tenant-scoped inventory tables added by `20260521_0003_inventory_engine_foundation.py`:

- `warehouse_stock`: tenant, product, warehouse, required location, on-hand quantity, reserved quantity, available quantity, updated timestamp; unique `(tenant_id, product_id, warehouse_id, location_id)`.
- `stock_ledger_entries`: immutable movement history with tenant, product, warehouse, required location, optional batch, optional serial, movement type, quantity/reserved/available deltas, reference, idempotency key, note, actor, and timestamp.
- `stock_reservations`: active/released/deducted reservation foundation with tenant, product, warehouse, required location, quantity, status, reference, actor, and timestamps.
- `idempotency_keys`: tenant-scoped mutation replay protection keyed by `(tenant_id, key, operation)` with request hash and stored response JSON.

### Product Import Foundation

Tenant-scoped import tables added by `20260521_0004_product_import_foundation.py`:

- `import_jobs`: tenant, creator, import type, filename, mode, status, row counts, created/updated/skipped counts, timestamps for validation, commit, cancellation, creation, and update.
- `import_job_rows`: tenant, job, CSV row number, raw row JSON, normalized row JSON, row status, errors JSON, warnings JSON, optional existing product, optional created product, and timestamps.

Import jobs and rows are scoped by `tenant_id`. They support preview and validation before commit. Product import commit creates or updates `products`, may create missing category, brand, or vendor master records when requested, and does not touch inventory stock tables.

### Purchase Receiving Foundation

Tenant-scoped purchase tables added by `20260521_0005_purchase_receiving_foundation.py`:

- `purchase_orders`: tenant, vendor, PO number, status, dates, notes, creator, workflow timestamps, and timestamps; unique `(tenant_id, po_number)`.
- `purchase_order_items`: tenant, purchase order, product, ordered quantity, received quantity, unit cost, notes, and timestamps.
- `purchase_receipts`: tenant, purchase order, receipt number, status, receiver, received/committed/cancelled timestamps, notes, and timestamps; unique `(tenant_id, receipt_number)`.
- `purchase_receipt_items`: tenant, receipt, purchase order item, product, warehouse, location, received quantity, unit cost, and timestamps.
- Phase 5 adds receipt item tracking fields: batch number, supplier batch number, manufacture date, expiry date, warranty date, and serial numbers JSON.

Purchase receipt commit updates `purchase_order_items.received_quantity` and purchase order status in the purchasing workflow transaction, while stock projection and ledger entries are created only through `InventoryEngine.stock_in()`.

### Batch, Expiry, And Serial Tracking Foundation

Tenant-scoped tracking tables added by `20260521_0006_batch_expiry_serial_foundation.py`:

- `inventory_batches`: tenant, product, warehouse, location, batch number, supplier batch number, manufacture date, expiry date, warranty date, quantities, status, and timestamps; unique `(tenant_id, product_id, warehouse_id, location_id, batch_number)`.
- `inventory_serials`: tenant, product, warehouse, location, optional batch, serial number, status, warranty date, expiry date, and timestamps; unique `(tenant_id, product_id, serial_number)`.

`warehouse_stock` remains location-level only with unique `(tenant_id, product_id, warehouse_id, location_id)`. Phase 5 does not add `batch_id` or `serial_id` to `warehouse_stock`.

### Sales Reservation And Fulfillment Foundation

Tenant-scoped sales tables added by `20260521_0007_sales_reservation_fulfillment_foundation.py`:

- `sales_orders`: tenant, customer, order number, status, order dates, notes, creator, workflow timestamps, and timestamps; unique `(tenant_id, order_number)`.
- `sales_order_items`: tenant, sales order, product, ordered quantity, reserved quantity, fulfilled quantity, unit price, notes, and timestamps.
- `sales_fulfillments`: tenant, sales order, fulfillment number, status, fulfiller, fulfilled/committed/cancelled timestamps, notes, and timestamps; unique `(tenant_id, fulfillment_number)`.
- `sales_fulfillment_items`: tenant, fulfillment, sales order item, product, warehouse, location, reservation, fulfilled quantity, and timestamps.

Sales confirmation creates `stock_reservations` and `SALES_RESERVE` ledger entries through `InventoryEngine.reserve_stock()`. Sales cancellation/close releases active reservations through `InventoryEngine.release_reservation()`. Fulfillment commit deducts reserved stock through `InventoryEngine.deduct_reserved_stock()`.

### Picking, Packing, And Serial Allocation Foundation

Tenant-scoped fulfillment operations tables added by `20260521_0008_picking_packing_serial_allocation_foundation.py`:

- `pick_tasks`: tenant, sales order, pick number, status, assignee, workflow timestamps, notes, creator, and timestamps; unique `(tenant_id, pick_number)`.
- `pick_task_items`: tenant, pick task, sales order item, reservation, product, warehouse, location, optional batch, optional serial, required quantity, picked quantity, status, and timestamps.
- `packages`: tenant, sales order, package number, status, packer, workflow timestamps, notes, and timestamps; unique `(tenant_id, package_number)`.
- `package_items`: tenant, package, pick task item, sales order item, product, optional batch, optional serial, quantity, and timestamps.

Picking and packing do not update `warehouse_stock`, `stock_reservations`, or `stock_ledger_entries`. Explicit serial allocation is stored on `pick_task_items.serial_id`; final serial status changes happen only during fulfillment deduction through `InventoryEngine.deduct_reserved_stock()`.

### Returns QC And Blocked Stock Foundation

Tenant-scoped return tables added by `20260521_0009_return_qc_blocked_stock_foundation.py`:

- `sales_returns`: tenant, sales order, return number, status, reason, notes, creator, submitted/inspected/processed/cancelled timestamps, and timestamps; unique `(tenant_id, return_number)`.
- `sales_return_items`: tenant, return, sales order item, product, warehouse, location, optional batch, optional serial, returned/accepted/rejected quantities, QC status, reason, notes, and timestamps.
- `return_qc_inspections`: tenant, return, inspector, inspected timestamp, notes, and timestamps.
- `blocked_return_stock`: tenant, return, return item, product, warehouse, location, optional batch, optional serial, quantity, non-sellable status, reason, notes, and timestamps.

Accepted sellable returns update `warehouse_stock` and write `RETURN_RESTOCK` ledger entries only through `InventoryEngine.return_restock()`. Blocked, damaged, and scrapped returns create `blocked_return_stock` records and do not increase sellable stock. Rejected returns do not mutate stock.

### Communication Foundation

Tenant-scoped communication tables added by `20260522_0011_communication_verification_notification.py`:

- `otp_verifications`: tenant, user, OTP source (EMAIL/PHONE), OTP purpose (EMAIL_VERIFICATION/PHONE_VERIFICATION), destination (email or phone), code hash, expiry datetime, consumed datetime, attempt count, superseded datetime, and timestamps. Indexed on `(user_id, purpose, destination)` for active OTP lookups and `expires_at` for cleanup.
- `sms_outbox`: tenant, user, phone number, message, status (PENDING/SENT/FAILED), error message, and timestamps. Logging-only table; no real SMS provider integration.
- `notifications`: tenant, user, notification type (INFO/SUCCESS/WARNING/ERROR/SYSTEM), category (AUTH/INVENTORY/PURCHASE/SALES/RETURNS/SYSTEM/VERIFICATION), title, message, is_read flag, and timestamps. Indexed on `(user_id, is_read, created_at)` for efficient unread queries.

OTP verification rules:
- Codes are stored as SHA-256 hashes via `hash_token()`.
- OTPs expire after `WARELYN_OTP_EXPIRE_MINUTES` (default 10).
- Attempt count increments on failed verification; reaching `WARELYN_OTP_MAX_ATTEMPTS` (default 5) blocks further attempts.
- Resend supersedes previous active OTPs for the same user/purpose/destination by setting `superseded_at`.
- A consumed OTP cannot be reused; `consumed_at` is set on successful verification.
- OTPs are user-scoped and cross-tenant isolated via `user_id`.

Notification rules:
- Notifications are user-scoped and tenant-scoped via `tenant_id`.
- Users can only read/mark their own notifications.
- Notification categories enable grouped filtering for different workflow areas.

## Enums

### `UserRole`

- `SUPER_ADMIN`
- `TENANT_ADMIN`
- `INVENTORY_MANAGER`
- `SALES_STAFF`
- `PURCHASE_STAFF`
- `VIEWER`

### `TenantStatus`

- `ACTIVE`
- `DISABLED`
- `PENDING`

### `UserStatus`

- `ACTIVE`
- `DISABLED`
- `INVITED`

### `RecordStatus`

- `ACTIVE`
- `INACTIVE`
- `ARCHIVED`

### `LocationType`

- `STORAGE`
- `PICKING`
- `RECEIVING`
- `PACKING`
- `SHIPPING`
- `RETURN`
- `DAMAGED`
- `EXPIRED`
- `QUARANTINE`
- `QC`
- `SCRAP`
- `VIRTUAL`

### `MovementType`

- `STOCK_IN`
- `STOCK_OUT`
- `ADJUSTMENT_IN`
- `ADJUSTMENT_OUT`
- `SALES_RESERVE`
- `SALES_RELEASE`
- `SALES_DEDUCT`
- `RETURN_RESTOCK`
- `TRANSFER_OUT`
- `TRANSFER_IN`
- `CYCLE_COUNT_ADJUSTMENT`

### `ReservationStatus`

- `ACTIVE`
- `RELEASED`
- `DEDUCTED`
- `CANCELLED`

### `ReferenceType`

- `MANUAL`
- `PURCHASE_RECEIPT`
- `SALES_ORDER`
- `SALES_RETURN`
- `TRANSFER`
- `ADJUSTMENT`
- `RECONCILIATION`

### `ImportJobStatus`

- `UPLOADED`
- `VALIDATING`
- `VALIDATED`
- `HAS_ERRORS`
- `COMMITTED`
- `CANCELLED`

### `ImportRowStatus`

- `PENDING`
- `VALID`
- `ERROR`
- `WARNING`
- `SKIPPED`
- `CREATED`
- `UPDATED`

### `ProductImportMode`

- `create_only`
- `update_existing`
- `upsert`

### `PurchaseOrderStatus`

- `DRAFT`
- `SUBMITTED`
- `PARTIALLY_RECEIVED`
- `RECEIVED`
- `CANCELLED`
- `CLOSED`

### `PurchaseReceiptStatus`

- `DRAFT`
- `COMMITTED`
- `CANCELLED`

### `InventoryBatchStatus`

- `ACTIVE`
- `QC_HOLD`
- `DAMAGED`
- `EXPIRED`
- `QUARANTINE`
- `SCRAPPED`

### `InventorySerialStatus`

- `IN_STOCK`
- `RESERVED`
- `SOLD`
- `DAMAGED`
- `SCRAPPED`
- `RETURNED`
- `QC_HOLD`

### `SalesOrderStatus`

- `DRAFT`
- `CONFIRMED`
- `PARTIALLY_FULFILLED`
- `FULFILLED`
- `CANCELLED`
- `CLOSED`

### `SalesFulfillmentStatus`

- `DRAFT`
- `COMMITTED`
- `CANCELLED`

### `PickTaskStatus`

- `PENDING`
- `IN_PROGRESS`
- `PICKED`
- `CANCELLED`

### `PickTaskItemStatus`

- `PENDING`
- `PICKED`
- `CANCELLED`

### `PackageStatus`

- `DRAFT`
- `PACKED`
- `CANCELLED`

### `SalesReturnStatus`

- `DRAFT`
- `SUBMITTED`
- `INSPECTION_PENDING`
- `PARTIALLY_PROCESSED`
- `PROCESSED`
- `CANCELLED`

### `SalesReturnItemStatus`

- `PENDING`
- `ACCEPTED_RESTOCK`
- `ACCEPTED_BLOCKED`
- `DAMAGED`
- `SCRAPPED`
- `REJECTED`

### `BlockedReturnStockStatus`

- `QC_HOLD`
- `QUARANTINE`
- `DAMAGED`
- `SCRAPPED`

### `OTPSource`

- `EMAIL`
- `PHONE`

### `OTPPurpose`

- `EMAIL_VERIFICATION`
- `PHONE_VERIFICATION`

### `SMSOutboxStatus`

- `PENDING`
- `SENT`
- `FAILED`

### `NotificationType`

- `INFO`
- `SUCCESS`
- `WARNING`
- `ERROR`
- `SYSTEM`

### `NotificationCategory`

- `AUTH`
- `INVENTORY`
- `PURCHASE`
- `SALES`
- `RETURNS`
- `SYSTEM`
- `VERIFICATION`

## Migration

Current migration:

- `backend/alembic/versions/20260521_0001_auth_tenant_foundation.py`
- `backend/alembic/versions/20260521_0002_catalog_warehouse_foundation.py`
- `backend/alembic/versions/20260521_0003_inventory_engine_foundation.py`
- `backend/alembic/versions/20260521_0004_product_import_foundation.py`
- `backend/alembic/versions/20260521_0005_purchase_receiving_foundation.py`
- `backend/alembic/versions/20260521_0006_batch_expiry_serial_foundation.py`
- `backend/alembic/versions/20260521_0007_sales_reservation_fulfillment_foundation.py`
- `backend/alembic/versions/20260521_0008_picking_packing_serial_allocation_foundation.py`
- `backend/alembic/versions/20260521_0009_return_qc_blocked_stock_foundation.py`
- `backend/alembic/versions/20260522_0011_communication_verification_notification.py`

Apply migrations:

```bash
cd backend
.venv/bin/alembic upgrade head
```

Seed a platform super admin from environment variables:

```bash
cd backend
.venv/bin/python -m app.utils.seed_super_admin
```

For local validation without MySQL, tests create an isolated in-memory SQLite database from SQLAlchemy metadata.

## Tenant Isolation Foundation

- Tenant-owned business tables added in later phases must include `tenant_id` unless explicitly documented as platform-global.
- Normal tenant APIs must resolve `tenant_id` from authenticated user context.
- Future tenant-owned modules must derive `tenant_id` from authenticated user context.
- `users.email` is globally unique in this foundation to simplify login and avoid cross-tenant ambiguity.
- Repository methods for future business tables should require tenant context by default.
- Catalog and warehouse master data use tenant-scoped repository helpers and tenant-scoped unique constraints.
- Inventory stock records are tenant-scoped and location-scoped. `InventoryEngine` is the only allowed stock mutation path.
- `warehouse_stock.quantity_available` is a projection that must equal `quantity_on_hand - quantity_reserved` in Phase 2.
- Product import records are tenant-scoped and catalog-only. Import commit must not write `warehouse_stock`, `stock_ledger_entries`, or `stock_reservations`.
- Purchase records are tenant-scoped. Receipt commit must call `InventoryEngine.stock_in()` and write ledger rows with `PURCHASE_RECEIPT` reference type.
- Return records are tenant-scoped. Sellable return restock must call `InventoryEngine.return_restock()` and write ledger rows with `SALES_RETURN` reference type; non-sellable return stock must remain in `blocked_return_stock` and outside sellable `warehouse_stock`.
