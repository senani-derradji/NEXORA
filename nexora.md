# NEXORA - Network Monitoring System Architecture

## Table of Contents
1. [Project Overview](#project-overview)
2. [High-Level Architecture](#high-level-architecture)
3. [Directory Structure](#directory-structure)
4. [Frontend (React + TypeScript)](#frontend)
5. [Backend (FastAPI)](#backend)
6. [Collectors Service](#collectors-service)
7. [Core Service](#core-service)
8. [Database Schema](#database-schema)
9. [Docker Configuration](#docker-configuration)
10. [API Endpoints](#api-endpoints)
11. [WebSocket Communication](#websocket-communication)
12. [Key Technologies](#key-technologies)

---

## Project Overview

**NEXORA** is a comprehensive network monitoring and alerting system designed to collect, process, and visualize network device metrics in real-time. The system uses SNMP to gather data from network devices, processes the data through a multi-tiered pipeline, stores metrics in time-series databases, and provides real-time alerts to administrators.

### Core Features
- **Real-time Device Monitoring**: Collects CPU, RAM, Disk, and Network metrics via SNMP
- **Network Topology Discovery**: Auto-discovers and visualizes network topology
- **Alert Engine**: Real-time alert generation based on configurable thresholds
- **WebSocket Alerts**: Push alerts to frontend without polling
- **Multi-user Access**: Role-based authentication (Admin, User)
- **Time-series Storage**: Historical data storage using InfluxDB
- **RESTful API**: Complete REST API for integration

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React + Vite)                      │
│  Pages: Dashboard | Devices | Alerts | Topology | Settings | Admin  │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                          HTTP / WebSocket
                                    │
┌─────────────────────────────────────────────────────────────────────┐
│                       BACKEND (FastAPI - Python)                    │
│  Routes: /api/devices | /api/alerts | /api/metrics | /api/auth      │
│  WebSocket: /ws/alerts                                             │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
              ┌─────▼─────┐  ┌─────▼─────┐  ┌─────▼─────┐
              │ Collectors │  │   Core    │  │ Database  │
              │  Service   │  │  Service  │  │  (Postgres)│
              └─────┬─────┘  └─────┬─────┘  └───────────┘
                    │               │
              ┌─────▼─────┐  ┌─────▼─────┐
              │ SNMP      │  │ InfluxDB  │
              │ Devices   │  │ (Metrics) │
              └───────────┘  └───────────┘
```

### Data Flow
1. **Collectors** poll network devices via SNMP
2. Collected data is normalized and sent to **Core** via gRPC
3. **Core** processes data, stores in **InfluxDB**, generates alerts
4. **Backend** serves data to **Frontend** via REST API and WebSocket

---

## Directory Structure

```
NEXORA/
├── backend/                  # FastAPI REST API Server
├── frontend/                 # React + TypeScript Web UI
├── collectors/               # SNMP Data Collectors
├── core/                     # Data Processing & Alert Engine
├── docker/                   # Docker helper scripts
├── nexora-db-package/        # Database operations package
├── v_labs/                   # Virtual lab configurations
├── docker_compose_full.yml   # Full stack Docker Compose
├── .env                      # Environment configuration
└── nexora.md                 # This documentation
```

---

## Frontend

**Technology Stack**: React 18, TypeScript, Vite, Tailwind CSS, shadcn/ui

### Directory Structure

```
frontend/
├── src/
│   ├── main.tsx              # React entry point
│   ├── app/
│   │   ├── App.tsx           # Root component
│   │   ├── routes.tsx        # Routing configuration
│   │   ├── api/
│   │   │   └── api.ts        # API client (Axios wrapper)
│   │   ├── context/
│   │   │   └── AuthContext.tsx  # Authentication context
│   │   ├── hooks/
│   │   │   ├── useAlertWebSocket.ts   # WebSocket hook for real-time alerts
│   │   │   └── useApi.ts               # API hook with error handling
│   │   ├── components/
│   │   │   ├── Layout.tsx         # Main application layout with sidebar
│   │   │   ├── StatCard.tsx       # Statistics card component
│   │   │   └── ui/                # shadcn/ui components (50+ components)
│   │   ├── pages/
│   │   │   ├── LoginPage.tsx      # Login/Authentication page
│   │   │   ├── DashboardPage.tsx  # Dashboard with stats and charts
│   │   │   ├── DevicesPage.tsx   # Device list and management
│   │   │   ├── AlertsPage.tsx     # Real-time alerts with WebSocket
│   │   │   ├── TopologyPage.tsx   # Network topology visualization
│   │   │   ├── MetricsPage.tsx   # Detailed metrics view
│   │   │   ├── SettingsPage.tsx  # User settings (non-admin)
│   │   │   └── AdminPage.tsx      # Admin-only user management
│   │   └── utils/
│   │       └── logger.ts         # Frontend logging utility
│   ├── styles/
│   │   ├── tailwind.css          # Tailwind CSS configuration
│   │   ├── theme.css             # Custom theme variables
│   │   └── fonts.css             # Font definitions
│   └── imports/
│       └── pasted_text/
│           └── nexora-frontend-guide.md  # Development guide
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── nginx.conf                  # Nginx configuration for production
```

### Key Components

#### Pages

| Page | File | Description |
|------|------|-------------|
| Login | `pages/LoginPage.tsx` | User authentication with JWT |
| Dashboard | `pages/DashboardPage.tsx` | Overview stats, charts, recent alerts |
| Devices | `pages/DevicesPage.tsx` | Device list with filtering, CRUD operations |
| Alerts | `pages/AlertsPage.tsx` | Real-time alerts via WebSocket |
| Topology | `pages/TopologyPage.tsx` | Network topology visualization |
| Metrics | `pages/MetricsPage.tsx` | Historical metrics charts |
| Settings | `pages/SettingsPage.tsx` | User preferences (non-admin) |
| Admin | `pages/AdminPage.tsx` | User management (admin only) |

#### Hooks

| Hook | File | Purpose |
|------|------|---------|
| `useAlertWebSocket` | `hooks/useAlertWebSocket.ts` | Connect to WebSocket, receive real-time alerts |
| `useApi` | `hooks/useApi.ts` | Wrapper for API calls with loading/error states |
| `useAuth` | `context/AuthContext.tsx` | Authentication state management |

#### API Client (`api/api.ts`)

The API client provides TypeScript interfaces for all API endpoints:

```typescript
// Key interfaces
export interface Device {
  id?: number;
  name: string;
  ip_address: string;
  mac_address: string;
  device_type?: string;
  vendor?: string;
  status: 'UP' | 'DOWN';
  // ... more fields
}

export interface Alert {
  id?: number;
  device?: string;
  device_hostname?: string;
  device_ip?: string;
  device_mac?: string;
  severity?: string;
  alert_level?: string;
  message?: string;
  alert_message?: string;
  timestamp?: string;
  acknowledged?: boolean;
}

export interface Metrics {
  device_id: number;
  timestamp: string;
  cpu_usage?: number;
  ram_usage?: number;
  disk_usage?: number;
  latency?: number;
}
```

---

## Backend

**Technology Stack**: Python 3.9, FastAPI, SQLAlchemy, PostgreSQL, JWT, WebSocket

### Directory Structure

```
backend/
├── main.py                   # FastAPI application entry point
├── config.py                 # Configuration management
├── requirements.txt         # Python dependencies
├── Dockerfile               # Docker image build
├── api/
│   ├── routes/
│   │   ├── auth.py          # Authentication endpoints
│   │   ├── users.py         # User management endpoints
│   │   ├── devices.py       # Device CRUD endpoints
│   │   ├── alerts.py        # Alert endpoints
│   │   ├── metrics.py       # Metrics endpoints
│   │   ├── dashboard.py    # Dashboard data endpoints
│   │   ├── alerts_ws.py     # WebSocket alert routes
│   │   └── alert_broadcast.py  # Alert broadcast management
│   └── websocket/
│       └── alerts_ws.py     # WebSocket manager for real-time alerts
├── security/
│   ├── jwt.py               # JWT token handling
│   └── password.py          # Password hashing (bcrypt)
├── services/
│   └── auth_service.py      # Authentication business logic
├── time_series_readers/
│   └── influx_reader.py     # InfluxDB data reader
├── utils/
│   ├── admin.py             # Admin utilities
│   └── logger.py            # Logging configuration
└── __init__.py
```

### Key Modules

#### Main Application (`main.py`)

```python
# FastAPI application setup
app = FastAPI(title="NEXORA API", version="1.0.0")

# Include routers
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(devices_router, prefix="/api/devices", tags=["devices"])
app.include_router(alerts_router, prefix="/api/alerts", tags=["alerts"])
app.include_router(metrics_router, prefix="/api/metrics", tags=["metrics"])
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(users_router, prefix="/api/users", tags=["users"])

# WebSocket endpoint
app.add_api_websocket_route("/ws/alerts", websocket_endpoint)
```

#### Authentication (`security/jwt.py`)

- JWT token generation and validation
- Token payload includes: user_id, username, role
- Token expiration: configurable (default 24 hours)

```python
def create_access_token(data: dict) -> str
def verify_token(token: str) -> dict
def get_current_user(credentials: HTTPBearer) -> User
```

#### API Routes

| Route | File | Methods | Description |
|-------|------|---------|-------------|
| `/api/auth/login` | `routes/auth.py` | POST | User login |
| `/api/auth/logout` | `routes/auth.py` | POST | User logout |
| `/api/devices` | `routes/devices.py` | GET, POST | List/Create devices |
| `/api/devices/{id}` | `routes/devices.py` | GET, PUT, DELETE | Device CRUD |
| `/api/alerts` | `routes/alerts.py` | GET | List alerts with pagination |
| `/api/alerts/{id}/acknowledge` | `routes/alerts.py` | POST | Acknowledge alert |
| `/api/metrics` | `routes/metrics.py` | GET | Get device metrics |
| `/api/metrics/history` | `routes/metrics.py` | GET | Historical metrics |
| `/api/dashboard/stats` | `routes/dashboard.py` | GET | Dashboard statistics |
| `/api/dashboard/recent-alerts` | `routes/dashboard.py` | GET | Recent alerts |
| `/api/users` | `routes/users.py` | GET, POST | User management (admin) |
| `/api/users/{id}` | `routes/users.py` | GET, PUT, DELETE | User CRUD |
| `/ws/alerts` | `routes/alerts_ws.py` | WebSocket | Real-time alert stream |

#### WebSocket Manager (`api/websocket/alerts_ws.py`)

```python
class AlertWebSocketManager:
    async def connect(websocket)
    async def disconnect(websocket)
    async def send_personal_message(message, websocket)
    async def broadcast(alert_data)  # Broadcast to all connected clients
```

---

## Collectors Service

**Technology Stack**: Python 3.9, PySNMP, gRPC, SQLite

The collectors service is responsible for polling network devices via SNMP and sending data to the core service.

### Directory Structure

```
collectors/
├── main.py                   # Collector service entry point
├── requirements.txt          # Python dependencies
├── Dockerfile               # Docker image build
├── engines/
│   └── snmp_engine/
│       ├── snmp_collector.py    # SNMP polling engine
│       └── utils/
│           ├── detect_type.py   # Device type detection
│           └── detect_vendor.py  # Vendor detection (Cisco, HP, etc.)
├── scheduler/
│   ├── scheduler.py         # Polling scheduler
│   └── heartbeat.py         # Collector heartbeat
├── transport/
│   ├── grpc_client.py       # gRPC client to core
│   └── check_core_health.py # Health check
├── buffer/
│   ├── buffer_manager.py    # Buffer management
│   ├── memory_queue.py      # In-memory queue
│   └── dbs_buffer/
│       ├── disk_queue.py    # Persistent disk queue
│       └── database_model.py # SQLite models
├── normalizer/
│   └── normalizer.py        # Data normalization
├── grpc_api/
│   ├── core_ingest_pb2.py      # Generated gRPC code
│   ├── core_ingest_pb2_grpc.py # Generated gRPC service
│   └── proto/
│       └── core_ingest.proto   # Protocol buffer definition
├── config/
│   ├── devices.yml          # Device configuration
│   ├── snmpd.conf           # SNMP daemon config
│   └── db_config/
│       └── database.py      # SQLite configuration
└── utils/
    ├── devices_.py          # Device utilities
    ├── default_data.py      # Default values
    └── logger.py            # Logging
```

### Key Components

#### SNMP Collector (`engines/snmp_engine/snmp_collector.py`)

The main SNMP polling engine that:
- Collects metrics from network devices
- Supports SNMP v1/v2c/v3
- Polls OIDs for CPU, RAM, Disk, Interface statistics

```python
class SNMPCollector:
    async def collect(device: Device) -> Metrics
    async def get_cpu_usage(device_ip: str) -> float
    async def get_ram_usage(device_ip: str) -> float
    async def get_disk_usage(device_ip: str) -> float
    async def get_interface_stats(device_ip: str) -> dict
```

#### Device Detection

- `detect_type.py`: Identifies device type (Router, Switch, Server, etc.)
- `detect_vendor.py`: Identifies vendor (Cisco, HP, Dell, etc.) using SNMP sysObjectID

#### Scheduler (`scheduler/scheduler.py`)

Manages polling intervals for different devices:
```python
class PollingScheduler:
    def add_job(device_id, interval_seconds)
    def remove_job(device_id)
    def start()
    def stop()
```

#### Data Buffer (`buffer/`)

Implements queuing to handle network issues:
- `memory_queue.py`: Fast in-memory queue for normal operation
- `dbs_buffer/disk_queue.py`: Persistent queue for resilience

#### gRPC Client (`transport/grpc_client.py`)

Sends collected metrics to Core service:
```python
class GRPCClient:
    async def send_metrics(metrics: MetricsRequest)
    async def check_health() -> bool
```

---

## Core Service

**Technology Stack**: Python 3.9, FastAPI, InfluxDB, PostgreSQL, gRPC

The core service handles data ingestion, processing, storage, and alert generation.

### Directory Structure

```
core/
├── requirements.txt          # Python dependencies
├── Dockerfile                # Docker image build
├── alert_engine/
│   ├── CoreAlertEngine.py    # Alert generation and management
│   └── README.md             # Alert engine documentation
├── buffer/
│   └── ingest_queue.py       # Ingest queue
├── configs/
│   └── database.py           # Database configuration
├── grpc_api/
│   ├── core_ingest_pb2.py      # Generated gRPC code
│   ├── core_ingest_pb2_grpc.py # Generated gRPC service
│   └── proto/
│       └── core_ingest.proto   # Protocol buffer definition
├── ingester/
│   ├── ingest_service.py     # Data ingestion service
│   └── README.md             # Ingester documentation
├── processer/
│   ├── normalizer.py         # Data normalization
│   └── README.md             # Processer documentation
├── time_series/
│   ├── client/
│   │   ├── client.py         # InfluxDB client wrapper
│   │   └── healthcheck.py    # Health check
│   ├── config/
│   │   └── settings.py       # InfluxDB settings
│   ├── models/
│   │   ├── device_health_model.py  # Device health model
│   │   └── main_model.py     # Main data model
│   ├── writers/
│   │   └── device_health_writer.py # Write metrics to InfluxDB
│   └── README.md             # Time series documentation
├── writer/
│   ├── data_writer.py        # Generic data writer
│   └── metadata_writer.py    # Metadata writer
└── utils/
    └── logger.py             # Logging
```

### Key Components

#### Alert Engine (`alert_engine/CoreAlertEngine.py`)

Generates alerts based on thresholds and broadcasts via WebSocket:

```python
class AlertEngine:
    async def check_thresholds(metrics: Metrics) -> List[Alert]
    async def create_alert(alert_data: dict) -> Alert
    async def broadcast_alert(alert: Alert)  # Send to WebSocket
    def load_thresholds()  # Load alert thresholds from config
```

**Alert Processing:**
- Monitors CPU, RAM, Disk, Latency against thresholds
- Supports multiple severity levels: CRITICAL, HIGH, MID, LOW, INFO
- Generates alerts when thresholds are exceeded
- Broadcasts alerts to connected frontend clients via WebSocket

#### Ingest Service (`ingester/ingest_service.py`)

Receives metrics from collectors via gRPC:
```python
class IngestService:
    async def ingest_metrics(request: MetricsRequest)
    async def process_metrics(metrics: Metrics)
    async def store_metrics(metrics: Metrics)
```

#### Normalizer (`processer/normalizer.py`)

Normalizes raw SNMP data to standard format:
```python
def normalize_device_data(raw_data: dict) -> NormalizedData
def normalize_metrics(raw_metrics: dict) -> Metrics
```

#### Time-Series Client (`time_series/client/client.py`)

InfluxDB client for time-series data storage:
```python
class InfluxDBClient:
    async def write_metrics(measurement: str, tags: dict, fields: dict)
    async def query_metrics(query: str) -> List[dict]
    async def get_device_history(device_id: int, duration: str) -> List[dict]
```

---

## Database Schema

### PostgreSQL (Primary Database)

The system uses PostgreSQL for persistent storage of devices, users, alerts, and configurations.

#### Core Tables

**users**
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    role VARCHAR(50) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**devices**
```sql
CREATE TABLE devices (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    ip_address VARCHAR(45) NOT NULL,
    mac_address VARCHAR(17),
    device_type VARCHAR(100),
    vendor VARCHAR(100),
    status VARCHAR(20) DEFAULT 'UNKNOWN',
    hostname VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**alerts**
```sql
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    device_id INTEGER REFERENCES devices(id),
    message TEXT,
    alert_level VARCHAR(50),
    severity VARCHAR(50),
    metric_name VARCHAR(100),
    value FLOAT,
    threshold FLOAT,
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by INTEGER REFERENCES users(id),
    acknowledged_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### InfluxDB (Time-Series Database)

Used for storing historical metrics data:

**Measurements:**
- `device_cpu`: CPU usage over time
- `device_ram`: RAM usage over time
- `device_disk`: Disk usage over time
- `device_latency`: Network latency over time

**Tags:** `device_id`, `device_name`, `device_ip`
**Fields:** `value`, `status`

---

## Docker Configuration

### docker_compose_full.yml

The full stack deployment includes:

| Service | Image | Ports | Description |
|---------|-------|-------|-------------|
| `postgres` | postgres:15 | 5432:5432 | Primary database |
| `influxdb` | influxdb:2.7 | 8086:8086 | Time-series database |
| `core` | nexora-core:latest | 50051:50051 | Core processing service |
| `collectors` | nexora-collectors:latest | - | SNMP collectors |
| `backend` | nexora-backend:latest | 8000:80, 8001:443 | REST API & WebSocket |
| `frontend` | nexora-frontend:latest | 3000:80 | Web UI |

### Docker Scripts

- `docker/create_network.sh`: Create Docker network
- `docker/create_network.bat`: Windows version
- `docker/init_postgres.sql`: Database initialization

---

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | User login |
| POST | `/api/auth/logout` | User logout |

### Devices
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/devices` | List all devices |
| POST | `/api/devices` | Create new device |
| GET | `/api/devices/{id}` | Get device details |
| PUT | `/api/devices/{id}` | Update device |
| DELETE | `/api/devices/{id}` | Delete device |

### Alerts
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/alerts` | List alerts (paginated) |
| POST | `/api/alerts/{id}/acknowledge` | Acknowledge alert |
| GET | `/api/alerts/stats` | Get alert statistics |

### Metrics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/metrics/{device_id}` | Get current metrics |
| GET | `/api/metrics/{device_id}/history` | Historical metrics |

### Dashboard
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dashboard/stats` | Dashboard statistics |
| GET | `/api/dashboard/recent-alerts` | Recent alerts |
| GET | `/api/dashboard/top-devices` | Top devices by metric |

### Users (Admin Only)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/users` | List all users |
| POST | `/api/users` | Create new user |
| GET | `/api/users/{id}` | Get user details |
| PUT | `/api/users/{id}` | Update user |
| DELETE | `/api/users/{id}` | Delete user |

### WebSocket
| Endpoint | Description |
|----------|-------------|
| `/ws/alerts` | Real-time alert stream |

---

## WebSocket Communication

### Alert WebSocket Flow

```
┌──────────────┐     Connect      ┌──────────────┐
│   Frontend   │ ────────────────►│    Backend    │
│  (React App)  │                  │  (FastAPI)    │
└──────────────┘                  └───────┬───────┘
                                         │
                                  ┌──────▼──────┐
                                  │   Core      │
                                  │Alert Engine │
                                  └──────┬──────┘
                                         │
                                  ┌──────▼──────┐
                                  │  Collectors │
                                  │ (SNMP Data) │
                                  └─────────────┘
```

### WebSocket Message Format

```json
{
  "id": 123,
  "message": "High CPU usage on server2win",
  "alert_level": "CRITICAL",
  "severity": "HIGH",
  "device_hostname": "server2win",
  "device_ip": "172.18.0.8",
  "device_mac": "55:b6:6c:b4:4a:50",
  "timestamp": "2026-03-23T10:00:21Z"
}
```

### Frontend WebSocket Hook

```typescript
const { isConnected, lastAlert, connect, disconnect } = useAlertWebSocket({
  onAlert: (alert) => {
    // Add alert to list
    setAlerts(prev => [alert, ...prev]);
  }
});
```

---

## Key Technologies

### Frontend
- **React 18**: UI framework
- **TypeScript**: Type safety
- **Vite**: Build tool
- **Tailwind CSS**: Styling
- **shadcn/ui**: Component library
- **Recharts**: Charting library
- **React Router**: Navigation
- **Axios**: HTTP client

### Backend
- **FastAPI**: Web framework
- **SQLAlchemy**: ORM
- **Pydantic**: Data validation
- **python-jose**: JWT handling
- **bcrypt**: Password hashing
- **uvicorn**: ASGI server

### Collectors
- **PySNMP**: SNMP polling
- **grpcio**: gRPC client
- **APScheduler**: Job scheduling

### Core
- **influxdb-client**: InfluxDB connection
- **websocket**: WebSocket broadcasting

### Database
- **PostgreSQL**: Primary database
- **InfluxDB**: Time-series data

### Infrastructure
- **Docker**: Containerization
- **Docker Compose**: Orchestration
- **Nginx**: Reverse proxy

---

## Configuration

### Environment Variables (.env)

```env
# Database
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=nexora
POSTGRES_PASSWORD=secret
POSTGRES_DB=nexora

# InfluxDB
INFLUXDB_URL=http://influxdb:8086
INFLUXDB_TOKEN=my-super-secret-token
INFLUXDB_ORG=nexora
INFLUXDB_BUCKET=nexora

# Backend
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Collectors
SNMP_COMMUNITY=public
POLLING_INTERVAL=60

# Core
ALERT_THRESHOLDS_PATH=/config/thresholds.yml
```

---

## Security

### Authentication Flow
1. User submits credentials to `/api/auth/login`
2. Backend validates and returns JWT token
3. Frontend stores token in localStorage
4. Subsequent requests include `Authorization: Bearer <token>`
5. Backend validates token for each protected endpoint

### Role-Based Access
- **Admin**: Full access including user management
- **User**: Read access to devices, metrics, alerts; limited settings

---

## Development Workflow

### Running Locally
```bash
# Start full stack
docker-compose -f docker_compose_full.yml up -d

# View logs
docker-compose -f docker_compose_full.yml logs -f

# Stop stack
docker-compose -f docker_compose_full.yml down
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

### Backend Development
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

---

## Summary

NEXORA is a complete network monitoring solution built with modern technologies:

- **Scalable Architecture**: Microservices-based with Docker containerization
- **Real-time Processing**: WebSocket-based real-time alerts
- **Time-series Storage**: InfluxDB for historical metrics
- **Comprehensive Monitoring**: SNMP-based device polling
- **User-friendly UI**: React-based responsive interface
- **Production-ready**: PostgreSQL, JWT auth, role-based access

The system can be deployed as a full stack using Docker Compose or individual services can be run separately for development or scaling purposes.