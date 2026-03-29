# NEXORA Collectors

> **Autonomous network observability collector service** — v0.2.0
> Polls devices via SNMP, normalises metrics, buffers them during core outages, and streams to the NEXORA Core via gRPC.

---

## Architecture Overview

```
collectors/
├── main.py                        # Entry point — initialises DB, starts Scheduler
├── requirements.txt               # Python dependencies
├── Dockerfile                     # Container image definition
│
├── config/                        # Static configuration files
│   ├── devices.yml                # ⚙️  Device inventory — ADD YOUR DEVICES HERE
│   ├── snmpd.conf                 # SNMP agent config (for simulated devices)
│   └── db_config/
│       ├── .env                   # ⚙️  Database connection string
│       └── database.py            # DB initialisation helper
│
├── engines/                       # Collection engines (protocol plugins)
│   └── snmp_engine/
│       ├── snmp_collector.py      # Core SNMP poller — CPU, RAM, disk, net, latency
│       └── utils/
│           ├── detect_vendor.py   # OID → vendor name map (Cisco, Juniper, Huawei …)
│           └── detect_type.py     # OID → device type map (router, switch, firewall …)
│
├── normalizer/
│   └── normalizer.py              # Reshapes raw SNMP dict into standard envelope
│
├── scheduler/
│   ├── scheduler.py               # Async per-device polling loop + hot-reload
│   └── heartbeat.py              # Device heartbeat stub (currently simulated)
│
├── buffer/                        # Two-tier metric buffer
│   ├── buffer_manager.py          # Orchestrates memory ↔ disk fallback
│   ├── memory_queue.py            # In-memory deque (maxlen=100)
│   └── dbs_buffer/
│       ├── database_model.py      # SQLAlchemy model (SqlMetrics / buffer_metrics)
│       └── disk_queue.py          # SQLite-backed persistence for offline metrics
│
├── transport/                     # Network transport layer
│   ├── grpc_client.py             # gRPC stub wrapper — sends Metric proto to Core
│   └── check_core_health.py       # gRPC health-check before every send
│
├── grpc_api/                      # Protobuf generated code
│   ├── proto/
│   │   └── core_ingest.proto      # ⚙️  Schema definition — edit to add fields
│   ├── core_ingest_pb2.py         # Auto-generated (DO NOT EDIT manually)
│   └── core_ingest_pb2_grpc.py    # Auto-generated (DO NOT EDIT manually)
│
└── utils/                         # Shared utility helpers
    ├── devices_.py                # DeviceBootstrapper — YAML ↔ DB device sync
    ├── default_data.py            # down_metric() — zero-filled metric when device is DOWN
    └── normalizer_helper.py       # safe_float() — null-safe float casting
```

---

## Data Flow

```
config/devices.yml
        │
        ▼
DeviceBootstrapper (utils/devices_.py)
        │  syncs YAML → PostgreSQL (nexora-db) on startup and every 10 s
        ▼
Scheduler (scheduler/scheduler.py)
        │  spawns one asyncio task per device
        ▼
SNMPMonitor (engines/snmp_engine/snmp_collector.py)
        │  polls CPU / RAM / disk / net / latency via SNMP + ping
        ▼
Normalizer (normalizer/normalizer.py)
        │  reshapes flat dict → structured envelope
        ▼
BufferManager (buffer/buffer_manager.py)
        │  if Core healthy → MemoryQueue → gRPC send
        │  if Core DOWN    → DatabaseBuffer (SQLite) until Core recovers
        ▼
CoreClient (transport/grpc_client.py)
        │  sends Metric proto over gRPC insecure channel
        ▼
NEXORA Core (host: "core", port: 50051)
```

---

## Environment Variables

Stored in `collectors/config/db_config/.env`:

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` |  | Full SQLAlchemy connection string for nexora-db (PostgreSQL) |

**Example:**
```env
DATABASE_URL=postgresql+psycopg2://nexorauser:nexorapass@postgres:5432/nexoradb
```

> ⚠️ If this variable is missing, `database.py` raises a `ValueError` immediately at startup (no silent SQLite fallback here, unlike the backend).

---

## Running Locally

### With Docker (recommended)
```bash
docker build -t nexora-collectors .
docker run --env-file config/db_config/.env nexora-collectors
```

### Without Docker
```bash
cd collectors
pip install -r requirements.txt
python main.py
```

---

## Startup Behaviour

`main.py` does two things on start:
1. Calls `config/db_config/database.py → init()` to connect to the shared PostgreSQL database and create tables.
2. Instantiates `Scheduler`, which:
   - Loads `config/devices.yml` and syncs devices to the DB via `DeviceBootstrapper`.
   - Spawns one `asyncio.Task` per device.
   - Launches a background loop that re-checks the device list every 10 seconds (hot-reload).

---

## Core gRPC Connection

| Setting | Default | Where to change |
|---|---|---|
| Core host | `"core"` | `scheduler/scheduler.py` → `self.host` |
| Core port | `50051` | `scheduler/scheduler.py` → `self.port` |
| Send timeout | `5 s` | `transport/grpc_client.py` → `self.stub.SendMetric(..., timeout=5)` |
| Health check timeout | `3 s` | `scheduler/scheduler.py` → `CoreHealth.check(..., timeout=3)` |

---

## Key Dependencies

| Package | Purpose |
|---|---|
| `pysnmp` | SNMP polling engine |
| `apscheduler` / `asyncio` | Async per-device task scheduling |
| `grpcio` / `protobuf` | gRPC transport to Core |
| `PyYAML` | Device inventory parsing |
| `sqlalchemy` + `psycopg2` | DB connection via nexora-db |
| `watchdog` | File system watching (future use) |
| `nexora-db` | Shared ORM models & device operations |

---

## Sub-module Documentation

| Folder | Mini README |
|---|---|
| `buffer/` | [buffer/README.md](buffer/README.md) |
| `config/` | [config/README.md](config/README.md) |
| `config/db_config/` | [config/README.md#db_config](config/README.md#db_config--database-initialisation) |
| `engines/` | [engines/README.md](engines/README.md) |
| `grpc_api/` | [grpc_api/README.md](grpc_api/README.md) |
| `normalizer/` | [normalizer/README.md](normalizer/README.md) |
| `scheduler/` | [scheduler/README.md](scheduler/README.md) |
| `transport/` | [transport/README.md](transport/README.md) |
| `utils/` | [utils/README.md](utils/README.md) |