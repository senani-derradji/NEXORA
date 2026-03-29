# NEXORA Core

> **Central ingest and processing hub** — receives metrics from Collectors via gRPC, validates and normalises them, triggers alerts, and writes to InfluxDB time-series + PostgreSQL.

---

## Architecture Overview

```
core/
├── ingester/
│   └── ingest_service.py      # gRPC server — receives Metric proto, runs the pipeline
│
├── buffer/
│   └── ingest_queue.py        # CoreBuffer — in-memory deque (maxlen=1000)
│
├── processer/
│   └── normalizer.py          # Validator + Normalizer — strict input validation & reshaping
│
├── writer/
│   ├── data_writer.py         # CoreWriter — orchestrates DB upsert + alert + InfluxDB write
│   └── metadata_writer.py     # DeviceMetadata — standalone device metadata writer (unused in main pipeline)
│
├── alert_engine/
│   └── CoreAlertEngine.py     # AlertEngine — 11 metrics × 2 thresholds, Telegram stub, DB writer
│
├── time_series/
│   ├── client/
│   │   ├── client.py          # InfluxClient — InfluxDB connection
│   │   └── healthcheck.py     # credentials_is_valid() + health_check() — bucket auto-create
│   ├── config/
│   │   ├── settings.py        # TSBS_INFO — reads env vars for InfluxDB
│   │   └── .env               # ⚙️  InfluxDB credentials (git-ignored)
│   ├── models/
│   │   ├── main_model.py      # InfluxMainModel — base Point builder (tags only)
│   │   └── device_health_model.py  # InfluxHealthModel — full health Point with all fields
│   └── writers/
│       └── device_health_writer.py # WriteHealthStatus() — writes Point to InfluxDB bucket
│
├── grpc_api/
│   ├── proto/
│   │   └── core_ingest.proto  # ⚙️  Protobuf schema (edit to change the data contract)
│   ├── core_ingest_pb2.py     # Auto-generated (DO NOT EDIT)
│   └── core_ingest_pb2_grpc.py  # Auto-generated (DO NOT EDIT)
│
├── configs/
│   ├── database.py            # DB initialisation — loads .env, connects nexora-db
│   └── .env                   # ⚙️  DATABASE_URL (git-ignored)
│
└── requirements.txt           # Python dependencies
```

---

## Data Flow

```
Collector (gRPC client)
        │  sends Metric proto over port 50051
        ▼
CoreIngestService.SendMetric()   (ingester/ingest_service.py)
        │
        ▼
Normalizer.normalize()           (processer/normalizer.py)
        │  validates hostname, IP, MAC, status, device_type, percentages, timestamps
        ▼
CoreBuffer.add_metric()          (buffer/ingest_queue.py)
        │  in-memory deque (maxlen=1000)
        ▼
CoreBuffer.get_metric()
        │
        ▼
CoreWriter.write_in_db()         (writer/data_writer.py)
        │
        ├──► DeviceOperations.create_device() / update_device_status()   (PostgreSQL via nexora-db)
        │
        ├──► AlertEngine.Engine()               (alert_engine/CoreAlertEngine.py)
        │       └──► alertOPS.create_alert()    (PostgreSQL via nexora-db)
        │       └──► _send_telegram()           (Telegram stub — implement for real notifications)
        │
        └──► WriteHealthStatus()                (time_series/writers/device_health_writer.py)
                └──► InfluxDB write_api()       (InfluxDB via influxdb-client)
```

---

## Environment Variables

### `configs/.env` — PostgreSQL (nexora-db)

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` |  | Full SQLAlchemy connection string |

```env
DATABASE_URL=postgresql+psycopg2://nexorauser:nexorapass@postgres:5432/nexoradb
```

### `time_series/config/.env` — InfluxDB

| Variable | Required | Default | Description |
|---|---|---|---|
| `INFLUXDB_INIT_ADMIN_TOKEN` |  | — | InfluxDB API token |
| `TSBS_ORGANIZATION` |  | — | InfluxDB org name |
| `TSBS_BUCKET` |  | — | InfluxDB bucket name |
| `TSBS_URL` |  | `http://influxdb:8086` | InfluxDB base URL |
| `TSBS_RAW_RETENTION` | ❌ | `7d` | Raw data retention window |
| `TSBS_PROCESSED_RETENTION` | ❌ | `30d` | Processed data retention window |

---

## Running Locally

### With Docker (recommended)
```bash
docker build -t nexora-core .
docker run -p 50051:50051 \
  --env-file configs/.env \
  --env-file time_series/config/.env \
  nexora-core
```

### Without Docker
```bash
cd core
pip install -r requirements.txt
python -m core.ingester.ingest_service
```

The gRPC server listens on `[::]:50051`.

---

## Key Dependencies

| Package | Purpose |
|---|---|
| `grpcio` / `protobuf` | gRPC server (receive metrics) |
| `influxdb-client` | Write time-series data to InfluxDB |
| `sqlalchemy` + `psycopg2` | PostgreSQL via nexora-db |
| `nexora-db` | Shared ORM: device ops + alert ops |
| `python-dotenv` | `.env` file loading |

---

## Sub-module Documentation

| Folder | Mini README |
|---|---|
| `alert_engine/` | [alert_engine/README.md](alert_engine/README.md) |
| `buffer/` | [buffer/README.md](buffer/README.md) |
| `configs/` | [configs/README.md](configs/README.md) |
| `grpc_api/` | [grpc_api/README.md](grpc_api/README.md) |
| `ingester/` | [ingester/README.md](ingester/README.md) |
| `processer/` | [processer/README.md](processer/README.md) |
| `time_series/` | [time_series/README.md](time_series/README.md) |
| `writer/` | [writer/README.md](writer/README.md) |
