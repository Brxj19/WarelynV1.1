---
name: warelyn-rbac-audit
description: Audit Warelyn frontend and backend role-based access control. Use when checking route guards, API guards, action buttons, viewer read-only behavior, tenant isolation, and super-admin boundaries.
---

# Warelyn RBAC Audit

Audit roles:

- SUPER_ADMIN
- TENANT_ADMIN
- INVENTORY_MANAGER
- SALES_STAFF
- PURCHASE_STAFF
- VIEWER

Inspect:

- backend/app/api
- backend/app/services
- backend/app/models/auth.py
- frontend/src/routes
- frontend/src/lib/permissions.js
- frontend/src/components/navigation.js
- frontend/src/pages

Find mismatches between frontend and backend.

Report:

- Route
- Frontend allowed roles
- Backend allowed roles
- Mismatch
- Security risk
- Required fix
- Tests needed

Special checks:

- VIEWER must be read-only
- SALES_STAFF must not manage purchase workflows
- PURCHASE_STAFF must not manage sales workflows
- INVENTORY_MANAGER must not manage users/templates unless explicitly allowed
- TENANT_ADMIN can manage tenant users/templates/settings
- SUPER_ADMIN must not be forced into tenant layout
- Cross-tenant access must be blocked

Create or update:

docs/WARELYN_RBAC_AUDIT.md