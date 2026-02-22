# Antigravity CRM

A modular, multi-tenant CRM with n8n webhook integration. Built with Python/FastAPI + React.

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 20+ (for local frontend dev)
- Python 3.12+ (for local backend dev)

### 1. Start with Docker Compose

```bash
docker compose up --build
```

This starts:
- **PostgreSQL** on port `5432`
- **FastAPI backend** on port `8000` (auto-runs migrations)
- **React frontend** on port `5173`

### 2. Seed the Database

```bash
docker compose exec backend python -m app.db.seed
```

Creates:
- Default tenant (`default`)
- Admin user: `admin@example.com` / `admin123!`
- 6 pipeline stages (Lead → Won/Lost)

### 3. Open the App

- **Frontend**: http://localhost:5173
- **API Docs** (Swagger): http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Local Development (without Docker)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Start PostgreSQL (ensure it's running on localhost:5432)
# Run migrations
alembic upgrade head

# Seed data
python -m app.db.seed

# Start server
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server proxies `/api` requests to `localhost:8000`.

---

## Architecture

```
crm/
├── backend/
│   ├── app/
│   │   ├── core/           # Config, security, exceptions, middleware
│   │   ├── db/             # Session, base model, seed script
│   │   ├── models/         # SQLAlchemy models (12 tables)
│   │   └── modules/        # Feature modules (7 total)
│   │       ├── auth/       # JWT login, API keys, RBAC
│   │       ├── contacts/   # Contact & company CRUD
│   │       ├── deals/      # Deal pipeline & stages
│   │       ├── activities/ # Unified activity log
│   │       ├── integrations/n8n/  # Webhook endpoints
│   │       ├── reporting/  # Pipeline stats, CSV export
│   │       └── customization/     # Custom fields, settings
│   ├── alembic/            # Database migrations
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/     # Layout, Sidebar
│   │   ├── pages/          # Dashboard, Contacts, Deals, etc.
│   │   └── services/       # API client with JWT interceptor
│   └── Dockerfile
└── docker-compose.yml
```

## n8n Integration

See [docs/n8n-integration.md](docs/n8n-integration.md) for a full guide on connecting n8n workflows.

### Quick Setup

1. Create an API key: **Settings → API Keys → Create Key**
2. In n8n, use HTTP Request nodes to POST to:
   - `POST /api/n8n/lead` — Upsert a lead/contact
   - `POST /api/n8n/activity` — Log an activity
   - `POST /api/n8n/email-history` — Import email threads
   - `POST /api/n8n/deal-update` — Update a deal
3. Set header: `x-api-key: <your-key>`

---

## Key Features

- **Multi-tenant** — each organization has isolated data
- **RBAC** — Admin, Manager, Agent roles
- **Drag & Drop Kanban** — visual deal pipeline
- **Custom Fields** — add fields to contacts/deals/companies via UI
- **Activity Timeline** — unified log across manual + automated sources
- **n8n Webhooks** — HMAC-verified inbound endpoints
- **CSV Export** — export contacts & reports
- **Auto Swagger Docs** — interactive API documentation at `/docs`
