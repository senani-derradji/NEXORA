# `collectors/normalizer` — Metric Normaliser

The normaliser is a **pure transformation layer**. It takes the flat raw dict produced by an engine (e.g. `SNMPMonitor.collect_device_metrics()`) and reshapes it into a **structured, canonical envelope** that the rest of the system (buffer, transport, Core) always expects.

```
normalizer/
└── normalizer.py    # Normalizer class with a single static method
```

---

## `normalizer.py` — `Normalizer`

### `normalize(raw_metric: dict) → dict`

**Static method.** No state, no I/O — pure dict-to-dict transformation.

#### Input (from SNMP engine)

```python
{
    "hostname": "server1linux",
    "device_type": "server",
    "device_ip": "172.18.0.9",
    "device_mac": "aa:bb:cc:dd:ee:ff",
    "cpu": 12.5,
    "ram": 67.3,
    "disk": 45.1,
    "in_bytes": 123456.0,
    "out_bytes": 654321.0,
    "in_packets": 1000.0,
    "out_packets": 900.0,
    "in_errors": 0.0,
    "out_errors": 0.0,
    "latency": 3.2,
    "packet_loss": 0.0,
    "status": "UP",
    "timestamp": 1741441200
}
```

#### Output (canonical envelope)

```python
{
    "device": {
        "hostname": "server1linux",
        "device_type": "server",
        "ip": "172.18.0.9",
        "mac": "aa:bb:cc:dd:ee:ff"
    },
    "sys": {
        "cpu": 12.5,
        "ram": 67.3,
        "disk": 45.1
    },
    "net": {
        "in_bytes": 123456.0,
        "out_bytes": 654321.0,
        "in_packets": 1000.0,
        "out_packets": 900.0,
        "in_errors": 0.0,
        "out_errors": 0.0,
        "latency": 3.2,
        "packet_loss": 0.0
    },
    "status": "UP",
    "timestamp": 1741441200
}
```

### Default values on missing keys

All fields use `.get(key, default)` — missing keys never raise an error:

| Field | Default |
|---|---|
| `hostname`, `device_type`, `ip`, `mac` | `"unknown"` |
| All numeric (`cpu`, `ram`, etc.) | `0.0` |
| `status` | `"unknown"` |
| `timestamp` | `int(time.time())` at normalisation time |

---

## What to change

| What | How |
|---|---|
| Add a new top-level group (e.g. `"power"`) | Add a new key to the returned dict in `normalize()` |
| Add a new field to an existing group | Add `.get("new_field", 0.0)` to the appropriate sub-dict |
| Rename output keys | Change the key string in the return dict. **Also update** `transport/grpc_client.py` which reads `metric["sys"]`, `metric["net"]`, and `metric["device"]`. |
| Support multiple engines | Keep the same output shape — the normaliser doesn't care which engine produced the raw dict as long as the field names match |
| Add validation / unit conversion | Add logic inside `normalize()` before returning (e.g. convert kB to MB, cap values at 100%) |
