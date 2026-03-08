# `backend/utils` — Utility Helpers

This folder contains utility scripts that support application startup and administrative tasks. These are **not** exposed as API routes — they run internally.

```
utils/
└── admin.py     # Super-user seeding on startup
```

---

## `admin.py` — Admin Seeder

**Target:** Called once at startup from `main.py` to ensure default admin accounts always exist in the database. It is **idempotent** — running it multiple times is safe because it skips users that already exist.

### Configuration

At the top of the file, a hardcoded list defines which emails are seeded as admins:

```python
admins = ["admin@nexora", "derradji@nexora"]
```

> ⚠️ **Change this list** to match your organisation's admin emails before deploying.

---

### Functions

#### `create_supper_user(password: str = "admin") → None`

| Item | Detail |
|---|---|
| **Called from** | `main.py` inside `on_startup()` |
| **Default password** | `"admin"` — **must be changed in production** |
| **DB interaction** | Opens a raw SQLAlchemy session via `get_db()`, queries `User` table, inserts missing admins, then closes the session |
| **Password storage** | Calls `hash_password()` from `security/password.py` (bcrypt, 72-char truncated) |
| **Role assigned** | `"admin"` |
| **`last_seen`** | Set to `datetime.utcnow()` at creation time |

**Logic (step by step):**
1. Opens a DB session.
2. Iterates over every email in the `admins` list.
3. Checks if a `User` with that email already exists → **skips if yes**.
4. If not found, creates a new `User` object with the hashed password and `role="admin"`.
5. Adds, commits, and refreshes the record.
6. Closes the session after all admins are processed.

---

### What You Need to Change

| What | Where | Why |
|---|---|---|
| Admin email list | `admins = [...]` at top of file | Replace/extend with your real admin emails |
| Default password | `create_supper_user(password=...)` call in `main.py` | **Never use `"admin"` in production** |
| Password passed at call site | `main.py` line: `create_supper_user(password="admin")` | Change the value or load it from `.env` |
| Add more seed data | Inside `create_supper_user()` | You can extend this to seed other default records (e.g., default devices) |
| Use env variable for password | Read `os.getenv("ADMIN_PASSWORD")` in `main.py` before passing to this function | Avoids hardcoding credentials |

---

### How to Add a New Admin

**Option 1 — Add to the seed list (permanent):**
```python
# admin.py
admins = ["admin@nexora", "derradji@nexora", "newadmin@yourcompany.com"]
```
Restart the service and the new admin will be created automatically.

**Option 2 — API (runtime):**
Register via `POST /auth/register`, then manually update the user's role in the DB to `"admin"`.
