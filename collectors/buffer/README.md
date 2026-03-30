# `collectors/buffer` — Two-Tier Metric Buffer

The buffer layer protects against data loss when the NEXORA Core gRPC service is temporarily unreachable. It implements a **two-tier strategy**: a fast in-memory queue for normal operation and a SQLite-backed disk queue as a persistence fallback.

> **Planned change (by the developer):** The disk buffer (`dbs_buffer/`) is a SQLite placeholder. It will be replaced by a **NoSQL store** (e.g. Redis, MongoDB) once the container stack supports it. The `MemoryQueue` inside the container will stay.

```
buffer/
├── buffer_manager.py        # Orchestrator — decides memory vs disk
├── memory_queue.py          # Tier 1: in-memory deque
└── dbs_buffer/
    ├── database_model.py    # SQLAlchemy model (SqlMetrics table)
    └── disk_queue.py        # Tier 2: SQLite persistence
```

---

## `buffer_manager.py` — `BufferManager`

**Target:** Called by `scheduler/scheduler.py`. Acts as the single entry point for all buffer operations. Routes metrics to the correct tier and handles drain-on-recovery.

### `__init__()`
Instantiates `MemoryQueue`, `DatabaseBuffer`, and `CoreClient` (for replaying buffered disk metrics when Core comes back online).

| Attribute | Value | Description |
|---|---|---|
| `self.host` | `"core"` | gRPC Core host |
| `self.port` | `50051` | gRPC Core port |

> ⚠️ **Change `self.host` and `self.port`** here if the Core service runs on a different address.

### `push_data(metric: dict, status: bool)`

| `status` | Action |
|---|---|
| `True` (Core reachable) | Push to `MemoryQueue`. Then drain any unsent disk rows: replay them to Core in order and call `mark_sent()` on success. |
| `False` (Core unreachable) | Write directly to `DatabaseBuffer` (SQLite). |

### `pop_data() → dict | None`
Pops and returns the oldest item from `MemoryQueue`. Called by the scheduler immediately after `push_data()` to hand the metric to the gRPC client.

---

## `memory_queue.py` — `MemoryQueue`

**Target:** In-process deque for hot metrics. Zero I/O, very fast. Auto-drops oldest entries when full.

| Method | Description |
|---|---|
| `push(data)` | Append to right. If full (maxlen=100), leftmost entry is silently dropped. |
| `pop() → dict` | Remove and return leftmost (oldest) entry. Returns `None` if empty. |
| `peek() → dict` | Read leftmost without removing. |
| `size() → int` | Current queue length. |
| `is_empty() → bool` | `True` if no items. |
| `clear()` | Flush entire queue. |
| `get_queue()` | Returns raw `deque` object. |

### What to change
| What | How |
|---|---|
| Queue capacity | Change `maxlen=100` in `__init__` |
| Overflow behaviour | `deque(maxlen=...)` auto-drops oldest — replace with a custom `push()` that spills to disk instead |
| **Replace with NoSQL** | Swap `MemoryQueue` for a Redis client (`redis.StrictRedis`) keeping the same `push/pop` interface |

---

## `dbs_buffer/database_model.py` — `SqlMetrics`

SQLAlchemy ORM model. Creates a table named `buffer_metrics` in a local SQLite file (`buffer.db`).

| Column | Type | Description |
|---|---|---|
| `id` | Integer PK | Auto-increment |
| `device` | String | Device hostname |
| `metric_type` | String | Device type (server, router …) |
| `ots` | Float | Original timestamp (Unix epoch) |
| `sent` | Boolean | `False` = unsent, `True` = delivered |
| `payload` | JSON | Full normalised metric dict |
| `created_at` | DateTime | Row insertion time (UTC) |

### What to change (NoSQL migration)
When replacing SQLite with NoSQL, delete this file and replace `DatabaseBuffer` with a client for your chosen store. Keep the same logical interface (`store_buffer`, `fetch_all_unsent`, `mark_sent`).

---

## `dbs_buffer/disk_queue.py` — `DatabaseBuffer`

**Target:** Persistence fallback. Stores failed metrics in SQLite so they survive container restarts.

Default DB path: `sqlite:///buffer.db` (created in the working directory).

### Methods

#### `store_buffer(data: dict) → bool`
Inserts a new `SqlMetrics` row. Extracts `hostname` and `device_type` from `data["device"]`, stores the full dict as JSON in `payload`.

#### `fetch_unsent(limit: int = 1000) → list[SqlMetrics] | False`
Returns up to `limit` unsent rows. Returns `False` if none found.

#### `fetch_all_unsent() → list[SqlMetrics] | False`
Returns **all** unsent rows (no limit). Used by `BufferManager` on drain.

#### `mark_sent(id_: int) → bool`
Sets `sent = 1` on the row with the given primary key. Returns `False` if the row doesn't exist.

### What to change
| What | How |
|---|---|
| **NoSQL replacement** | Replace this entire class with a client for Redis (`LPUSH`/`LRANGE`/delete), MongoDB, or Cassandra keeping the same method signatures |
| SQLite file location | Change `db_url` default in `__init__` |
| Fetch batch size | Tune `limit` in `fetch_unsent()` |
| Retry on mark failure | Add retry logic inside `mark_sent()` |