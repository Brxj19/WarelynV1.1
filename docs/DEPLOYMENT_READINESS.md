# Warelyn Deployment Readiness

Phase 11 focuses on regression testing, production hardening, and deployment safety. This document is a checklist for preparing Warelyn beyond local development.

## Scope

- Warelyn V2 is complete through Phase 14 (communication/verification/notifications).
- Stock mutation must continue to go through `InventoryEngine` only.
- Frontend values must remain backend-driven for stock, reports, and workflow state.

## Required Environment

Backend production environment values must be explicitly provided:

- `WARELYN_ENVIRONMENT=production`
- `WARELYN_DEBUG=false`
- `WARELYN_DATABASE_URL` with production MySQL credentials.
- `WARELYN_CORS_ORIGINS` limited to trusted frontend origins.
- `WARELYN_JWT_SECRET_KEY` set to a long random secret; never use the example value.
- `WARELYN_ACCESS_TOKEN_EXPIRE_MINUTES` and `WARELYN_REFRESH_TOKEN_EXPIRE_DAYS` set for the deployment policy.
- `WARELYN_SEED_SUPER_ADMIN_ON_STARTUP=false` unless a controlled bootstrap procedure requires it.
- `WARELYN_SMTP_HOST` — SMTP server hostname (e.g., `mailhog`, `smtp.sendgrid.net`).
- `WARELYN_SMTP_PORT` — SMTP port (e.g., `1025` for MailHog, `587` for TLS, `465` for SSL).
- `WARELYN_SMTP_USERNAME` — SMTP username (empty for MailHog).
- `WARELYN_SMTP_PASSWORD` — SMTP password (empty for MailHog).
- `WARELYN_SMTP_FROM_EMAIL` — From address for outbound emails.
- `WARELYN_SMTP_FROM_NAME` — From display name for outbound emails.
- `WARELYN_SMTP_USE_TLS` — Enable STARTTLS (`true`/`false`).
- `WARELYN_SMTP_USE_SSL` — Enable SSL (`true`/`false`).
- `WARELYN_EMAIL_DELIVERY_MODE` — `smtp` for real delivery, `log` to log to console.
- `WARELYN_OTP_CODE_LENGTH` — Number of OTP digits (default `6`).
- `WARELYN_OTP_EXPIRE_MINUTES` — OTP expiry in minutes (default `10`).
- `WARELYN_OTP_MAX_ATTEMPTS` — Max failed OTP attempts before lockout (default `5`).

Frontend production environment values:

- `VITE_API_BASE_URL` pointing to the deployed backend `/api` base URL.

## Docker Notes

`docker-compose.yml` is a development compose file. It intentionally uses bind mounts, local development credentials, and reload/dev servers.

Do not use it as-is for production. A production deployment should:

- Build immutable backend and frontend images.
- Run backend without `--reload`.
- Serve frontend static assets through a production web server or hosting platform.
- Use managed or hardened MySQL with backups.
- Keep secrets outside source control and outside committed compose files.
- Restrict published ports and network access.
- Replace MailHog with a production SMTP relay (SendGrid, Mailgun, SES, etc.).

## Database And Alembic

Before promoting a release:

1. Create or restore the target database.
2. Set `WARELYN_DATABASE_URL` for the target environment.
3. Run `cd backend && .venv/bin/alembic upgrade head`.
4. Confirm the app starts against the migrated database.
5. Keep migrations append-only after release; do not rewrite shipped migrations.

## MailHog / Dev Email

The development `docker-compose.yml` includes a MailHog service for local email testing:

- SMTP: `localhost:1025`
- Web UI: `http://localhost:8025`
- No authentication required in dev.

The backend email service defaults to `WARELYN_SMTP_HOST=localhost` and `WARELYN_SMTP_PORT=1025`. Inside Docker, `WARELYN_SMTP_HOST=mailhog` is set via compose environment.

Backend tests use mock/skip email delivery and do not require MailHog.

## Verification Flow

Email and phone verification use a time-limited, single-use OTP model:

1. User requests verification code (send endpoint).
2. Backend generates random digit code, stores SHA-256 hash.
3. Previous active OTPs for the same user/purpose/destination are superseded.
4. Code is delivered via email (SMTP/MailHog) or SMS outbox record.
5. User submits code; backend validates hash, expiry, consumption, supersede, and attempt count.
6. On success, `email_verified_at` or `phone_verified_at` is set, audit log is created, and a notification is emitted.

Production deployments should configure real SMTP credentials. The `email_delivery_mode=log` setting can be used during development without a mail server.

## Security Checklist

- JWT secret is strong and not the example value.
- CORS origins are explicit and minimal.
- Debug docs and OpenAPI are disabled in production unless intentionally exposed behind access controls.
- Super admin seed credentials are not default values.
- Upload/import endpoints reject malformed input with structured errors.
- Backend role checks enforce permissions; frontend visibility is not security.
- Tenant APIs derive tenant context from authenticated users, not request-supplied tenant IDs.
- OTP codes are hashed at rest; plaintext codes are never persisted.
- Email delivery failures return a clean error; no stack traces are exposed.
- Notification access is user-scoped; cross-user notification reads return 404.

## Validation Checklist

Run before handoff or release:

```bash
cd backend && python3 -m compileall app
cd backend && .venv/bin/python -m pytest  # Expect 136+ passing tests
cd backend && .venv/bin/alembic upgrade head
cd frontend && npm run build
docker compose config
git status --short
```

Or run the helper:

```bash
./scripts/validate.sh
```

## CI Readiness

The repository includes a minimal GitHub Actions workflow at `.github/workflows/ci.yml` for:

- backend compile
- backend pytest
- Alembic migration against MySQL service
- frontend build
- Docker Compose config validation

CI is not deployment automation. Deployment should be added only after target infrastructure is known.
