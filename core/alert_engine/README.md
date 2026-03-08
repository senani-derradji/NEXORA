# `core/alert_engine` — Alert Engine

The alert engine evaluates every incoming metric against hardcoded thresholds and, when breached, writes an alert record to PostgreSQL and (optionally) sends a Telegram notification.

```
alert_engine/
└── CoreAlertEngine.py    # AlertEngine class — all threshold checks + Engine() orchestrator
```

---

## `CoreAlertEngine.py` — `AlertEngine`

### `__init__()`
Instantiates `AlertOperations` and `DeviceOperations` from `nexora-db`, and opens a DB session used for device lookups.

---

### `_send_telegram(message: str, level: str = "WARNING")`

Currently a **stub** — prints to stdout with an emoji prefix.

| Level | Prefix |
|---|---|
| `CRITICAL` | 🔴 |
| `WARNING` | 🟡 |
| `INFO` | 🔵 |
| Other | ⚪ |

**To activate real Telegram alerts**, replace the body with:
```python
import requests
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID")
url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
requests.post(url, json={"chat_id": CHAT_ID, "text": f"[{level}] {message}"})
```
Store `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in `configs/.env`.

---

### Alert Threshold Methods

Each method returns `True` if a threshold was breached (and sends a Telegram message), `False` otherwise.

| Method | WARNING threshold | CRITICAL threshold |
|---|---|---|
| `cpu_alert(cpu, host)` | `> 85%` | `> 90%` |
| `ram_alert(ram, host)` | `> 80%` | `> 95%` |
| `disk_alert(disk, host)` | `> 80%` | `> 95%` |
| `latency_alert(latency, host)` | `> 150 ms` | `> 400 ms` |
| `packet_loss_alert(packet_loss, host)` | `> 1%` | `> 5%` |
| `in_bytes_alert(in_bytes, host)` | `> 800 Mbps` | `> 950 Mbps` |
| `out_bytes_alert(out_bytes, host)` | `> 800 Mbps` | `> 950 Mbps` |
| `in_packets_alert(in_packets, host)` | `> 500k pps` | `> 900k pps` |
| `out_packets_alert(out_packets, host)` | `> 500k pps` | `> 900k pps` |
| `in_errors_alert(in_errors, host)` | `> 0.5%` | `> 2%` |
| `out_errors_alert(out_errors, host)` | `> 0.5%` | `> 2%` |

All methods guard against `None` input — returning `False` immediately if the value is `None`.

---

### `Engine(status, hostname, cpu, ram, disk, latency, packet_loss_percent, in_bytes, out_bytes, in_packets, out_packets, in_errors, out_errors, device_id=None)`

**Main orchestrator method.** Called by `writer/data_writer.py → CoreWriter.write_in_db()`.

**Logic:**
1. Returns `{"invalid_input": True}` if `status` or `hostname` is missing.
2. Looks up the device in PostgreSQL by hostname (or uses `device_id` if provided).
3. If `status == "down"`:
   - Creates a `high` severity alert: `"Device <hostname> is DOWN"`.
   - Returns `{"down": True}` immediately — no metric checks.
4. If `status == "up"`:
   - Runs all 11 threshold methods.
   - Creates DB alert records for triggered groups:
     - CPU or RAM breach → `mid` alert: `"High load: CPU=X%, RAM=Y%"`
     - Disk breach → `low` alert: `"High disk usage: Disk=X%"`
     - Latency breach → `mid` alert: `"High latency: X ms"`
     - Packet loss breach → `mid` alert: `"Packet loss detected: X%"`
     - In/out bytes breach → `mid` alert: `"High traffic: in=X / out=Y"`
     - In/out packets breach → `mid` alert: `"High packets: in=X / out=Y"`
     - In/out errors breach → `mid` alert: `"Network errors: in=X / out=Y"`
5. Returns the `alerts` dict with `True/False` per metric.

#### Alert severity levels used

| Level | When |
|---|---|
| `"high"` | Device DOWN |
| `"mid"` | CPU, RAM, latency, packet loss, traffic, errors |
| `"low"` | Disk usage |

---

## What to change

| What | How |
|---|---|
| **Enable real Telegram** | Replace `_send_telegram()` body — see implementation stub in the docstring |
| Add Telegram credentials | Add `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` to `configs/.env` |
| Change a threshold | Edit the `if value > X` lines in the corresponding `*_alert()` method |
| Add a new metric check | Add a new `def new_metric_alert(self, value, host)` method and call it in `Engine()` |
| Change alert severity mapping | Edit the `alert_level=` arguments in `Engine()` |
| Add email / webhook | Add a new `_send_email()` / `_send_webhook()` method and call it alongside `_send_telegram()` |
