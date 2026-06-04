# Code Quality Rules

## Backend Python quality

- type hints on all public function signatures
- validate all external input with Pydantic
- prefer explicit arguments over splatting unknown dicts
- use string error codes for domain errors
- never return ORM objects directly from API routes
- use `Decimal` for money
- use timezone-aware datetimes
- use indexes on hot foreign-key and tenant filters
- use explicit boolean defaults

## Frontend React quality

- use controlled inputs
- prefer stable keys
- clean up effects on unmount
- use error boundaries for page-level failures
- keep shared components prop-documented
- avoid unnecessary wrappers
- use loading and empty states everywhere data is fetched

## Database quality

- upgrade and downgrade for every migration
- add tenant keys to tenant-owned tables
- prefer explicit string statuses
- avoid storing derived values unless they are materialised intentionally
- use soft delete or status transitions where auditability matters

## Testing quality

- tests should prove persistence, not just session state
- every new endpoint needs allow + deny coverage
- every workflow transition needs expected-task coverage
- every tenant boundary needs cross-tenant denial coverage

## General habit

- choose explicitness over cleverness
- keep names stable and descriptive
- do not remove tests as part of a refactor unless replacements are added first
