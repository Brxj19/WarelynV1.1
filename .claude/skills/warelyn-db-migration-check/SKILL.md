---
name: warelyn-db-migration-check
description: Review Warelyn SQLAlchemy models and Alembic migrations for correctness, tenant_id indexes, FK constraints, nullable fields, soft delete, auditability, and backwards compatibility.
---

# Warelyn DB Migration Check

Inspect:

- backend/app/models
- backend/alembic
- backend/app/repositories

Check:

- every tenant-owned table has tenant_id
- tenant_id is indexed where needed
- foreign keys are correct
- migrations match models
- nullable fields are intentional
- enum changes have migrations
- soft-delete fields are used where needed
- workflow/audit tables are append-safe
- no migration destroys existing data unnecessarily

Run if possible:

cd backend
PYTHONPATH=. alembic upgrade head
python -m compileall app

Report issues and fixes.