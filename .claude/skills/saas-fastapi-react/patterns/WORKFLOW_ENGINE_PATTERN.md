# Workflow Engine Pattern

## Core pattern

Every important business action should follow:

`action → permission check → status change → domain event → task → notification → audit`

## Workflow task shape

Suggested fields:
- `tenant_id`
- `entity_type`
- `entity_id`
- `step_key`
- `assigned_role`
- `status`
- `priority`
- `action_url`

## Behaviour rules

- create the task for the next role after the primary action succeeds
- prevent duplicate open tasks for the same entity and step
- auto-complete the current step when the workflow advances
- cancel open tasks when the entity is cancelled
- keep workflow side effects in `try/except`

## Role visibility

- admins may see all tasks
- regular roles should see only their assigned tasks
- read-only roles should not see workflow actions

## Task implementation notes

- use stable machine-readable step keys
- link each task to a deep link that opens the work surface
- emit workflow events for auditability and reporting
- keep business logic in services, not in routers
