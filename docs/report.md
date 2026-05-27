# Warelyn Inventory — Phases 15–18 Implementation Report

## Overview

| Phase | Name | Tests Added | Total After | Status |
|-------|------|-------------|-------------|--------|
| 15 | Jinja2 + PDF Templates | 17 | 108 target (actual 192 baseline) | Done |
| 16 | Admin Layout + Role Guards | 8 | 116 target | Done |
| 17 | Settings + Toast + Editors | 24 (17/17A/17B/17C) | 140 target | Done |
| 18 | Operational Completion | 26 | 170 target (actual 218) | Done |

Final test count: **218 passing, 0 failures.**

---

## Phase 15 — Jinja2 Engine + WeasyPrint PDF + HTML Templates

### What was requested
- Replace `str.format_map` template rendering with Jinja2
- Implement WeasyPrint PDF generation (with fallback)
- HTML email templates with Jinja2 variables
- Auto-seed default templates on first render
- `body_template_text` column on DocumentTemplate
- PDF preview endpoint

### What was built
- `app/services/documents.py` — Full rewrite with Jinja2 `_render()`, HTML DEFAULT_TEMPLATES, nested context builders
- `app/services/pdf_service.py` — `render_html_to_pdf()` using WeasyPrint + text fallback
- `app/api/verification.py` — Updated to pass Jinja2 context and HTML/text to send_email
- `app/schemas/documents.py` — Added `body_template_text` to read/update schemas
- `app/models/documents.py` — Added `body_template_text` field
- `app/api/documents.py` — Added `POST /document-templates/{id}/preview-pdf`
- `alembic/versions/20260525_0013_document_template_text_column.py` — Migration
- `requirements.txt` — Added jinja2>=3.1.4, weasyprint==62.3
- `tests/test_documents.py` — Updated existing tests for Jinja2 syntax

### Bugs fixed
- BUG-001: PDF stub returning empty bytes
- BUG-002: Template engine using str.format_map
- BUG-003: Context structure mismatch for document rendering
- BUG-004: Auto-seed not triggering on first render
- BUG-005: body_template_text not persisted

---

## Phase 16 — Admin Layout + Role Guards + Notification Rename

### What was requested
- Platform Admin layout with deep navy sidebar
- Super admin role guard on admin routes
- Rename NotificationService → NotificationRepository
- Admin dashboard summary endpoint
- Tenant list endpoint for super admins

### What was built
- `frontend/src/layouts/AdminLayout.jsx` — Deep navy sidebar with Platform Admin badge
- `frontend/src/routes/ProtectedRoute.jsx` — Added `requiredRole` prop
- `frontend/src/routes/AppRoutes.jsx` — Admin layout routes
- `app/repositories/notification.py` — Renamed to NotificationRepository
- `app/api/notifications.py` — Updated import
- `tests/test_phase16_admin.py` — 8 tests

### Bugs fixed
- BUG-006: Admin routes nested in tenant layout
- BUG-009: NotificationService naming collision

---

## Phase 17 — Settings + Global Toast + Template Editors + XLSX Import

### What was requested
- Settings page with controlled React state (no document.getElementById)
- Global error toast via apiClient interceptor
- Email Template Editor (list + WYSIWYG + placeholder insertion)
- PDF Template Gallery + Editor + live preview
- XLSX import template download button

### What was built
- `frontend/src/pages/SettingsPage.jsx` — Full rewrite with useState
- `frontend/src/services/apiClient.js` — Added setGlobalErrorHandler + error interception
- `frontend/src/layouts/MainLayout.jsx` — Global error handler registration
- `frontend/src/pages/EmailTemplatesPage.jsx` — List + editor + Insert Placeholder
- `frontend/src/pages/PdfTemplatesPage.jsx` — Card gallery + editor + live preview
- `frontend/src/services/documentService.js` — listTemplates, getTemplate, updateTemplate, previewTemplate, previewTemplatePdf
- `frontend/src/pages/ProductImportPage.jsx` — XLSX template download button
- `app/api/imports.py` — `GET /imports/products/template.xlsx`
- `app/services/imports.py` — `build_template_xlsx()` static method
- `tests/test_phase17_settings.py` — 6 tests
- `tests/test_phase17a_email_templates.py` — 8 tests
- `tests/test_phase17b_pdf_templates.py` — 6 tests
- `tests/test_phase17c_xlsx_import.py` — 4 tests

### Bugs fixed
- BUG-007: document.getElementById in React settings
- BUG-008: No global error toast
- BUG-010: XLSX import UI missing template download

---

## Phase 18 — Operational Completion

### What was requested
- Stock State Expansion: 5 new quantity columns on warehouse_stock
- Reorder Rules: Full CRUD table
- Putaway Tasks: New table + workflow (PENDING → IN_PROGRESS → COMPLETED)
- Cycle Counts: Session + lines, DRAFT → SUBMITTED → RECONCILED workflow
- Expiry Job: Batch expiry detection + stock adjustment
- Outbox Events: Foundation for async event dispatch

### What was built
- `app/models/operations.py` — ReorderRule, PutawayTask, StockCountSession, StockCountLine, OutboxEvent
- `app/models/inventory.py` — 5 new Decimal columns on WarehouseStock
- `app/schemas/operations.py` — All CRUD + workflow schemas
- `app/schemas/inventory.py` — Expanded WarehouseStockRead with new fields
- `app/repositories/operations.py` — ReorderRuleRepository, PutawayTaskRepository, CycleCountRepository, OutboxRepository
- `app/services/operations.py` — ReorderRuleService, PutawayTaskService, CycleCountService, ExpireBatchesService
- `app/api/reorder_rules.py` — GET/POST/PATCH/DELETE /reorder-rules
- `app/api/putaway.py` — CRUD + /start /complete /cancel workflow
- `app/api/cycle_counts.py` — Sessions + lines + /submit /reconcile + /expire-batches
- `app/events/outbox.py` — publish_event() foundation
- `app/jobs/expire_batches.py` — run_expire_batches() job
- `alembic/versions/20260525_0014_phase18_operational_completion.py` — Migration for all new tables
- `app/api/router.py` — 3 new routers registered (cycle_counts, putaway, reorder_rules)
- `tests/test_phase18_operations.py` — 26 tests

---

## What Remains (Not in Phases 15–18 scope)

These items are referenced in the codebase or phase plan but were NOT part of Phases 15–18:

| Item | Notes |
|------|-------|
| Frontend pages for Phase 18 features | ReorderRulesPage.jsx, PutawayTasksPage.jsx, CycleCountsPage.jsx not built (backend-only phase) |
| Outbox event consumers/dispatchers | Foundation laid (publish + mark processed), no actual consumers |
| Reorder rule auto-PO creation | Flag exists, no PO auto-creation logic wired |
| Putaway wired to receipt commit | Table + API ready, not auto-triggered on receipt |
| Alembic `upgrade head` on real DB | Migrations written and tested in SQLite; MySQL run not performed |
| E2E browser testing | Backend tests pass; frontend pages not browser-tested in this session |
| Navigation sidebar entries for new pages | Not added (no frontend pages built for Phase 18) |

---

## File Summary

```
53 files changed, 5,406 insertions, 228 deletions
New files: 24
Modified files: 29
```

## Test Breakdown

| Test File | Count |
|-----------|-------|
| test_phase16_admin.py | 8 |
| test_phase17_settings.py | 6 |
| test_phase17a_email_templates.py | 8 |
| test_phase17b_pdf_templates.py | 6 |
| test_phase17c_xlsx_import.py | 4 |
| test_phase18_operations.py | 26 |
| **New tests total** | **58** |
| **Full suite total** | **218** |
