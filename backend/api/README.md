# `backend/api` — Routes Layer

This folder contains all FastAPI **route handlers** (controllers). Each file maps to one resource and defines the HTTP endpoints for it. The actual business logic lives in `services/` and the security guards live in `security/`.

```
api/
├── __init__.py
└── routes/
    ├── __init__.py
    ├── auth.py      # /auth/*
    ├── users.py     # /users/*
    ├── devices.py   # /devices/*
    └── alerts.py    # /alerts/*
```

---

## `routes/auth.py` — Authentication

**Prefix:** `/auth` | **Tag:** `auth`

### Functions

#### `register(data: UserCreate) → dict`
- **Route:** `POST /auth/register`
- **Auth:** Public (no token required)
- **Input:** JSON body — `email: str`, `password: str`
- **What it does:** Calls `register_user()` from `services/auth_service.py` which hashes the password and writes the new user to the DB via `nexora-db`.
- **Returns:** `{ "username": "...", "email": "..." }`
- **Note:** Username is derived from the email prefix (before `@`) via `UserUtils.get_username_from_email`.

#### `login(form_data: OAuth2PasswordRequestForm, db) → dict`
- **Route:** `POST /auth/login`
- **Auth:** Public
- **Input:** Form-encoded `username` (email) + `password` (OAuth2 standard)
- **What it does:** Calls `authenticate_user()` to verify credentials, then `login_user()` to issue a signed JWT.
- **Returns:** `{ "access_token": "...", "token_type": "bearer" }`
- **Raises:** `401` if credentials are invalid.

### What to change
| What | How |
|---|---|
| Registration validation rules | Edit the `UserCreate` schema in the `nexora-db` package |
| Token response shape | Edit the `return` dict in `login()` |
| Enable email verification on register | Add a verification step inside `register_user()` in `services/auth_service.py` |

---

## `routes/users.py` — User Profile

**Prefix:** `/users` | **Tag:** `users`

### Functions

#### `read_me(user: dict) → dict`
- **Route:** `GET /users/me`
- **Auth:** Bearer token (any authenticated user)
- **Input:** JWT token via `Authorization: Bearer <token>` header
- **What it does:** Calls `get_current_user()` from `security/jwt.py` to decode the token.
- **Returns:** `{ "email": "...", "role": "..." }` — the decoded token payload.

#### `admin_only_route(user: dict) → dict`
- **Route:** `GET /users/admin-only`
- **Auth:** Bearer token — **admin role required**
- **What it does:** A guard example using `require_role("admin")`. Returns a welcome message.
- **Returns:** `{ "msg": "Hello <email>! You are admin." }`
- **Raises:** `403` if the user's role is not `admin`.

### What to change
| What | How |
|---|---|
| Add a profile update endpoint | Add a `PUT /users/me` handler here using `UserOperations` from `nexora-db` |
| Expose more user fields | Extend the return value in `read_me()` by fetching from the DB using the email |
| Add more roles | Change the `require_role("admin")` argument and update the role check in `security/jwt.py` |

---

## `routes/devices.py` — Device Management

**Prefix:** `/devices` | **Tag:** `devices`
**Auth:** All endpoints require `admin` role.

Uses `DeviceOperations` from `nexora-db` for all DB operations.

### Functions

#### `create_device(user, device_form: DeviceCreateForm) → dict`
- **Route:** `POST /devices/create`
- **Input:** Form fields — `hostname`, `device_type`, `ip_address`, `mac_address`
- **Returns:** `{ "status": "created", "device": { "hostname": "..." } }`
- **Raises:** `400` if a device with the same MAC already exists.

#### `list_devices(user) → list`
- **Route:** `GET /devices/`
- **Returns:** List of all registered devices.

#### `get_device(device_mac_address: str, user) → dict`
- **Route:** `GET /devices/{mac}`
- **Returns:** `{ "device": { ... } }`
- **Raises:** `404` if MAC not found.

#### `delete_device(device_mac_address: str, user) → dict`
- **Route:** `DELETE /devices/{mac}`
- **Returns:** `{ "status": "deleted" }`
- **Raises:** `404` if MAC not found.

#### `update_device_api(device_mac_address: str, device_form: DeviceUpdateForm, user) → dict`
- **Route:** `PUT /devices/{mac}`
- **Input:** JSON body — any subset of updatable device fields (partial update supported via `exclude_unset=True`)
- **Returns:** `{ "status": "updated", "device": { ... } }`
- **Raises:** `400` if no data provided · `404` if device not found · `500` on DB error.

### What to change
| What | How |
|---|---|
| Allow non-admin users to list devices | Change `require_role("admin")` to `get_current_user` in `list_devices` |
| Add more device fields | Extend `DeviceCreateForm` / `DeviceUpdateForm` in the `nexora-db` package |
| Add filtering/search on list | Add query parameters to `list_devices()` and pass them to `device_ops.get_all_devices()` |
| Remove the `init()` call at module level | Move it to `main.py` lifespan handler — it's redundant currently |

---

## `routes/alerts.py` — Alerts

**Prefix:** `/alerts` | **Tag:** `alerts`
**Auth:** ⚠️ Currently **public** — no authentication required.

Uses `AlertOperations` from `nexora-db`.

### Functions

#### `all_alerts() → list | str`
- **Route:** `GET /alerts/`
- **Returns:** All alerts, or a string message if none exist or if there are more than 100.
- **Note:** The `+100` cap returns a plain string, not structured JSON — consider improving this.

#### `get_alerts(device_hostname: str) → list | str`
- **Route:** `GET /alerts/{hostname}`
- **Returns:** All alerts for the given device hostname, or a message if none found.

#### `delete_alert(device_hostname: str) → dict | str`
- **Route:** `DELETE /alerts/{hostname}`
- **Returns:** `{ "status": "alert deleted successfully for <hostname>" }`
- **Raises:** Returns a plain string (not an HTTP error) if not found — consider changing to `404`.

### What to change
| What | How |
|---|---|
| Secure alert endpoints | Add `Depends(get_current_user)` or `Depends(require_role("admin"))` to each function |
| Fix 100-alert cap | Return proper pagination (`limit`/`offset` query params) instead of a string |
| Fix error responses | Replace plain string returns with `raise HTTPException(404, ...)` |
| Remove the `init()` call at module level | Same as `devices.py` — it's redundant |