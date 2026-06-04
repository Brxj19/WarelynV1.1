# Backend Architecture Rules

## 5-layer architecture

### models/
- SQLAlchemy ORM only
- persistence shape only
- no business logic

### repositories/
- database access only
- tenant-scoped queries only
- no `commit()`
- no HTTP concerns

### services/
- business logic
- transaction boundary
- external services and side effects
- owns `commit()`

### api/
- HTTP translation only
- dependency-based auth
- service orchestration only

### schemas/
- Pydantic request/response contracts
- no ORM objects in responses

## 10 never-violate rules

1. Domain mutations go through the domain engine or service layer only.
2. `tenant_id` comes from authenticated context only.
3. Use Jinja2 or equivalent safe template rendering for output templates.
4. Every schema change gets an Alembic migration.
5. `commit()` belongs in services, never in repositories or routers.
6. Every protected endpoint needs an explicit role dependency.
7. Every repository query filters by tenant.
8. Services raise domain errors, not raw framework exceptions.
9. Routers never contain business rules.
10. Workflow side effects always run in `try/except`.

## Multi-tenancy patterns

- Base tenant-scoped repository methods should accept `tenant_id`.
- Queries should default to tenant-scoped filters.
- If a super-admin bypass is allowed, it must be explicit and documented.
- Cross-tenant reads should return 403 or 404, never 200.

## Request lifecycle

`HTTP request → auth dependency → user context → role check → service call → repository query → response schema → HTTP response`

## Repository pattern

- build reusable base helpers for filters, pagination, and ordering
- keep query composition inside repository methods
- return ORM objects or tuples to services, not to API routes

## Service pattern

- validate preconditions
- perform the business action
- persist the primary change
- emit side effects safely
- commit once at the end

## Database hygiene

- every business table has `created_at` and `updated_at`
- every tenant-owned table has a `tenant_id` index
- every natural key that must be unique gets a constraint
- prefer explicit status values over magic integers
