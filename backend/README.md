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
| `DATABASE_URL` | ✅ | SQLite fallback | Full SQLAlchemy connection string |
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

### Users — `/users`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/users/me` | Bearer token | Returns the current user's email + role |
| `GET` | `/users/admin-only` | Bearer token (admin) | Admin-only test route |

### Devices — `/devices`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/devices/create` | admin | Register a new device |
| `GET` | `/devices/` | admin | List all devices |
| `GET` | `/devices/{mac}` | admin | Get device by MAC address |
| `PUT` | `/devices/{mac}` | admin | Update device fields |
| `DELETE` | `/devices/{mac}` | admin | Remove a device |

### Alerts — `/alerts`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/alerts/` | Public | List all alerts (max 100) |
| `GET` | `/alerts/{hostname}` | Public | Alerts for a specific device |
| `DELETE` | `/alerts/{hostname}` | Public | Delete alerts for a device |

### System

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service health check |

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
