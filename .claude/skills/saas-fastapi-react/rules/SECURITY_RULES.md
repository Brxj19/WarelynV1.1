# Security Rules

## Authentication

- use short-lived access tokens and revocable refresh tokens
- hash passwords with a dedicated password hashing algorithm
- rate limit login and recovery endpoints
- prevent user enumeration in password reset flows
- make recovery tokens single-use and time-limited
- revoke sessions when passwords change

## Authorisation

- every protected endpoint needs an explicit role dependency
- super-admin routes should be isolated under a separate path and guard
- tenant IDs come from authenticated context only
- read-only roles must not see mutation actions
- deny cross-role access explicitly

## Multi-tenancy

- every repository query must include tenant scope
- cross-tenant reads should never return data
- cross-tenant writes should never succeed
- include tenant and actor IDs in audit logs

## HTTP security headers

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy` should disable unused device APIs

## Input security

- validate all API inputs
- reject unexpected fields where practical
- escape rendered templates
- validate MIME type and size for uploads
- keep uploaded files out of the web root

## API security

- use explicit CORS origin lists
- add idempotency to stock and financial mutations
- send request IDs through the stack for tracing
- never log secrets or sensitive personal data

## Security review checklist

1. Does the endpoint have a role guard?
2. Does the service scope by tenant?
3. Does the mutation need idempotency?
4. Is any user input rendered safely?
5. Are secrets excluded from logs and errors?
