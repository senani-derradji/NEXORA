# `core/buffer` — Ingest Queue

A lightweight in-memory FIFO queue that sits between the gRPC ingest layer and the writer. It decouples the gRPC receive thread from the (potentially slower) InfluxDB + PostgreSQL write operations.

```
buffer/
└── ingest_queue.py    # CoreBuffer — deque-backed FIFO queue
```

---

## `ingest_queue.py` — `CoreBuffer`

### `__init__(max_size: int = 1000)`

Creates a `deque(maxlen=max_size)`. When full, the oldest entry is silently dropped to make room for the newest.

| Parameter | Default | Description |
|---|---|---|
| `max_size` | `1000` | Maximum number of metrics held in memory |

---

### Methods

| Method | Returns | Description |
|---|---|---|
| `add_metric(metric: dict)` | `True` | Appends a metric to the right of the queue |
| `get_metric()` | `dict` or `None` | Pops and returns the oldest (leftmost) metric |
| `clear_queue()` | `False` always | Clears the queue — **note: always returns `False`** (bug: `deque.clear()` returns `None`, not a truthy value) |
| `size()` | `int` | Current number of items (returns `0` if empty) |

**Usage pattern in `ingester/ingest_service.py`:**
```python
if self.buffer.add_metric(metric=metric__):
    get = self.buffer.get_metric()         # immediately pop what was just added
    self.coredbwriter.write_in_db(get)     # write synchronously
```

This means the buffer currently acts as a **pass-through** — add and immediately pop. Its real value would be unlocked with an async consumer loop.

---

## What to change

| What | How |
|---|---|
| Increase queue capacity | Change `max_size=1000` in `CoreIngestService.__init__()` in `ingester/ingest_service.py` |
| Fix `clear_queue()` return | Change `if self._queue.clear():` to just `self._queue.clear(); return True` |
| Make it async (batch writes) | Replace the direct `write_in_db` call in `ingester` with a background asyncio consumer that drains the buffer in batches |
| Add overflow alerting | Override `add_metric()` to log a warning when `size() >= max_size` |
