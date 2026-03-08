# `collectors/scheduler` — Async Polling Scheduler

The scheduler is the **central orchestrator** of the collector. It owns one `asyncio.Task` per device, manages those tasks' lifecycles, and drives the full collect→normalise→buffer→send pipeline every tick.

```
scheduler/
├── scheduler.py     # Scheduler class — main event loop, task management, hot-reload
└── heartbeat.py     # DeviceHeartbeat — stub (currently simulated, not used in prod loop)
```

---

## `scheduler.py` — `Scheduler`

### `__init__(devices_file="config/devices.yml")`

| Attribute | Value | Description |
|---|---|---|
| `self.host` | `"core"` | gRPC Core hostname |
| `self.port` | `50051` | gRPC Core port |
| `self.devices_file` | `"config/devices.yml"` | Path to device inventory |
| `self.bootstrapper` | `DeviceBootstrapper` | YAML ↔ DB sync utility |
| `self.devices` | `list[dict]` | Loaded device list from DB |
| `self.buffer` | `BufferManager` | Two-tier buffer (memory + disk) |
| `self.config` | `SNMPConfig` | SNMP session parameters |
| `self.snmp_collector` | `SNMPMonitor` | SNMP polling engine |
| `self.CoreClient` | `CoreClient` | gRPC client to Core |
| `self.tasks` | `dict[mac → Task]` | Active asyncio tasks keyed by MAC |

> ⚠️ **Raises `ValueError`** if `devices.yml` is missing or empty — the service cannot start without at least one device.

---

### `async run_device(device: dict)`

The **per-device polling coroutine**. Runs in an infinite loop, sleeping `device["interval"]` seconds between iterations.

**Per-tick flow:**
1. Calls `SNMPMonitor.collect_metrics_as_dataclass()` → raw dict.
2. Applies status classification:
   - `latency > 200 ms` OR `packet_loss > 5%` OR `cpu > 85%` → `status = "DEGRADED"`
   - Otherwise → `status = "UP"`
3. Calls `Normalizer.normalize()` → canonical envelope.
4. Fetches `sysObjectID` and runs `detect_vendor()` + `detect_device_type()` (currently only printed, not stored).
5. Checks Core health via `CoreHealth.check()`:
   - **Core healthy:** `buffer.push_data(status=True)` → `buffer.pop_data()` → `CoreClient.send_metric()`. If send fails → `buffer.push_data(status=False)`.
   - **Core unreachable:** `buffer.push_data(status=False)` → metric goes to disk buffer.
6. All exceptions are caught and printed (the loop continues).

### Status thresholds — what to change

| Threshold | Current value | Where |
|---|---|---|
| Latency alert | `> 200 ms` | `scheduler.py` line ~48 |
| Packet loss alert | `> 5%` | `scheduler.py` line ~49 |
| CPU alert | `> 85%` | `scheduler.py` line ~50 |

---

### `async start()`

Called from `main.py`. Launches two things concurrently:
1. `sync_devices_loop()` — background hot-reload task.
2. `spawn_tasks()` — creates one `asyncio.Task` per device.

Then blocks forever with `await asyncio.Event().wait()`.

---

### `async spawn_tasks()`

Iterates `self.devices`. For each device not already in `self.tasks`, creates `asyncio.create_task(run_device(device))` keyed by `mac_address`.

---

### `async sync_devices_loop()`

Runs every **10 seconds**. Calls `DeviceBootstrapper.check_dbs_exists_and_matched_with_yaml()` to get the latest device list. Compares MAC sets:
- **Removed devices:** cancels their tasks and deletes from `self.tasks`.
- **Added devices:** `spawn_tasks()` creates new tasks for them.

This enables **hot-reload** — you can add or remove devices from `devices.yml` without restarting.

---

## `heartbeat.py` — `DeviceHeartbeat`

### `is_alive(device_name: str) → bool`

**Currently a stub / simulation.** Returns `True` ~95% of the time (random). The real call is commented out in `scheduler.py`.

### What to change

| What | How |
|---|---|
| Activate heartbeat | Uncomment the heartbeat block in `run_device()` (lines 37–39 have the commented code) |
| Real ping check | Replace the `random.randint` with a `subprocess.run(["ping", "-c", "1", ip])` call |
| Change sync interval | Edit `await asyncio.sleep(10)` in `sync_devices_loop()` |
| Change SNMP config | Edit `self.config = SNMPConfig(community=..., ...)` in `__init__()` |
| Change Core host/port | Edit `self.host` and `self.port` in `__init__()` |
| Store vendor/type | Add `normalized["device"]["vendor"] = vendor` before `buffer.push_data()` in `run_device()` |
