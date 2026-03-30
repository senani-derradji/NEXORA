# NEXORA Backend

> **FastAPI-based observability platform backend** — v0.2.0
> Handles authentication, device management, and alert tracking via a REST API.

---

## Architecture Overview

```
backend/
├── main.py                  # App entry point — FastAPI instance, startup hook, router registration
├── config.py                # DB initialisation — loads .env and bootstraps nexora-db
├── requirements.txt         # Python dependencies
├── Dockerfile               # Container image definition
├── .env                     # Environment variables (git-ignored)
│
├── api/
│   └── routes/
│       ├── auth.py          # POST /auth/register  · POST /auth/login
│       ├── users.py         # GET /users/me  · GET /users/admin-only
│       ├── devices.py       # CRUD /devices/*  (admin only)
│       └── alerts.py        # GET/DELETE /alerts/*
│
├── services/
│   └── auth_service.py      # Business logic: register, authenticate, login (JWT issue)
│
├── security/
│   ├── jwt.py               # JWT creation · token decoding · role guard (require_role)
│   └── password.py          # bcrypt hash & verify helpers
│
└── utils/
    └── admin.py             # Super-user seed — creates default admin accounts on startup
```

### Request Flow

```
Client Request
    │
    ▼
FastAPI Router  (api/routes/*.py)
    │
    ▼
Service Layer   (services/auth_service.py)
    │
    ▼
nexora-db pkg   (ORM models + DB operations)
    │
    ▼
PostgreSQL  (or SQLite fallback)
```

Security middleware (`security/jwt.py`) is applied as a FastAPI `Depends()` on protected routes **before** the service layer is called.

---

## Environment Variables

Stored in `backend/.env` (never commit this file):

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` |  | SQLite fallback | Full SQLAlchemy connection string |
| `SECRET_KEY` | ⚠️ | `"derradji"` | JWT signing key — **change in production!** |
| `ALGORITHM` | ❌ | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | ❌ | `60` | Token TTL in minutes |

**Example `.env`:**
```env
DATABASE_URL=postgresql+psycopg2://nexorauser:nexorapass@postgres:5432/nexoradb
SECRET_KEY=your-very-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

> ⚠️ If `DATABASE_URL` is missing the app falls back to a local `temp.db` SQLite file. This is fine for development but **not** for production.

---

## API Reference

### Auth — `/auth`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/auth/register` | Public | Create a new user account |
| `POST` | `/auth/login` | Public | OAuth2 password flow — returns a Bearer token |
| `GET` | `/auth/check-auth` | Bearer token | Check if user is authenticated |

### Users — `/users`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/users/me` | Bearer token | Returns the current user's email + role |
| `PUT` | `/users/me` | Bearer token | Update current user profile |
| `POST` | `/users/change-password` | Bearer token | Change user password |
| `GET` | `/users/` | Bearer token (admin) | List all users |
| `DELETE` | `/users/{id}` | Bearer token (admin) | Delete a user |
| `GET` | `/users/admin-only` | Bearer token (admin) | Admin-only test route |

### Devices — `/devices`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/devices/create` | admin | Register a new device |
| `GET` | `/devices/` | admin | List all devices |
| `GET` | `/devices/{mac}` | admin | Get device by MAC address |
| `PUT` | `/devices/{mac}` | admin | Update device fields |
| `DELETE` | `/devices/{mac}` | admin | Remove a device |
| `GET` | `/devices/count` | admin | Get device count |

### Alerts — `/alerts`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/alerts/` | Public | List all alerts (paginated) |
| `GET` | `/alerts/stats` | Public | Get alert statistics (critical, warnings, info, total) |
| `GET` | `/alerts/realtime` | Public | Get real-time alerts with pagination |
| `GET` | `/alerts/latest` | Public | Get latest alerts (limit parameter) |
| `GET` | `/alerts/{hostname}` | Public | Alerts for a specific device |
| `DELETE` | `/alerts/{hostname}` | Public | Delete alerts for a device |

### Dashboard — `/dashboard`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/dashboard/summary` | admin/viewer | Get dashboard summary with device counts, alerts, and metrics |
| `GET` | `/dashboard/device-metrics` | admin/viewer | Get metrics for all devices with latest readings |
| `GET` | `/dashboard/topology` | admin/viewer | Get network topology with devices |
| `GET` | `/dashboard/metrics/history` | admin/viewer | Get time-series metrics history from InfluxDB |
| `GET` | `/dashboard/metrics/current` | admin/viewer | Get current metrics for all devices from InfluxDB |

### Metrics — `/metrics`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/metrics/cpu` | admin/viewer | Get CPU usage metrics for all devices |
| `GET` | `/metrics/ram` | admin/viewer | Get RAM usage metrics for all devices |
| `GET` | `/metrics/disk` | admin/viewer | Get disk usage metrics for all devices |
| `GET` | `/metrics/network` | admin/viewer | Get network metrics (in/out bytes) for all devices |
| `GET` | `/metrics/latency` | admin/viewer | Get latency metrics for all devices |
| `GET` | `/metrics/packet-loss` | admin/viewer | Get packet loss metrics for all devices |
| `GET` | `/metrics/all` | admin/viewer | Get all metrics at once for dashboard overview |

### WebSocket — `/ws`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `WebSocket` | `/ws/alerts` | Public | Real-time alerts channel — clients receive instant alerts as they are created |

### System

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service health check |
| `GET` | `/test` | Test endpoint for nginx connectivity |

---

## Running Locally

### With Docker (recommended)
```bash
docker build -t nexora-backend .
docker run -p 8000:8000 --env-file .env nexora-backend
```

### Without Docker
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Interactive docs available at: `http://localhost:8000/docs`

---

## Startup Behaviour

On every startup (`main.py → on_startup`):

1. `config.init()` loads `.env` and initialises the database connection + creates all tables.
2. `create_supper_user()` seeds default admin accounts (idempotent — skips if they already exist).

### Default Admin Accounts

Defined in `utils/admin.py`:

| Email | Password |
|---|---|
| `admin@nexora` | `admin` |
| `derradji@nexora` | `admin` |

> ⚠️ Change the default password and the `admins` list before deploying to production.

---

## Key Dependencies

| Package | Purpose |
|---|---|
| `fastapi` | Web framework |
| `uvicorn` | ASGI server |
| `sqlalchemy` | ORM |
| `psycopg2-binary` | PostgreSQL driver |
| `python-jose` | JWT encode/decode |
| `passlib[bcrypt]` | Password hashing |
| `python-dotenv` | `.env` file loading |
| `nexora-db` | Shared DB models & operations package |

---

## What You May Need to Change

| What | Where | Why |
|---|---|---|
| Admin email list | `utils/admin.py` → `admins` list | Add/remove default super-users |
| Default admin password | `main.py` → `create_supper_user(password=...)` call | Harden before production |
| `SECRET_KEY` | `.env` | Never use the default in production |
| Alert auth | `api/routes/alerts.py` | Alerts are currently **public** — add `require_role` if needed |
| Token expiry | `.env` → `ACCESS_TOKEN_EXPIRE_MINUTES` | Tune for security vs. UX |
