# Warelyn V2 Inventory Engine Specification

Source of truth: `docs/WARELYN_REAL_WORLD_V2_PRD.md`.

## Purpose

`InventoryEngine` is the single backend authority for stock mutation in Warelyn V2. It protects inventory correctness by centralizing stock math, tenant isolation, idempotency, row locking, ledger writes, audit logs, and operational notifications.

Any workflow that changes stock must call `InventoryEngine`, including purchase receiving, stock in/out, adjustment, reservation, reservation release, delivery deduction, transfer, returns QC, damaged stock, expired stock, quarantine, scrap, and reconciliation fixes.

Product import is catalog-only in Phase 3. It creates or updates product master data and must not call `InventoryEngine`, create `warehouse_stock`, create `stock_ledger_entries`, or create `stock_reservations`.

Purchase receiving is implemented in Phase 4 through purchase receipt commit. Commit calls `InventoryEngine.stock_in()` for accepted receipt quantities, uses `STOCK_IN` movement entries with `PURCHASE_RECEIPT` reference type, and must not directly update stock projection or ledger rows outside the engine.

Phase 5 adds batch, expiry, and serial tracking foundation to `InventoryEngine.stock_in()`. The engine validates tracking fields, updates batch quantities, creates serial rows, and writes `batch_id`/`serial_id` ledger references during inbound stock. Purchasing stores draft tracking input, but batch and serial records are created only on receipt commit through the engine.

Phase 6 adds sales reservation and fulfillment foundation. Sales confirmation calls `InventoryEngine.reserve_stock()`, sales cancellation/close calls `InventoryEngine.release_reservation()`, and fulfillment commit calls `InventoryEngine.deduct_reserved_stock()`. Sales services own sales workflow state but do not directly mutate `warehouse_stock`, `stock_reservations`, or `stock_ledger_entries` outside the engine.

Phase 7 adds picking, packing, and explicit serial allocation foundation. Pick task creation, picking, package creation, and packing do not mutate `warehouse_stock`, do not release reservations, and do not create stock ledger entries. Serial-tracked sales reservations must be split into one-unit reservation lines; picking stores the selected `serial_id`, and fulfillment commit passes that allocation into `InventoryEngine.deduct_reserved_stock()`, which marks the serial as `SOLD` while deducting reserved stock. Package data remains optional before fulfillment in Phase 7.

Phase 8 adds returns QC and blocked return stock foundation. Sellable accepted returns call `InventoryEngine.return_restock()` and create `RETURN_RESTOCK` ledger entries with `SALES_RETURN` references. Blocked, damaged, and scrapped returns call return-specific engine methods that update serial state where applicable and create `blocked_return_stock` records; they do not increase `warehouse_stock` and do not create stock ledger projection entries. Rejected returns do not call inventory mutation methods.

Phase 9 adds read-only reports and operational dashboard queries. Reports may read `warehouse_stock`, `stock_ledger_entries`, batches, serials, returns, purchases, sales, picking, and packages, but they must not call `InventoryEngine` mutation methods, update projections, create ledger entries, or create purchase orders.

Phase 10 and Phase 11 add frontend polish, regression coverage, deployment readiness, validation scripts, and CI only. They do not add stock mutation behavior or change the `InventoryEngine` authority boundary.

## Required Public Methods

```python
class InventoryEngine:
    def stock_in(...): ...
    def stock_out(...): ...
    def adjust_stock(...): ...
    def reserve_stock(...): ...
    def release_reservation(...): ...
    def deduct_reserved_stock(...): ...
    def receive_purchase_order(...): ...
    def transfer_stock(...): ...
    def return_restock(...): ...
    def record_return_blocked(...): ...
    def record_return_damaged(...): ...
    def record_return_scrap(...): ...
    def mark_damaged(...): ...
    def mark_expired(...): ...
    def reconcile_stock(...): ...
```

## Stock Invariants

- `quantity_on_hand >= 0`.
- `quantity_reserved >= 0`.
- `quantity_reserved <= quantity_on_hand`.
- `quantity_available = quantity_on_hand - quantity_reserved - blocked_quantities`.
- Blocked quantities include damaged, expired, quarantine, QC hold, scrapped, lost, and any future non-sellable state.
- Stock cannot be deducted below available quantity unless a documented tenant/admin setting explicitly allows negative stock.
- Every stock mutation creates at least one immutable stock ledger entry.
- Every important stock mutation creates an audit log.
- Stock changes happen inside database transactions.
- Rows that can be concurrently mutated are locked before validation and update.
- Tenant boundaries are never crossed.
- Critical actions are idempotent when called with the same idempotency key.

## Stock States

Core states:

- `ON_HAND`
- `AVAILABLE`
- `RESERVED`
- `IN_TRANSIT`
- `QC_HOLD`
- `DAMAGED`
- `EXPIRED`
- `QUARANTINE`
- `RETURNED`
- `SCRAPPED`
- `LOST`

`AVAILABLE` is a derived sellable state, not a separate source of truth. It must be calculated from current projection fields and blocked quantities.

## Stock Ledger Design

`stock_ledger_entries` is the immutable source of stock movement history.

Target fields:

- `id`
- `tenant_id`
- `product_id`
- `warehouse_id`
- `location_id` nullable
- `batch_id` nullable, implemented in Phase 5
- `serial_id` nullable, implemented in Phase 5
- `movement_type`
- `quantity_delta`
- `reserved_delta`
- `available_delta`
- `reference_type`
- `reference_id`
- `idempotency_key`
- `note`
- `created_by`
- `created_at`

Movement types:

- `STOCK_IN`
- `STOCK_OUT`
- `ADJUSTMENT_IN`
- `ADJUSTMENT_OUT`
- `PURCHASE_RECEIVE`
- `SALES_RESERVE`
- `SALES_RELEASE`
- `SALES_DEDUCT`
- `TRANSFER_OUT`
- `TRANSFER_IN`
- `RETURN_RECEIVED`
- `RETURN_RESTOCKED`
- `DAMAGE_OUT`
- `EXPIRE_OUT`
- `SCRAP_OUT`
- `QC_HOLD`
- `QC_RELEASE`
- `CYCLE_COUNT_ADJUSTMENT`

Implemented enum names currently include `STOCK_IN`, `STOCK_OUT`, `ADJUSTMENT_IN`, `ADJUSTMENT_OUT`, `SALES_RESERVE`, `SALES_RELEASE`, `SALES_DEDUCT`, `RETURN_RESTOCK`, `TRANSFER_OUT`, `TRANSFER_IN`, and `CYCLE_COUNT_ADJUSTMENT`. Product import, reports, dashboard reads, picking, packing, and non-sellable return records must not create ledger entries.

Ledger rules:

- Ledger entries are append-only.
- Corrections are represented by new entries, not edits to old entries.
- Every entry must include tenant, product, warehouse, actor, timestamp, movement type, and reference.
- Reference fields must identify the workflow that caused the movement, such as purchase receive, sales order, package, return, transfer, or cycle count.
- Idempotent requests must not duplicate ledger entries.

## Warehouse Stock Projection Design

`warehouse_stock` is a fast current-state projection used by APIs and reports. It must reconcile with ledger totals.

Implemented Phase 5 fields:

- `id`
- `tenant_id`
- `product_id`
- `warehouse_id`
- `location_id`
- `quantity_on_hand`
- `quantity_reserved`
- `quantity_available`
- `updated_at`

Current Phase 5 projection rules:

- `warehouse_stock` remains location-level only with unique `(tenant_id, product_id, warehouse_id, location_id)`.
- Phase 5 does not add `batch_id` or `serial_id` to `warehouse_stock`.
- Batch and serial traceability is represented by `inventory_batches`, `inventory_serials`, and ledger references.

Future target fields:

- `id`
- `tenant_id`
- `product_id`
- `warehouse_id`
- `location_id` nullable for warehouse-level summaries or required for bin-level rows once locations are enabled
- `batch_id` nullable
- `serial_id` nullable
- `quantity_on_hand`
- `quantity_reserved`
- `quantity_available`
- `quantity_in_transit`
- `quantity_qc_hold`
- `quantity_damaged`
- `quantity_expired`
- `quantity_quarantine`
- `updated_at`

Projection rules:

- Projection rows are updated only by `InventoryEngine`.
- Projection updates and ledger inserts happen in the same transaction.
- Projection values must never be negative unless a future explicit negative-stock setting allows a documented exception.
- Projection rows must be lockable by tenant, product, warehouse, location, batch, and serial dimensions.

## Warehouse Location/Bin Design

`warehouse_locations` models physical and virtual places where stock can exist.

Target fields:

- `id`
- `tenant_id`
- `warehouse_id`
- `parent_location_id` nullable
- `code`
- `name`
- `barcode`
- `location_type`
- `status`
- `sort_order`

Location types:

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

Location rules:

- Locations belong to one tenant and one warehouse.
- Location codes and barcodes are unique per tenant/warehouse.
- Receiving, QC, damaged, expired, quarantine, scrap, packing, and shipping locations can be operational holding states.
- Transfers between locations are stock movements and must create ledger entries.

## Batch, Lot, Expiry, And Serial Design

`inventory_batches` tracks grouped stock for products that require lot or expiry traceability.

Target batch fields:

- `id`
- `tenant_id`
- `product_id`
- `warehouse_id`
- `location_id` nullable
- `batch_number`
- `supplier_batch_number` nullable
- `manufacture_date` nullable
- `expiry_date` nullable
- `warranty_until` nullable
- `quantity_on_hand`
- `quantity_available`
- `quantity_reserved`
- `status`

`inventory_serials` tracks individually identifiable units.

Target serial fields:

- `id`
- `tenant_id`
- `product_id`
- `warehouse_id`
- `location_id`
- `batch_id` nullable
- `serial_number`
- `status`
- `warranty_until` nullable
- `expires_on` nullable

Batch and serial rules:

- Products with batch tracking require batch assignment on receive before stock becomes usable.
- Products with expiry tracking require expiry date on receive and should support FEFO picking.
- Products with serial tracking require serial capture for each unit at receive, reservation, pick, pack, delivery, and return.
- Phase 5 implements serial capture only on stock-in/receiving; reservation, pick, pack, delivery, and return serial capture remain future work.
- Serial-tracked stock-in creates one ledger entry per serial with quantity `1` and `serial_id`.
- Batch/expiry non-serial stock-in creates one ledger entry with `batch_id`.
- Untracked products reject tracking fields.
- Expired batches cannot be reserved for normal sales.
- Damaged, expired, quarantine, and QC-held batch/serial stock is blocked from available quantity.
- Expired/damaged/quarantine/QC blocked-state enforcement is future work beyond the Phase 5 foundation.

## Reservation Rules

- Sales confirmation reserves stock; it does not physically deduct stock.
- Phase 6 confirmation requires explicit location-level allocation lines and does not auto-pick warehouse/location.
- Reservations create `stock_reservations` rows and `SALES_RESERVE` ledger entries.
- Reservations reduce `quantity_available` and increase `quantity_reserved`.
- Reservations can target warehouse, location, batch, or serial when allocation is known.
- Reservations can be released before delivery, creating `SALES_RELEASE` ledger entries.
- Reservations convert to physical deduction during delivery through `deduct_reserved_stock()`.
- Reservation release and deduction must be idempotent.
- Reservation cannot exceed available sellable stock unless an explicit future admin setting allows backorder behavior.
- Phase 6 does not implement FEFO, batch-specific allocation, or serial-specific allocation. Serial-tracked products are blocked from sales confirmation until explicit serial picking/allocation is implemented.

## Purchase Receive Rules

- Purchase order status alone must not increase stock.
- Stock increases only when goods are received and posted.
- Receiving supports partial quantity, accepted quantity, rejected quantity, damaged quantity, batch, expiry, serials, and receiving location.
- Accepted quantity creates `PURCHASE_RECEIVE` ledger entries and updates stock projection.
- Phase 4 records accepted quantity as `STOCK_IN` ledger entries with `PURCHASE_RECEIPT` references until a dedicated purchase movement type is introduced.
- Phase 5 purchase receipt items can store batch, expiry, warranty, and serial input while draft. Commit forwards those fields to `InventoryEngine.stock_in()`.
- Damaged received quantity must enter damaged or QC state, not sellable available stock.
- Rejected quantity should be recorded against receiving workflow but should not increase sellable stock.
- Received tracked products must satisfy required batch, expiry, and serial data before posting.
- Posting a receive must be idempotent.

## Sales Picking, Packing, And Delivery Rules

- Confirming a sales order reserves stock.
- Picking consumes reservations into operational pick tasks but does not deduct physical stock by itself unless the implementation explicitly models a picked holding state.
- Packing groups picked items into packages and may move stock into a packing/shipping location.
- Delivery completes shipment and deducts physical stock.
- Delivery should normally require an active reservation.
- Delivery without reservation must be blocked unless a documented admin setting allows it.
- FEFO should be used for expiring items when allocation is not explicitly chosen.
- Serial-tracked items must identify exact serials before delivery.
- Phase 6 fulfillment is a basic delivery/deduction foundation against active reservations. Full picking, packing, carrier shipment, mobile scanner workflow, and serial allocation are future work.

## Return QC Rules

- Returned goods do not become sellable immediately.
- Receiving a return moves stock into a return or QC location/state.
- QC result determines final stock state: restock, damaged, expired, repair, scrap, return to vendor, or reject.
- `return_to_qc()` creates return/QC ledger entries and audit logs.
- `approve_return_to_stock()` releases QC-held stock into sellable stock only after a valid QC decision.
- Restocked returns must preserve batch/serial traceability where applicable.

## Damaged, Expired, And Quarantine Rules

- Damaged stock is blocked from available quantity.
- Expired stock is blocked from available quantity and should be moved to an expired location/state.
- Quarantine stock is blocked until explicitly released through QC or an approved workflow.
- Scrapped stock is physically removed from on-hand inventory and must create a ledger entry.
- Expiry jobs may identify expired batches, but `InventoryEngine` must perform the state change.
- Manual damage/expiry/quarantine actions require audit logs with actor, reason, product, warehouse, and quantity.

## Reconciliation Rules

- Reconciliation compares ledger totals to `warehouse_stock` projections.
- Reconciliation supports dry-run, export mismatch report, and controlled fix projection modes.
- Fixes must create `CYCLE_COUNT_ADJUSTMENT` or reconciliation ledger entries, not silent projection edits.
- Reconciliation must be tenant-scoped.
- Reconciliation command target: `python -m app.cli.reconcile_inventory --tenant-id <id>` once backend code exists.

## Audit Log Rules

- Every important stock mutation records tenant, actor, action, reference type, reference ID, before/after quantities where practical, timestamp, and reason/note.
- Audit logs are required for receive, reserve, release, deduct, transfer, adjust, return QC, damage, expire, scrap, quarantine, and reconciliation.
- Audit logging must be part of the same workflow transaction or use a reliable outbox if asynchronous.

## Notification Rules

- Important inventory events may create notifications: low stock, expiry warning, purchase received, order reserved, delivery completed, return QC needed, damaged stock, reconciliation mismatch.
- Notifications should be triggered by domain events or services after the successful mutation path is known.
- Failed transactions must not create success notifications.

## Transaction And Locking Rules

Stock mutation order:

1. Validate tenant, actor, permissions, request shape, and idempotency key.
2. Start transaction.
3. Lock relevant `warehouse_stock` row or rows.
4. Lock batch and serial rows where applicable.
5. Validate availability, state, workflow transition, and tracking requirements.
6. Insert ledger entry or entries.
7. Update projection rows.
8. Create reservations, audit logs, events, and notifications/outbox records as required.
9. Commit transaction.
10. Return authoritative current stock state.

Locking rules:

- Lock rows in a deterministic order to reduce deadlocks.
- Lock by tenant and stock dimensions.
- Avoid broad table locks.
- Retry only safe idempotent operations.
- Never validate availability before acquiring the row locks needed to protect that availability.

## Error Handling Rules

Use structured errors with stable codes.

Recommended codes:

- `INSUFFICIENT_STOCK`
- `INVALID_STOCK_STATE`
- `RESERVATION_NOT_FOUND`
- `RESERVATION_ALREADY_RELEASED`
- `RESERVATION_ALREADY_DEDUCTED`
- `BATCH_REQUIRED`
- `EXPIRY_REQUIRED`
- `SERIAL_REQUIRED`
- `SERIAL_ALREADY_USED`
- `LOCATION_REQUIRED`
- `TENANT_ACCESS_DENIED`
- `IDEMPOTENCY_CONFLICT`
- `CONCURRENT_STOCK_UPDATE`
- `RECONCILIATION_MISMATCH`

Error response shape should include code, message, details, and request ID. Do not expose another tenant's identifiers through errors.

## Backend Test Matrix

| Area | Required Tests |
|---|---|
| Tenant isolation | A tenant cannot read, reserve, receive, transfer, adjust, or reconcile another tenant's stock. |
| Stock invariants | Quantity, reserved quantity, available quantity, and blocked quantities cannot violate invariants. |
| Ledger writes | Every mutation creates the expected ledger entry with tenant, actor, reference, and deltas. |
| Idempotency | Repeating the same critical request with the same idempotency key does not duplicate stock or ledger entries. |
| Locking/concurrency | Concurrent reservations cannot oversell the same stock row. |
| Purchase receive | Partial receive, damaged receive, rejected quantity, batch-required, expiry-required, and serial-required cases. |
| Sales reservation | Reserve, release, insufficient stock, already released, and convert reservation to delivery deduction. |
| Picking/packing/delivery | Delivery requires reservation, serials are enforced, and delivery deducts physical stock. |
| Transfers | Transfer out and transfer in create balanced ledger entries and preserve tenant/location boundaries. |
| Adjustments | Adjustment in/out records reasons and blocks negative stock where not allowed. |
| Returns QC | Returned stock enters QC and only becomes sellable after approved QC result. |
| Damaged/expired/quarantine | Blocked stock is excluded from available quantity and cannot be reserved. |
| Reconciliation | Dry-run reports mismatches; fix mode creates correction entries and updates projection. |
| Audit logs | Critical operations create audit records with actor, tenant, reference, and reason. |
| Notifications | Low stock, expiry, and QC-needed events create notifications only after successful commit. |

## Acceptance Criteria

- All stock mutations go through `InventoryEngine`.
- No router, frontend page, repository helper, script, or model method directly changes stock quantities outside the engine.
- Every mutation writes stock ledger entries.
- Warehouse stock projections reconcile with ledger entries.
- Tenant users cannot access or mutate other tenants' stock.
- Sales confirmation reserves stock.
- Sales delivery deducts reserved stock.
- Purchase receiving increases accepted stock only after receive posting.
- Returns go through QC before becoming sellable.
- Damaged, expired, quarantine, and QC-held stock is excluded from available quantity.
- Batch, expiry, and serial tracking are enforced for products that require them.
- Idempotency prevents duplicate mutation from repeated requests.
- Row locks prevent concurrent oversell.
- Audit logs exist for critical stock operations.
- Tests cover core invariants, tenant isolation, ledger behavior, reservations, receiving, delivery, returns QC, and reconciliation.
