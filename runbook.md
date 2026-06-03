# Warelyn Runbook

This guide covers local development, Docker Compose, MailHog, data seeding, and the native dependencies needed for PDF generation.

## 1. Prerequisites

- Python 3.11 or newer
- Node.js 20 or newer
- Docker and Docker Compose
- MySQL 8 if you are running outside Docker

The backend also requires a Gemini API key for the AI assistant features. The app will not boot cleanly without the required backend settings in `backend/.env` or the Docker Compose environment.

## 2. Local development

### Backend

```bash
cd backend
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
.venv/bin/alembic upgrade head
.venv/bin/python -m app.utils.seed_super_admin
.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

If you want the Minimalist tenant demo data, run:

```bash
cd backend
.venv/bin/python scripts/seed_minimalist.py
```

If you also want the IKEA tenant demo data, run:

```bash
cd backend
.venv/bin/python scripts/seed_ikea.py
```

### Frontend

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

The frontend expects the backend at `http://localhost:8000/api`.

## 3. Docker development

Docker Compose brings up:

- MySQL on `localhost:3307` to avoid colliding with a local MySQL install
- MongoDB on `localhost:27017`
- MailHog on `http://localhost:8025`
- Backend on `http://localhost:8000`
- Frontend on `http://localhost:5173`

Start everything with:

```bash
docker compose up --build
```

Stop the stack with:

```bash
docker compose down
```

### Fresh start options

If you want a clean restart from the repo root and also want to wipe the Docker volumes so the database starts empty:

```bash
docker compose down -v --remove-orphans
docker compose up --build -d
```

Then seed the data in a second terminal:

```bash
docker compose --profile seed run --rm ikea-seed
```

If you also want the Minimalist demo tenant seeded manually from the host:

```bash
cd backend
.venv/bin/python scripts/seed_minimalist.py
```

If you only want to delete the old containers but keep the existing database data:

```bash
docker compose down --remove-orphans
docker compose up --build -d
```

### Docker seed data

If you want the Minimalist tenant demo data after the stack is up:

```bash
docker compose exec backend python scripts/seed_minimalist.py
```

If you want the IKEA tenant demo data after the stack is up:

```bash
docker compose --profile seed run --rm ikea-seed
```

The IKEA seed creates the `IKEA` tenant, products with batch/expiry/serial tracking, and a full set of purchase, sales, return, and cycle count workflows using the shared password `Ikea@12345` for the tenant users.

## 4. MailHog guide

MailHog captures SMTP email in development so you can verify OTP, reset-password, and notification mail without sending real messages.

### Docker Compose

MailHog is already started by `docker compose up --build`.

- SMTP host: `mailhog`
- SMTP port: `1025`
- Web UI: `http://localhost:8025`

### Local backend

If you are running the backend directly on your machine, start MailHog separately:

```bash
docker run --rm -p 1025:1025 -p 8025:8025 mailhog/mailhog
```

Then keep these backend settings:

```env
WARELYN_SMTP_HOST=localhost
WARELYN_SMTP_PORT=1025
WARELYN_EMAIL_DELIVERY_MODE=mailhog
```

## 5. PDF generation dependencies

Warelyn uses WeasyPrint for HTML-to-PDF rendering. WeasyPrint needs system libraries and fonts in addition to the Python package.

### Debian / Ubuntu

```bash
sudo apt-get update
sudo apt-get install -y \
  fonts-liberation \
  fonts-dejavu-core \
  libpango-1.0-0 \
  libpangocairo-1.0-0 \
  libgdk-pixbuf2.0-0
```

### macOS

```bash
brew install pango gdk-pixbuf fontconfig cairo
```

If PDF rendering still looks broken, reinstall the fonts and native libraries above before debugging the Python code.

## 6. Verification commands

### Backend

```bash
cd backend
.venv/bin/python -m compileall app
.venv/bin/python -m pytest -q
```

### Frontend

```bash
cd frontend
npm run build
```

### Full stack smoke check

```bash
curl http://localhost:8000/api/health
```

## 7. Troubleshooting

- If the backend fails on startup, confirm `WARELYN_DATABASE_URL`, `WARELYN_JWT_SECRET_KEY`, `WARELYN_SUPER_ADMIN_EMAIL`, `WARELYN_SUPER_ADMIN_PASSWORD`, and `WARELYN_GEMINI_API_KEY` are set.
- If emails do not appear, open the MailHog UI at `http://localhost:8025`.
- If PDFs fail, check the native libraries in section 5 and make sure the backend container/image was rebuilt.
- If the frontend points to the wrong API, verify `VITE_API_BASE_URL=http://localhost:8000/api`.
