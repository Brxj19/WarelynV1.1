# Testing Standards

## Test organisation

Suggested structure:

- `test_auth.py`
- `test_rbac.py`
- `test_tenant_isolation.py`
- `test_workflow.py`
- `test_notifications.py`
- `test_{domain}.py`

## Mandatory categories

### RBAC tests
- allowed role gets success
- denied role gets 403
- unauthenticated request gets 401

### Tenant isolation tests
- tenant A can create data
- tenant B cannot read or modify it
- denied access should be 403 or 404, never 200

### Workflow tests
- business action creates the expected task
- duplicate action does not create duplicate task
- cancellation closes open tasks
- completion advances the next step

### Mutation persistence tests
- perform the mutation
- re-fetch the entity
- assert the change persisted

## Naming convention

`test_{what}_{when}_{expected_result}`

Examples:
- `test_confirm_order_creates_pick_task_for_manager`
- `test_viewer_cannot_access_write_actions`
- `test_tenant_a_cannot_read_tenant_b_records`

## Fixture guidance

- use tenant-specific fixtures
- keep role-specific tokens or sessions explicit
- use a real test database for integration tests

## Test count rule

- tests should never decrease as the project evolves
- if a refactor deletes a test, add a replacement before merging
