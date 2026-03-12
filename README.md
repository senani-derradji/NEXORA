# NEXORA

> **Open-source network observability platform** — collect, process, store, alert, and visualise the health of every device in your infrastructure in real time.

NEXORA is a self-hosted, containerised observability stack built around industry-standard protocols (SNMP, gRPC, InfluxDB line protocol). It is designed to grow from a single-node lab environment to a scalable, multi-tenant SaaS deployment.

---

## What NEXORA Does

| Capability | Description |
|---|---|
| **Device discovery & inventory** | Register devices via YAML or REST API. Device state is kept in sync automatically. |
| **Real-time metric collection** | Polls every registered device over SNMP at configurable per-device intervals (CPU, RAM, disk, network counters, latency, packet loss). |
| **Streaming ingest pipeline** | Metrics flow from collectors to the Core over gRPC — binary, efficient, and health-checked. |
| **Strict data validation** | The Core processor validates every field (hostname regex, IP/MAC format, percentage bounds, Unix timestamp range) before anything is written. |
| **Time-series storage** | All metrics land in InfluxDB for high-resolution querying and dashboarding. |
| **Relational metadata** | Device inventory, status, and alert history are stored in PostgreSQL. |
| **Threshold-based alerting** | 11 metrics × 2 severity levels (WARNING / CRITICAL) evaluated on every incoming metric. Alerts written to PostgreSQL. Telegram notification stub ready to activate. |
| **REST API** | FastAPI backend exposes device management, user auth (JWT), and alert retrieval. |
| **Resilient buffering** | Collectors buffer metrics locally (memory → SQLite disk fallback) during Core outages and replay them automatically on recovery. |

---

## Architecture & Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Physical / Virtual Network                  │
│  [ Linux Server ]  [ Windows ]  [ Router ]  [ Switch ]  [ Firewall ]│
│       SNMP ↑            SNMP ↑       SNMP ↑      SNMP ↑     SNMP ↑  │
└───────────────────────────┬─────────────────────────────────────────┘
                            │  UDP/161 (SNMP polling + ping)
                            ▼
┌───────────────────────────────────────────────────────┐
│                    COLLECTORS  (.40)                  │
│                                                       │
│  config/devices.yml ──► DeviceBootstrapper            │
│                              │                        │
│                              ▼                        │
│  Scheduler (1 asyncio task / device)                  │
│      │                                                │
│      ▼                                                │
│  SNMPMonitor.collect_device_metrics()                 │
│      │                                                │
│      ▼                                                │
│  Normalizer.normalize()  ── canonical envelope        │
│      │                                                │
│      ▼                                                │
│  BufferManager                                        │
│    ├── MemoryQueue (in-memory deque)                  │
│    └── DatabaseBuffer (SQLite fallback on outage)     │
│      │                                                │
│      ▼  gRPC / port 50051                             │
└──────────────────────────────┬────────────────────────┘
                               │
                               ▼
┌───────────────────────────────────────────────────────┐
│                      CORE  (.30)                      │
│                                                       │
│  CoreIngestService.SendMetric()  ◄── gRPC server      │
│      │                                                │
│      ▼                                                │
│  Normalizer.normalize()  (strict validation)          │
│      │                                                │
│      ▼                                                │
│  CoreBuffer (in-memory deque, maxlen=1000)            │
│      │                                                │
│      ▼                                                │
│  CoreWriter.write_in_db()                             │
│    ├──► DeviceOperations.upsert()  ─────────────────────────────────┐
│    ├──► AlertEngine.Engine()       ─────────────────────────────────┤
│    │       └──► alertOPS.create_alert()  ────────────────────────── │
│    └──► WriteHealthStatus()  ───────────────────────────────────────┤
│              └──► InfluxDB write_api()                              │
└───────────────────────────────────────────────────────┬─────────────┘
                │ PostgreSQL                             │ InfluxDB
                ▼                                        ▼
┌─────────────────────────┐              ┌──────────────────────────┐
│   POSTGRES  (.20)       │              │   INFLUXDB  (.10)        │
│                         │              │                          │
│  Tables:                │              │  Measurement:            │
│  • users                │              │  DEVICE_STATS_V1         │
│  • devices              │              │                          │
│  • alerts               │              │  Tags: hostname, ip,     │
│                         │              │        mac, device_type  │
│  Managed by nexora-db   │              │                          │
│  (shared ORM package)   │              │  Fields: cpu, ram, disk, │
└────────────┬────────────┘              │    net counters, latency,│
             │                           │    packet_loss, status   │
             │                           └──────────────────────────┘
             │ REST / HTTP :8000
             ▼
┌───────────────────────────────────────────────────────┐
│                     BACKEND  (.50)                    │
│                                                       │
│  FastAPI REST API                                     │
│  • POST /auth/register  · POST /auth/login (JWT)      │
│  • GET  /users/me                                     │
│  • CRUD /devices/*  (admin only)                      │
│  • GET/DELETE /alerts/*                               │
│  • GET /health                                        │
└───────────────────────────────────────────────────────┘
             │
             ▼
       [ Frontend ]  ← coming soon
```

---

## Stack & Services

### `docker_compose_full.yml` — All Services

| Service | Container | IP | Port(s) | Role |
|---|---|---|---|---|
| `postgres` | `postgres` | `172.18.0.20` | `5432` | Relational DB — devices, users, alerts (PostgreSQL 16) |
| `influxdb` | `influxdb` | `172.18.0.10` | `8086` | Time-series DB — metric history (InfluxDB 2) |
| `core` | `core` | `172.18.0.30` | `50051` | gRPC ingest server — validation, alerting, writing |
| `collectors` | `collectors` | `172.18.0.40` | `50052→50051` | SNMP poller — per-device async collection |
| `backend` | `backend` | `172.18.0.50` | `8000` | REST API — management interface |
| `v_lab_linux` | `linux` | `172.18.0.9` | `161` | Virtual lab: Linux server (SNMP-enabled) |
| `v_lab_linux_2` | `linux_2` | `172.18.0.5` | `161` | Virtual lab: Linux server 2 |
| `v_lab_linux_3` | `linux_3` | `172.18.0.4` | `161` | Virtual lab: Linux server 3 |
| `v_lab_linux_4` | `linux_4` | `172.18.0.3` | `161` | Virtual lab: Linux server 4 |
| `v_lab_windows` | `windows` | `172.18.0.8` | `161` | Virtual lab: Windows server (SNMP-enabled) |
| `v_lab_micro_router` | `m_router` | `172.18.0.7` | `161` | Virtual lab: MikroTik router |
| `v_lab_micro_switch` | `m_switch` | `172.18.0.6` | `161` | Virtual lab: MikroTik switch |
| `v_lab_fortinet_firewall` | `f_firewall` | — | `161` | Virtual lab: Fortinet firewall |

**Network:** All services share `my_shared_network` — an overlay (`172.18.0.0/24`) that is created automatically by `docker compose`. If you need to pre-create it manually, run `./docker/create_network.sh` (or `.bat`).

**Volumes:**
| Volume | Mounts to | Purpose |
|---|---|---|
| `influxdb2-data` | `/var/lib/influxdb2` | InfluxDB data persistence |
| `postgres_data` | `/var/lib/postgresql/data` | PostgreSQL data persistence |

**Startup dependency order:**
```
postgres (healthy) ──┐
influxdb (healthy) ──┤──► core ─────┐
                     │              ├──► collectors ──► backend
                     └──────────────┘
```

---

### Running the Full Stack

```bash
.env
# Edit .env and enter your secure passwords/tokens

# 2. Start everything
docker compose -f docker_compose_full.yml up --build

# 3. Backend API
open http://localhost:8000/docs

# 4. InfluxDB UI
open http://localhost:8086
```

> To run without the virtual lab devices (real infrastructure only):
> ```bash
> docker compose -f docker_compose_full.yml up --build postgres influxdb core collectors backend
> ```

---

## Repository Structure

```
NEXORA/
├── .env         # Template for all infrastructure secrets
├── backend/             # FastAPI REST API (auth, devices, alerts)
├── collectors/          # SNMP collector service
├── core/                # gRPC ingest, processing, alerting, InfluxDB write
├── nexora-db-package/   # Shared SQLAlchemy ORM package (published to PyPI)
├── docker/
│   ├── init_postgres.sh   # Dynamic PostgreSQL DB/user permission script
│   └── create_network.*   # Helper scripts for manual network creation
├── v_labs/              # Virtual lab device simulators (SNMP-enabled containers)
└── docker_compose_full.yml
```

---

## Service Documentation

| Service | README |
|---|---|
| **Backend** (REST API) | [backend/README.md](backend/README.md) |
| **Collectors** (SNMP poller) | [collectors/README.md](collectors/README.md) |
| **Core** (gRPC + alerting + storage) | [core/README.md](core/README.md) |
| **Frontend** | Coming soon |

---

## Current State & Roadmap

### What works today
- Full metric collection pipeline: SNMP → gRPC → validate → PostgreSQL + InfluxDB
- Threshold alerting (11 metrics, 2 levels) written to PostgreSQL
- REST API: JWT auth, device CRUD, alert retrieval
- Hot-reload device list from YAML (no restart needed)
- Resilient buffering with disk fallback on Core outage
- Virtual lab environment for testing without real hardware

### Planned Features

#### Near-term
- **Frontend dashboard** — real-time device map, metric graphs from InfluxDB, alert feed
- **Real Telegram / email / webhook notifications** — replace the print-stub in `AlertEngine._send_telegram()`
- **NoSQL buffer for collectors** — replace SQLite disk queue with Redis or MongoDB
- **Alert rule configuration** — make thresholds configurable via the API instead of hardcoded
- **SNMP v3 support** — add `UsmUserData` authentication to `snmp_collector.py`

#### Medium-term
- **Multi-engine collectors** — WMI (Windows), Prometheus scrape, Netflow/sFlow, syslog ingestion
- **Custom alert rules** — define per-device thresholds, silence windows, and escalation policies via the REST API
- **Grafana integration** — expose InfluxDB to Grafana with pre-built dashboards for devices, alerts, and traffic
- **Role-based access control (RBAC)** — fine-grained permissions beyond `admin` / `user` roles
- **Audit logging** — record every API action to a dedicated audit trail

#### AI Integration (Future)
- **Anomaly detection** — use time-series ML models (e.g. Isolation Forest, LSTM) trained on InfluxDB data to detect unusual patterns without static thresholds
- **Predictive capacity planning** — forecast CPU, RAM, and disk exhaustion before it happens
- **Intelligent alert correlation** — group related alerts across devices to identify root causes automatically (e.g. upstream router failure causing downstream device alerts)
- **Natural language querying** — allow operators to ask "which devices had high CPU last night?" through an LLM-powered query interface backed by InfluxDB

#### SaaS & Scale Path
- **Multi-tenancy** — namespace all data (devices, alerts, metrics) per organisation; add organisation-level API keys
- **Horizontal collector scaling** — deploy multiple collector instances, each responsible for a subnet, coordinated via a shared device registry
- **gRPC TLS + mTLS** — secure all Collector → Core communication with mutual TLS
- **Token-based API authentication** — replace JWT-only auth with API key support for programmatic integrations
- **Kubernetes deployment** — Helm chart for deploying the full stack on K8s with auto-scaling collectors
- **Managed InfluxDB Cloud / TimescaleDB** — pluggable time-series backend for cloud deployments
- **SOC 2 / compliance mode** — enforce audit logging, data retention policies, and encryption at rest

---

## Key Dependencies

| Package | Service | Purpose |
|---|---|---|
| `fastapi` + `uvicorn` | Backend | REST API framework |
| `sqlalchemy` + `psycopg2` | All | PostgreSQL ORM |
| `nexora-db` | All | Shared ORM models & device/alert operations |
| `influxdb-client` | Core | Time-series write |
| `grpcio` + `protobuf` | Core, Collectors | Binary metric streaming |
| `pysnmp` | Collectors | SNMP polling engine |
| `apscheduler` / `asyncio` | Collectors | Per-device async scheduling |
| `python-jose` + `passlib` | Backend | JWT + bcrypt auth |
| `PyYAML` | Collectors | Device inventory parsing |
