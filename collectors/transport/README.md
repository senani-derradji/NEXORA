# `collectors/transport` — gRPC Transport Layer

This folder handles **all outbound network communication** from the collector to the NEXORA Core service. It is kept separate from the engine layer so that changing the transport protocol (e.g. switching from gRPC to HTTP/MQTT) only requires changes here.

```
transport/
├── grpc_client.py          # CoreClient — sends Metric proto to Core
└── check_core_health.py    # CoreHealth — gRPC health probe before every send
```

---

## `grpc_client.py` — `CoreClient`

**Target:** Used by `scheduler/scheduler.py` and `buffer/buffer_manager.py`. Wraps the generated gRPC stub into a clean `send_metric()` interface.

### `__init__(host: str, port: int)`

Opens a **persistent insecure gRPC channel** to `host:port`.  
Instantiates `CoreIngestStub` from the generated code in `grpc_api/`.

> ⚠️ The channel is **not authenticated**. For production, replace `grpc.insecure_channel` with `grpc.secure_channel` and provide TLS credentials.

### `send_metric(metric: dict) → dict`

**Main send method.** Takes a normalised metric envelope (output of `Normalizer.normalize()`), builds a `Metric` proto, and calls `stub.SendMetric()`.

**Metric fields mapped to proto:**

| Proto field | Source in `metric` dict |
|---|---|
| `device_hostname` | `metric["device"]["hostname"]` |
| `metric_values["cpu"]` | `metric["sys"]["cpu"]` |
| `metric_values["ram"]` | `metric["sys"]["ram"]` |
| `metric_values["disk"]` | `metric["sys"]["disk"]` |
| `metric_values["in_bytes"]` | `metric["net"]["in_bytes"]` |
| `metric_values["out_bytes"]` | `metric["net"]["out_bytes"]` |
| `metric_values["in_packets"]` | `metric["net"]["in_packets"]` |
| `metric_values["out_packets"]` | `metric["net"]["out_packets"]` |
| `metric_values["in_errors"]` | `metric["net"]["in_errors"]` |
| `metric_values["out_errors"]` | `metric["net"]["out_errors"]` |
| `metric_values["packet_loss"]` | `metric["net"]["packet_loss"]` |
| `metric_values["latency"]` | `metric["net"]["latency"]` |
| `tags["hostname"]` | `metric["device"]["hostname"]` |
| `tags["device_type"]` | `metric["device"]["device_type"]` |
| `tags["ip"]` | `metric["device"]["ip"]` |
| `tags["mac"]` | `metric["device"]["mac"]` |
| `tags["status"]` | `metric["status"]` |
| `timestamp` | `int(time.time())` at send time |

All numeric values pass through `safe_float()` from `utils/normalizer_helper.py` to handle `None` safely.

**Returns:**
- `{"success": True}` on success.
- `{}` (empty dict) on gRPC error, exception, or invalid input.

**Raises:** None — all exceptions are caught and logged.

### `safe_send_metric(metric: dict) → dict`

Thin wrapper around `send_metric()` — swallows any unexpected top-level exception and returns `{}`. Use this instead of `send_metric()` if you need extra safety (e.g. in a retry loop).

---

## `check_core_health.py` — `CoreHealth`

**Target:** Called by `scheduler/scheduler.py` before every `send_metric()` attempt. Prevents sending to a Core that is not yet ready.

### `CoreHealth.check(host: str, port: int, timeout: float = 8) → bool`

1. Opens a temporary insecure gRPC channel to `host:port`.
2. Waits until the channel is ready (or timeout).
3. Calls the standard **gRPC health check protocol** (`grpc_health.v1`) with an empty service name.
4. Returns `True` only if `response.status == SERVING`.
5. Returns `False` and prints an error on any `RpcError` or timeout.
6. Always closes the channel in `finally`.

| Parameter | Default | Description |
|---|---|---|
| `host` | (required) | Core hostname — passed from `scheduler.py` (`"core"`) |
| `port` | (required) | Core port — passed from `scheduler.py` (`50051`) |
| `timeout` | `8 s` | Both channel-ready wait and RPC timeout |

> ⚠️ The Core service **must implement the standard gRPC health checking protocol** (`grpc.health.v1.Health`). If it doesn't, this check will always return `False`.

---

## What to change

| What | How |
|---|---|
| Enable TLS | Replace `grpc.insecure_channel(...)` in both files with `grpc.secure_channel(...)` + credentials |
| Add metadata / auth token | Add `metadata=[("authorization", "Bearer <token>")]` to the `stub.SendMetric(proto, metadata=...)` call |
| Add a new metric field to the proto send | Add it to `metric_values` dict in `send_metric()` and update `grpc_api/proto/core_ingest.proto` |
| Change send timeout | Edit `self.stub.SendMetric(proto, timeout=5)` — increase for slow networks |
| Change health check timeout | Edit `CoreHealth.check(..., timeout=3)` call in `scheduler.py` |
| Switch to HTTP transport | Replace the entire `CoreClient` class with an `httpx` or `requests` client, keeping the same `send_metric(metric: dict) → dict` interface |
