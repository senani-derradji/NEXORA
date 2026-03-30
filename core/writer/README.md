# `core/writer` — Data Writer Layer

The writer layer is the **final step** in the Core pipeline. It receives a validated, normalised metric dict and fans it out to three targets: PostgreSQL (device upsert), the alert engine, and InfluxDB.

```
writer/
├── data_writer.py       # CoreWriter — main pipeline writer (PostgreSQL + alerts + InfluxDB)
└── metadata_writer.py   # DeviceMetadata — standalone device metadata writer (not used in main pipeline)
```

---

## `data_writer.py` — `CoreWriter`

### `__init__()`

| Attribute | Type | Description |
|---|---|---|
| `self.deviceOPS` | `DeviceOperations` | nexora-db device CRUD operations |
| `self.alertEngine` | `AlertEngine` | Alert threshold evaluator |

---

### `write_in_db(metric: dict) → result | None`

**Main method.** Called by `ingester/ingest_service.py` after popping from `CoreBuffer`.

**Step by step:**

1. **Guard:** Returns `None` if `metric` is `None`.

2. **Extract payload:**
   ```python
   {"hostname", "device_type", "ip_address", "mac_address", "status"}
   ```
   `device_type` defaults to `"unknown"` if missing.

3. **PostgreSQL device upsert** (via `nexora-db → DeviceOperations`):
   - Looks up device by `ip_address`.
   - **Not found:** calls `create_device(hostname, device_type, ip_address, mac_address, status)`.
   - **Found:** calls `update_device_status(ip_address, status, last_seen=datetime.utcnow())`.

4. **Alert evaluation** → `AlertEngine.Engine(...)`:
   - Passes all 11 metric fields.
   - Internally writes alert records to PostgreSQL and sends Telegram notifications.

5. **InfluxDB write** → `WriteHealthStatus(...)`:
   - Writes a `Point("DEVICE_STATS_V1")` to the configured bucket.
   - Returns the InfluxDB write API response.

#### Notable field name mismatch
`CoreWriter` reads `metric.get("packet_loss_percent")` but `Normalizer.normalize()` outputs `"packet_loss"` (no `_percent` suffix). This means `packet_loss_percent` is always `None` in both the alert engine and InfluxDB write.

**Fix:**
```python
# In write_in_db(), change:
packet_loss_percent=metric.get("packet_loss_percent"),
# To:
packet_loss_percent=metric.get("packet_loss"),
```

---

## `metadata_writer.py` — `DeviceMetadata`

A **standalone utility class** — not used in the main ingestion pipeline.

### `write_device_metadata(payload: dict) → bool`

Creates a new device in PostgreSQL from a payload dict. Returns `False` if payload is empty, `True` on success.

This can be used for manual device registration or as a batch import helper.

---

## What to change

| What | How |
|---|---|
| Fix `packet_loss` field name | Change `metric.get("packet_loss_percent")` → `metric.get("packet_loss")` in `write_in_db()` |
| Add a new output target (e.g. Kafka) | Add the client in `__init__()` and call it after the InfluxDB write in `write_in_db()` |
| Change device lookup key | Currently looks up by `ip_address`. Switch to `mac_address` for more reliable identity by editing the `get_device_by_ip()` call |
| Log write failures | Wrap `WriteHealthStatus()` in try/except and log to stdout or a monitoring endpoint |
| Use `DeviceMetadata` in the pipeline | Replace the inline `create_device()` call in `write_in_db()` with `DeviceMetadata().write_device_metadata(payload)` |
