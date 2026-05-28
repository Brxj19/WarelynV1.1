---
name: warelyn-security-review
description: Review Warelyn for SaaS security problems: tenant isolation, RBAC bypass, unsafe template rendering, file/PDF generation risks, auth/session issues, sensitive logging, and insecure defaults.
---

# Warelyn Security Review

Check:

- tenant_id filtering on all queries
- cross-tenant access
- RBAC enforcement on every API
- VIEWER write-blocking
- user management restrictions
- template rendering security
- PDF rendering security
- email template injection risks
- password reset safety
- disabled user login blocking
- audit logs
- sensitive data in logs
- CORS and auth cookies/tokens
- environment secrets

Return:

- Severity
- File
- Risk
- Exploit example
- Fix
- Test required