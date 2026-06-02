# Warelyn API Endpoint Map

This document summarizes the major Warelyn API endpoint groups and their operational purpose. Warelyn APIs are tenant-aware by default. Tenant routes use role guards and UserContext; super admin routes live under `/admin` and do not use tenant business context.

## Auth

`/auth` handles registration, login, refresh, logout, current user lookup, and public password reset. It returns tokens and user identity details. Auth routes create UserContext for protected routes.

## Catalog

`/catalog` handles products, categories, brands, customers, vendors, and related master data. Product APIs power inventory, order lines, valuation, reorder, and stock reports. Customer APIs support sales and returns. Vendor APIs support purchasing and bills.

## Sales

`/sales` and sales order APIs handle customer orders, order status transitions, line items, confirmation, cancellation, and sales workflow progression. Confirmed sales orders generate inventory work through picking tasks.

## Purchases

`/purchases` and purchase order APIs handle vendor orders, submitted/received states, approval, receipt creation, and purchase workflow progression. Receipt commitment creates putaway work for inventory users.

## Fulfillment

`/fulfillment` handles packages and fulfillment records. Picked stock becomes package and fulfillment drafts. Final packing and fulfillment commit are manual actions. Fulfillment commit deducts reserved stock and creates invoice follow-up work.

## Returns

`/returns` handles sales returns, submission, QC inspection, processing, and stock outcomes. Return submission creates QC work for inventory users. Processing applies accepted restock, blocked, damaged, or rejected outcomes.

## Operations

Operations APIs cover pick tasks, putaway tasks, cycle counts, inventory adjustments, warehouse work, and operational status changes. Putaway completion creates billing follow-up work for purchase users.

## Documents

Document APIs handle invoices, bills, document templates, PDF rendering, email templates, sending invoices, and recording bills. Invoices and bills carry currency snapshots.

## Reports

`/reports` exposes read-only operational reports: warehouse stock, low stock, stock movements, blocked stock, batch expiry, reconciliation, product valuation, inventory summary, and dashboard data.

## Workflow

`/workflow` exposes workflow tasks and events. `workflow_tasks` and `workflow_events` are canonical for role handoff. My Tasks uses these APIs to show work assigned to the current user role.

## Notifications

`/notifications` exposes notification listing, unread counts, mark-read, clear, and clear-all actions. Notifications are tenant-scoped and user-scoped.

## Assistant

`/assistant` powers FAQ, knowledge retrieval, copilot sessions, copilot messages, feedback, reindexing, and telemetry. FAQ is for tenant users. Tenant admin copilot is restricted to TENANT_ADMIN. Assistant answers must stay read-only.

## Admin

`/admin` is for SUPER_ADMIN platform operations such as tenants, users, audit logs, platform dashboard, and platform health. These routes use super admin guards and should not expose tenant-specific business ownership actions.

## Common Request Flow

The common protected request path is: HTTP request -> API router -> role guard -> UserContext -> service -> repository -> database. The service owns workflow and notification side effects. Repositories own tenant-filtered queries only.
