# {PROJECT_NAME} Agent Rules

{PROJECT_NAME} is a multi-tenant FastAPI + React SaaS platform.

---

## Required Reading Before Coding

Always read the current project plan and architecture docs before starting work:

- `docs/{PROJECT_NAME}_CODE_PLAN.md`
- `docs/{PROJECT_NAME}_BUSINESS_WORKFLOW_RBAC_PLAN.md`
- `docs/REAL_WORLD_PRD.md`
- `docs/MODULE_BOUNDARIES.md`
- `docs/API_CONTRACT.md`
- `docs/DATABASE_DESIGN.md`
- `docs/DEPLOYMENT_READINESS.md`

---

## Current Implementation Phase

Track the current phase explicitly and do not skip ahead.

Rules:
- declare the phase at the start of the session
- complete and verify the current phase before moving on
- record the phase result in the plan docs
- if verification fails, fix it before continuing

---

## Subagent Roles

Use the roles in `agents/SUBAGENT_ROLES.md`:

- `saas-backend-fastapi-specialist`
- `saas-frontend-react-specialist`
- `saas-rbac-security-auditor`
- `saas-database-migration-specialist`
- `saas-workflow-architect`
- `saas-testing-qa-specialist`
- `saas-debugging-specialist`
- `saas-ai-rag-specialist`
- `saas-devops-deployment-specialist`

---

## Backend Architecture Rules

Use this 5-layer structure:
- `models/` for ORM persistence
- `repositories/` for DB access only
- `services/` for business logic and commit boundaries
- `api/` for HTTP translation only
- `schemas/` for Pydantic contracts

Never:
- put business logic in routers
- commit in repositories
- bypass tenant filters

---

## Frontend Architecture Rules

Use this structure:
- `pages/` for thin screens
- `services/` for API calls
- `components/` for reusable UI
- `context/` for global state
- `routes/AppRoutes.jsx` for lazy routes and guards
- `components/navigation.js` for nav visibility and breadcrumbs

Never:
- inline fetch in pages
- compute backend business logic in the UI
- show write actions to read-only roles

---

## RBAC Rules

- backend permission checks are authoritative
- frontend permissions are UX only
- every route with backend permissions needs a matching guard
- tenant-scoped data must never leak across tenants

---

## Multi-Tenancy Rules

- every tenant-owned query filters by tenant
- `tenant_id` comes from authenticated context only
- never accept `tenant_id` from the request body for access control

---

## Workflow Rules

Use this chain:

`action → permission check → status change → domain event → task → notification → audit`

Rules:
- wrap side effects in `try/except`
- prevent duplicate open tasks
- keep next-step role assignment explicit

---

## Database Rules

- every schema change gets Alembic
- never use `create_all()`
- service layer owns `commit()`
- add tenant and foreign-key indexes

---

## Security Rules

- short-lived access tokens + revocable refresh tokens
- no secrets in source control
- explicit CORS origins
- safe template rendering
- idempotency for stock and money mutations
- upload validation
- request IDs for traceability

---

## Verification Commands

```bash
cd backend && .venv/bin/python -m compileall app && .venv/bin/python -m pytest -q
cd frontend && npm install && npm run build
```

---

## Commit Rules

Use `rules/GIT_COMMIT_RULES.md`.
Never commit broken tests.
