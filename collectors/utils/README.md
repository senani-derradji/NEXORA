# `collectors/utils` — Shared Utility Helpers

General-purpose utilities shared across the collector service. No business logic lives here — only reusable helpers used by the scheduler, transport, and buffer layers.

```
utils/
├── devices_.py           # DeviceBootstrapper — YAML ↔ DB device sync
├── default_data.py       # down_metric() — zero-filled envelope for DOWN devices
└── normalizer_helper.py  # safe_float() — null-safe float casting
```

---

## `devices_.py` — `DeviceBootstrapper`

**Target:** Called by `scheduler/scheduler.py` in `__init__()` and every 10 seconds in `sync_devices_loop()`. Keeps the device registry in the shared PostgreSQL database in sync with the `config/devices.yml` file.

### `__init__(yaml_path: str)`

Stores the path to `devices.yml` and instantiates `DeviceOperations` from `nexora-db`.

---

### `_load_yaml_devices() → list[dict]`

Reads `devices.yml` and returns the `devices` list. Returns `[]` if the file doesn't exist.

---

### `_load_db_devices() → list[dict]`

Queries all devices from the shared DB via `nexora-db → DeviceOperations.get_all_devices()`. Returns a list of dicts with these keys:

```python
["hostname", "device_type", "ip_address", "mac_address", "status", "interval"]
```

---

### `compare() → bool`

Compares YAML MAC addresses against DB MAC addresses. Returns `True` if both sets are identical. Used as a fast pre-check before doing DB writes.

---

### `check_dbs_exists_and_matched_with_yaml() → list[dict]`

**Main public method.** Called by `Scheduler.__init__()` and `sync_devices_loop()`.

**Logic:**
1. Load YAML devices and DB devices.
2. If MAC sets match → return DB devices immediately (no writes).
3. If not → for each YAML device missing from DB, call `DeviceOperations.create_device()`.
4. Return the updated DB device list.

This makes the system **idempotent on startup** — running it multiple times is safe.

> ⚠️ `status` is hardcoded to `"START"` when a device is first inserted. The operational status (`"UP"`, `"DOWN"`, `"DEGRADED"`) is set later by the scheduler based on metric collection results.

### What to change

| What | How |
|---|---|
| Add a new YAML field | Add it to `devices.yml`, then pull it from `device.get("new_field", default)` in `check_dbs_exists_and_matched_with_yaml()` and pass it to `create_device()` |
| Change initial device status | Edit `status="START"` on the `create_device()` call |
| Change the sync interval | Edit `await asyncio.sleep(10)` in `scheduler/scheduler.py → sync_devices_loop()` |
| Support multiple YAML files | Extend `__init__` to accept a list of paths and merge the device lists |
| Delete removed devices from DB | Add logic to find devices in DB that are no longer in YAML and call `DeviceOperations.delete_device()` |

---

## `default_data.py` — `down_metric(device: dict)`

**Target:** Returns a zero-filled metric dict for a device that is confirmed DOWN. Used as the raw input to `Normalizer.normalize()` when a heartbeat fails.

> ⚠️ Currently **not called** — the heartbeat block is commented out in `scheduler/scheduler.py`. This function is ready for when the heartbeat is activated.

### Output shape

```python
{
    "hostname": device["hostname"],
    "device_type": device["device_type"],
    "device_ip": device["ip_address"],
    "device_mac": device["mac_address"],
    "cpu": 0.0, "ram": 0.0,
    "disk": 0.0,
    "in_net_bytes": 0.0, "out_net_bytes": 0.0,
    "in_net_packets": 0.0, "out_net_packets": 0.0,
    "in_net_errors": 0.0, "out_net_errors": 0.0,
    "latency": 0.0, "packet_loss": 0.0,
    "status": "DOWN",
    "timestamp": <current unix epoch>
}
```

### Known bug
The `device_type` comparison uses `" server"` (with a leading space) instead of `"server"`. Fix:
```python
# Change this:
"disk": 0.0 if device["device_type"] == " server" else "",
# To this:
"disk": 0.0 if device["device_type"] == "server" else None,
```

Also, **the field names here don't match the SNMP engine output** (`in_net_bytes` vs `in_bytes`). If you activate the heartbeat path, align these keys with `normalizer/normalizer.py`'s expected input.

### What to change
| What | How |
|---|---|
| Fix the space bug in device_type check | Remove leading space: `== "server"` |
| Align field names with engine output | Rename `in_net_bytes → in_bytes`, `out_net_bytes → out_bytes`, etc. |
| Add missing fields | Add `disk`, `in_errors`, `out_errors` using the same key names as `snmp_collector.py` |

---

## `normalizer_helper.py` — `safe_float(value, default=0.0)`

**Target:** Used by `transport/grpc_client.py` to safely convert any metric value to `float` before packing into a proto `map<string, double>`.

```python
safe_float(None)          # → 0.0
safe_float("3.14")        # → 3.14
safe_float("bad_value")   # → 0.0
safe_float(42)            # → 42.0
```

### What to change
| What | How |
|---|---|
| Change the default | Pass `default=<value>` at call site |
| Add logging on bad values | Add a `logging.warning(...)` in the `except` block |
