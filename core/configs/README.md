# `core/configs` — Database Configuration

Handles PostgreSQL connection initialisation for the Core service using the shared `nexora-db` package.

```
configs/
├── .env          # ⚙️  DATABASE_URL — credentials (git-ignored)
└── database.py   # init() — loads .env, connects nexora-db
```

---

## `database.py` — `init(url_env: str = "DATABASE_URL")`

**Target:** Called at module-import time from `writer/data_writer.py` and `alert_engine/CoreAlertEngine.py`. Connects nexora-db to PostgreSQL and creates all ORM tables.

**Behaviour:**
1. Loads `.env` from the same directory as `database.py`.
2. Reads the value of `url_env` from environment.
3. If missing → raises `ValueError` immediately (no fallback).
4. Calls `nexora_db.configs.database.init_database(url)` and `init_db_tables()`.

> Because this is called at import time (top-level `init()` call), the DB connection is established the moment either `data_writer.py` or `CoreAlertEngine.py` is imported. If `DATABASE_URL` is missing, the process crashes before the gRPC server can start.

---

## `configs/.env`

```env
DATABASE_URL=postgresql+psycopg2://nexorauser:nexorapass@postgres:5432/nexoradb
```

---

## What to change

| What | How |
|---|---|
| Change DB host/port | Update `DATABASE_URL` in `.env` |
| Use a different env var name | Pass `init(url_env="MY_VAR")` at the call site |
| Add connection pool settings | Modify `init_database()` inside the `nexora-db` package |
| Move to lazy initialisation | Wrap the top-level `init()` calls in a startup function instead of calling at import time |
