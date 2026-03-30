# `core/processer` — Normaliser & Validator

The processer performs **strict data validation and reshaping** on the raw proto payload received by the gRPC server. It is the first defence against malformed or out-of-range data entering the system.

> Note: the folder is named `processer` (one 's') — this matches the existing code convention.

```
processer/
└── normalizer.py    # Validator (static methods) + Normalizer.normalize()
```

---

## `normalizer.py`

### `NormalizerValidationError(Exception)`

Custom exception raised by all `Validator` methods when input fails validation. Propagated up to `ingester/ingest_service.py` — if raised, the metric is dropped.

---

### `Validator` — Static Validation Methods

| Method | Input | Validates | Returns |
|---|---|---|---|
| `validate_host(host)` | `str` | Non-empty, ≤253 chars, valid hostname regex | Stripped `str` |
| `validate_ip(ip)` | `str` or `None` | IPv4 (0-255 octets) or IPv6 format | Stripped `str` or `None` |
| `validate_mac(mac)` | `str` or `None` | `XX:XX:XX:XX:XX:XX` or `XX-XX-XX-XX-XX-XX` format | Uppercased `str` or `None` |
| `validate_status(status)` | `str` or `None` | Must be one of: `up`, `down`, `degraded`, `unknown` | Lowercased `str` or `None` |
| `validate_device_type(device_type)` | `str` or `None` | Must be one of: `router`, `switch`, `server`, `firewall`, `access_point`, `endpoint`, `unknown` | Lowercased `str` or `None` |
| `validate_percentage(value, field)` | `int`/`float` or `None` | Must be `0.0 ≤ value ≤ 100.0` | `float` or `None` |
| `validate_non_negative(value, field)` | `int`/`float` or `None` | Must be `≥ 0` | `float` or `None` |
| `validate_timestamp(timestamp)` | `datetime`, `int`/`float`, or ISO `str` | Unix range `1e9 ≤ ts ≤ 1e11`; or valid ISO string | `float` (Unix epoch) |

**Percentage validators** are used for: `cpu`, `ram`, `disk`, `packet_loss`.  
**Non-negative validators** are used for: `in_bytes`, `out_bytes`, `in_packets`, `out_packets`, `in_errors`, `out_errors`, `latency`.

---

### `Normalizer.normalize(host, raw_metrics, tags, timestamp) → dict | False`

**Static method.** Validates all fields and produces a flat dict ready for `CoreWriter`.

**Returns `False`** if any of `host`, `raw_metrics`, `tags`, or `timestamp` is `None`.  
**Raises `NormalizerValidationError`** if any field fails validation (propagated — not caught here).

#### Input
| Arg | Source in ingest_service |
|---|---|
| `host` | `request.device_hostname` |
| `raw_metrics` | `request.metric_values` (`map<string, double>`) |
| `tags` | `request.tags` (`map<string, string>`) |
| `timestamp` | `request.timestamp` |

#### Output — flat dict

```python
{
    # From tags:
    "hostname":    "server1linux",
    "ip_address":  "172.18.0.9",
    "mac_address": "AA:BB:CC:DD:EE:FF",   # always uppercased
    "status":      "up",                   # always lowercased
    "device_type": "server",               # always lowercased

    # From metric_values:
    "cpu":          85.2,
    "ram":          67.1,
    "disk":         45.0,
    "in_bytes":     123456.0,
    "out_bytes":    654321.0,
    "in_packets":   1000.0,
    "out_packets":  900.0,
    "in_errors":    0.0,
    "out_errors":   0.0,
    "latency":      3.2,
    "packet_loss":  0.0,

    # Validated timestamp:
    "timestamp":    1741441200.0
}
```

---

## What to change

| What | How |
|---|---|
| Add a new allowed device type | Add the string to `allowed` set in `validate_device_type()` |
| Add a new allowed status | Add to `allowed` set in `validate_status()` |
| Add a new metric field | Add a `validate_*` call inside `data = { ... }` in `Normalizer.normalize()` |
| Loosen timestamp validation range | Adjust `1e9` / `1e11` bounds in `validate_timestamp()` |
| Return `False` instead of raising | Wrap the validation block in try/except `NormalizerValidationError` and return `False` — this would make the ingester swallow bad metrics silently instead of crashing |
