# Warelyn Backend Module Architecture

The repository graph identifies Warelyn as a layered FastAPI application. The graph has 4,160 nodes, 14,870 edges, and major communities for Audit, Assistant and FAQ, Document Management, Purchasing and POs, Sales Orders, Inventory Management, Fulfillment and Picking, Tenant Settings, Putaway Tasks, and Frontend Routing.

## Layer Responsibilities

`models/` defines persistence shape through SQLAlchemy ORM classes and enums. Models describe tables, columns, relationships, statuses, and tenant fields. They should not contain business workflows.

`repositories/` defines database access. Repositories query and persist model rows. Tenant repositories must filter by `tenant_id`. Repositories should not create workflow handoffs, send notifications, or make HTTP decisions.

`services/` defines business logic. Services coordinate repositories, validate business transitions, call InventoryEngine for stock mutations, create workflow tasks, send notifications, and write audit events.

`api/` defines HTTP endpoints. Routers should stay thin: parse request schemas, require roles, build UserContext, call services, and return response schemas.

`schemas/` defines Pydantic request and response contracts. Schemas are the boundary between frontend service calls and backend service results.

`dependencies/` and auth helpers provide `require_roles()` and `require_super_admin()`. These are the backend security boundary.

## Request Flow

The standard protected flow is:

1. HTTP request enters an API router.
2. The route applies `require_roles()` or `require_super_admin()`.
3. The dependency returns UserContext with user id, tenant id, and role.
4. The route calls a service method.
5. The service calls repositories and domain logic.
6. Repositories issue tenant-filtered database queries.
7. The service emits workflow tasks, notifications, and audit logs when the business action requires them.
8. The route returns a schema response.

## Inventory Mutation Rule

Stock changes must go through InventoryEngine. Direct stock mutations outside the engine risk breaking ledger integrity, reservations, reconciliation, and reports.

## Workflow Rule

Major business actions follow this pattern: permission check -> entity status change -> domain event -> workflow task -> notification -> audit log. Side effects are wrapped so a workflow or notification failure does not break the main business operation.

## Coupling Observed in the Graph

AppError is the most connected backend node with 398 edges, so error codes and user-facing messages are central. UserContext has 259 edges, showing that role and tenant context are central to endpoint behavior. Product has 227 edges, showing that catalog data is the main backbone of stock, order, and report behavior.

## What Not To Do

Do not put business workflow in repositories. Do not put database logic in API routers. Do not bypass role guards. Do not query tenant data without tenant_id. Do not let the AI assistant perform write actions or direct database queries.
