# {PROJECT_NAME} Agent Rules

{PROJECT_NAME} is a multi-tenant FastAPI + React SaaS platform.

---

## Required Reading Before Coding

Always read the current project docs before starting work:

- `docs/{PROJECT_NAME}_CLAUDE_CODE_PLAN.md` or the active phase plan
- `docs/{PROJECT_NAME}_BUSINESS_WORKFLOW_RBAC_PLAN.md` or equivalent domain plan
- `docs/{PROJECT_NAME}_PRD.md` or product requirements
- `docs/MODULE_BOUNDARIES.md`
- `docs/{DOMAIN_ENTITY}_ENGINE_SPEC.md` or the domain engine spec
- `docs/API_CONTRACT.md`
- `docs/DATABASE_DESIGN.md`
- `docs/DEPLOYMENT_READINESS.md`

---

## Current Implementation Phase

Track phases in a single source of truth.

Rules:
- State the current phase at the top of the session.
- Do not start a later phase until the current phase passes verification.
- Record the phase outcome in the phase plan before moving on.
- If the phase fails verification, fix the failure before proceeding.

Example phase list:
1. Foundation
2. Documents and Reports
3. Workflow Task Engine
4. Sales Workflow Automation
5. Purchase Workflow Automation
6. My Tasks + Role Dashboards
7. RBAC Audit and Cleanup
8. Testing Hardening

---

## Subagent Roles

Use the personas defined in `agents/SUBAGENT_ROLES.md`.

---

## Backend Architecture Rules

Use a 5-layer structure:
- `models/` for ORM persistence only
- `repositories/` for DB access only
- `services/` for business logic and commit boundaries
- `api/` for HTTP translation, auth, and response shaping
- `schemas/` for request/response contracts

Rules:
- Keep routers thin.
- Never put business rules in repositories or routers.
- Repositories never call `commit()`.
- Services own `commit()` and transactional side effects.
- Schema objects, not ORM objects, leave the API.

---

## Frontend Architecture Rules

Rules:
- `pages/` stay thin and compose UI.
- `services/` hold API calls only.
- `components/` are reusable UI pieces without business logic.
- `context/` stores global app state.
- `routes/AppRoutes.jsx` owns route guards and lazy loading.
- `components/navigation.js` owns navigation visibility metadata.

---

## RBAC Rules

- Backend auth is the security boundary.
- Frontend role hiding is UX only.
- Every API endpoint must have an explicit permission dependency.
- Keep route permissions aligned with backend permissions.
- Read-only roles must never see write actions.

---

## Multi-Tenancy Rules

- Every tenant-owned query must filter by `tenant_id`.
- `tenant_id` comes from authenticated context, not request body.
- Never trust client-supplied tenant identifiers.
- Tenant isolation tests are mandatory for new data paths.

---

## Workflow Engine Rules

Follow this chain for major business actions:

`action → permission check → status change → domain event → task → notification → audit`

Rules:
- Wrap all non-primary side effects in `try/except`.
- Duplicate tasks must be prevented.
- Tasks must route to the correct role.
- Cancellation must close open tasks for the entity.

---

## Database Rules

- Use Alembic for every schema change.
- Never use `create_all()` in production code.
- Repositories must not commit.
- Services commit once the business unit of work is complete.
- Add indexes for hot query paths and tenant filters.

---

## Security Rules

1. Authenticate with short-lived access tokens and revocable refresh tokens.
2. Hash passwords with a strong password hash, never a general-purpose hash.
3. Use dependency-based role checks on every protected endpoint.
4. Use tenant-scoped queries everywhere.
5. Keep secrets out of source control and logs.
6. Render templates with safe escaping.
7. Reject unexpected input and validate file uploads.

---

## Code Quality Rules

See `rules/CODE_QUALITY_RULES.md`. Keep the following as defaults:
- strong type hints
- explicit validation
- timezone-aware datetimes
- decimal money values
- stable IDs for React lists
- loading and empty states on every async surface

---

## Verification Commands

Run at the end of each meaningful change:

```bash
cd backend && .venv/bin/python -m compileall app && .venv/bin/python -m pytest -q
cd frontend && npm install && npm run build
```

Use any project-specific validation script if present.

---

## Git Commit Rules

Use the commit format in `rules/GIT_COMMIT_RULES.md`.
Never commit broken tests.
