# `core/time_series` — InfluxDB Time-Series Layer

Manages the full lifecycle of writing device health metrics to InfluxDB: connection management, credential/bucket validation, Point model construction, and the write function called by the writer layer.

```
time_series/
├── client/
│   ├── client.py              # InfluxClient — InfluxDB connection wrapper
│   └── healthcheck.py         # credentials_is_valid() — bucket auto-create + health_check()
├── config/
│   ├── settings.py            # TSBS_INFO — reads all InfluxDB env vars
│   └── .env                   # ⚙️  InfluxDB credentials (git-ignored)
├── models/
│   ├── main_model.py          # InfluxMainModel — base Point (tags only)
│   └── device_health_model.py # InfluxHealthModel — full health Point with fields
└── writers/
    └── device_health_writer.py # WriteHealthStatus() — sends Point to InfluxDB
```

---

## `config/settings.py` — `TSBS_INFO`

Loads InfluxDB connection settings from environment variables.

| Variable | Attribute | Default | Description |
|---|---|---|---|
| `TSBS_URL` | `TSBS_INFO.URL` | — | InfluxDB base URL |
| `INFLUXDB_INIT_ADMIN_TOKEN` | `TSBS_INFO.TOKEN` | — | API token |
| `TSBS_ORGANIZATION` | `TSBS_INFO.ORGANIZATION` | — | Org name |
| `TSBS_BUCKET` | `TSBS_INFO.BUCKET` | — | Bucket name |
| `TSBS_RAW_RETENTION` | `TSBS_INFO.RAW_RETENTION` | `"7d"` | Raw data retention |
| `TSBS_PROCESSED_RETENTION` | `TSBS_INFO.PROCESSED_RETENTION` | `"30d"` | Processed data retention |

> `settings.py` calls `load_dotenv()` without a path — it picks up whichever `.env` is in the current working directory or any parent. For reliable loading, keep your env vars in the container's environment or Docker Compose.

### `config/.env` (current values — **change before production**)
```env
INFLUXDB_INIT_ADMIN_TOKEN=<token>
TSBS_ORGANIZATION=myorg
TSBS_BUCKET=dr_bucket
TSBS_URL=http://influxdb:8086
```

---

## `client/client.py` — `InfluxClient`

Wraps `influxdb_client.InfluxDBClient`. On init, calls `credentials_is_valid()` first — if that returns `False`, the client is not created (attribute `self.client` won't exist, causing errors downstream).

**Connection defaults:**
- URL: `TSBS_INFO.URL` or `"http://influxdb:8086"`
- Org: `TSBS_INFO.ORGANIZATION` or `"myorg"`

---

## `client/healthcheck.py`

### `credentials_is_valid() → bool`

1. Creates a temporary `InfluxDBClient`.
2. Checks the organisation exists via `OrganizationsApi`.
3. Checks if the bucket exists via `BucketsApi`.
4. **If bucket doesn't exist → automatically creates it** with `every_seconds=0` (infinite retention).
5. Returns `True` if all checks pass, `False` on any error.

> The `RAW_RETENTION` and `PROCESSED_RETENTION` values in `TSBS_INFO` are read but **not used** in bucket creation — the bucket is currently created with `every_seconds=0` (no expiry). Wire them in if you want timed retention.

### `health_check() → bool`

Calls `InfluxClient().client.health()`. Returns `True` if `status == "pass"`, raises `Exception` otherwise.

---

## `models/main_model.py` — `InfluxMainModel`

### `device_main_point(device_name, device_ip, device_mac, device_type, timestamp, site) → Point`

Builds the base `Point("DEVICE_STATS_V1")` with **tags only** (no metric fields).

| Tag | Field name in Influx |
|---|---|
| `device_name` | `device_name` |
| `device_ip` | `device_ip` |
| `device_mac` | `device_mac` |
| `device_type` | `device_type` |
| `site` | `site` (optional) |

Timestamp precision: `"ms"`.

> The **measurement name** is `"DEVICE_STATS_V1"`. To change it, edit the `Point("DEVICE_STATS_V1")` call here.

---

## `models/device_health_model.py` — `InfluxHealthModel`

### `device_health_point(...) → Point`

Extends the base point with all health fields (fields in InfluxDB = numeric values):

| Field | Notes |
|---|---|
| `status` | Required — raises `InfluxDBError` if `None` |
| `latency` | Required — raises `InfluxDBError` if `None` |
| `packet_loss_percent` | Optional |
| `cpu_usage` | Optional |
| `ram_usage` | Optional |
| `disk_usage` | Optional |
| `in_bytes` | Optional |
| `out_bytes` | Optional |
| `in_packets` | Optional |
| `out_packets` | Optional |
| `in_errors` | Optional |
| `out_errors` | Optional |

All optional fields are only added to the Point if not `None`.

---

## `writers/device_health_writer.py` — `WriteHealthStatus()`

**Top-level function** (not a class). Called by `writer/data_writer.py`.

Opens a **new** `InfluxClient` and `write_api(SYNCHRONOUS)` on every call. Builds the health `Point` with `InfluxHealthModel`, then calls `WRITE_API.write(bucket=..., org=..., record=...)`.

> Opening a new client on every write is inefficient. For high-throughput usage, instantiate `InfluxClient` once (e.g. as a singleton or in `CoreWriter.__init__`) and reuse it across calls.

---

## What to change

| What | How |
|---|---|
| Change InfluxDB URL/token/org/bucket | Update `time_series/config/.env` |
| Add bucket retention | Pass `retention_rules` using `TSBS_INFO.RAW_RETENTION` in `credentials_is_valid()` |
| Change the InfluxDB measurement name | Edit `Point("DEVICE_STATS_V1")` in `models/main_model.py` |
| Add a new metric field to InfluxDB | Add a `.field("new_field", value)` call in `InfluxHealthModel.device_health_point()` — pass the value through `WriteHealthStatus()` and `CoreWriter.write_in_db()` |
| Reuse the InfluxDB client | Instantiate `InfluxClient` once in `CoreWriter.__init__()` and pass it to `WriteHealthStatus()` instead of creating a new one per call |
| Use async write API | Replace `SYNCHRONOUS` with `WriteOptions(batch_size=..., flush_interval=...)` for batched writes |