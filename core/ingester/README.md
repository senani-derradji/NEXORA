# `core/ingester` — gRPC Ingest Service

The ingester is the **entry point** of the Core service. It runs the gRPC server, receives `Metric` protos from collectors, and drives the full processing pipeline.

```
ingester/
└── ingest_service.py    # CoreIngestService (gRPC servicer) + HealthServicer + serve()
```

---

## `ingest_service.py`

### `CoreIngestService` (implements `CoreIngestServicer`)

| Attribute | Type | Description |
|---|---|---|
| `self.buffer` | `CoreBuffer(max_size=1000)` | In-memory FIFO queue |
| `self.normalizer` | `Normalizer()` | Validates and reshapes the raw proto payload |
| `self.coredbwriter` | `CoreWriter()` | Writes to PostgreSQL + InfluxDB + alerts |

#### `SendMetric(request, context) → Ack`

Called by the gRPC framework for every incoming `Metric` proto.

**Step by step:**
1. Prints the incoming `metric_values` and `tags` to stdout.
2. Calls `Normalizer.normalize(hostname, metric_values, tags, timestamp)` → validated flat dict.
3. Adds the result to `CoreBuffer`.
4. Immediately pops it back out and calls `CoreWriter.write_in_db()`.
5. Returns `Ack(success=True, message="Metric received")` — **always succeeds** even if the write fails (the `Ack` is returned before checking write results).

> The `Ack` is returned unconditionally — if `write_in_db()` raises an exception, the collector will still see a success response. Consider wrapping in try/except and returning `Ack(success=False)` on failure.

---

### `HealthServicer` (implements standard gRPC health protocol)

Returns `SERVING` for all health check requests. This is what `collectors/transport/check_core_health.py` calls before every metric send.

---

### `serve()`

Starts the gRPC server:

| Setting | Value | Where to change |
|---|---|---|
| Thread pool workers | `10` | `futures.ThreadPoolExecutor(max_workers=10)` |
| Listen address | `[::]:50051` | `server.add_insecure_port("[::]:50051")` |
| TLS | Not enabled | Replace with `add_secure_port(...)` for production |

Registered services:
- `CoreIngestService` — handles `SendMetric` RPCs
- `HealthServicer` — handles gRPC health check protocol

---

## What to change

| What | How |
|---|---|
| Change listen port | Edit `"[::]:50051"` in `serve()` — also update the port in all Collector configs |
| Increase thread pool | Edit `max_workers=10` in `serve()` |
| Enable TLS | Replace `add_insecure_port` with `add_secure_port` + `grpc.ssl_server_credentials()` |
| Return `Ack(success=False)` on write failure | Wrap `write_in_db()` in try/except and return `Ack(success=False, message=str(e))` on exception |
| Add authentication (JWT/token) | Add a gRPC interceptor that validates the `authorization` metadata header |
| Increase buffer size | Edit `CoreBuffer(max_size=1000)` in `__init__()` |
