# Warelyn Entity Relationships and Architecture

This document summarizes entity relationships from the repository graph generated on 2026-06-02. The graph contains 4,160 nodes and 14,870 edges across 446 files. Use this as operational context for questions about how Warelyn entities connect.

## Most Connected Core Nodes

The graph shows these central nodes:

- AppError has 398 edges. Error handling is centralized: services and API layers raise standardized application errors instead of ad hoc exceptions.
- UserContext has 259 edges. Tenant identity, actor identity, and role checks are core to almost every API operation.
- Product has 227 edges. Product connects catalog, warehouse stock, sales lines, purchase lines, batches, reports, valuation, reorder, and stock movement analysis.
- apiRequest() has 214 edges. Frontend service modules share one HTTP client layer.
- WarehouseLocation has 189 edges and Warehouse has 184 edges. Warehouse structure is central to inventory placement, putaway, picking, stock reports, and movement reporting.

## Core Business Entities

Product represents the item Warelyn tracks. Product connects to SKU, category, reorder level, cost price, stock rows, sales order items, purchase order items, stock ledger entries, batches, and reports. Product is the main join point for stock health questions.

Warehouse represents a physical stock-holding site. Warehouse connects to WarehouseLocation, WarehouseStock, putaway tasks, stock ledger entries, reports, and movement filters.

WarehouseLocation represents a bin, shelf, aisle, or named storage position inside a warehouse. It appears heavily in inventory, putaway, picking, and reconciliation workflows.

SalesOrder represents customer demand. It connects to SalesOrderItem, Customer, PickTask, package and fulfillment records, Invoice, SalesReturn, workflow tasks, and notifications.

PurchaseOrder represents replenishment from a vendor. It connects to PurchaseOrderItem, Vendor, PurchaseReceipt, PutawayTask, Bill, workflow tasks, and approval/receipt flows.

SalesReturn represents customer returned stock. It connects to fulfilled sales orders, return lines, QC decisions, blocked stock, stock ledger entries, workflow tasks, and notifications.

StockLedgerEntry represents immutable inventory movement history. It connects Product, Warehouse, movement type, reference type, quantity delta, and reconciliation logic. Stock calculations and audits should use the inventory engine and ledger-backed projections.

WorkflowTask represents role handoff. Sales order confirmation creates PICK_ORDER for inventory. Receipt commit creates PUTAWAY_STOCK. Putaway completion creates RECORD_BILL. Fulfillment commit creates CREATE_INVOICE. Return submission creates RETURN_QC.

Invoice represents sales billing. It connects to Customer and SalesOrder and tracks status, due date, sent date, total amount, and currency snapshot.

Bill represents vendor billing. It connects to Vendor and PurchaseOrder and tracks status, due date, total amount, and currency snapshot.

## Relationship Patterns

Sales flow relationships are: Customer -> SalesOrder -> SalesOrderItem -> reservation/pick task -> package -> fulfillment -> Invoice. Returns can link back to a fulfilled SalesOrder.

Purchase flow relationships are: Vendor -> PurchaseOrder -> PurchaseOrderItem -> PurchaseReceipt -> PutawayTask -> Bill.

Inventory relationships are: Product -> WarehouseStock -> Warehouse/WarehouseLocation, with StockLedgerEntry as the movement audit trail.

Workflow relationships are status-driven. A business status transition creates a task for the next responsible role, and open tasks should not be duplicated for the same entity and step.

Tenant isolation relationships are enforced through UserContext and tenant_id filtering. Repository methods should never return cross-tenant rows.

## Practical Interpretation

When a user asks why an order is stuck, inspect the entity chain in order: SalesOrder status, open PickTask, package/fulfillment draft, Invoice task, and related workflow tasks.

When a user asks why stock looks wrong, inspect Product, WarehouseStock, WarehouseLocation, StockLedgerEntry, and reconciliation mismatch reports.

When a user asks about replenishment, inspect Product reorder level, WarehouseStock available quantity, PurchaseOrder state, PurchaseReceipt state, and PutawayTask state.
