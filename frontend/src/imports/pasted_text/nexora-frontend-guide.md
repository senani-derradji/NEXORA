# NEXORA Frontend Development Prompt

You are tasked with building the frontend for **NEXORA**, a network observability and monitoring platform. This document provides comprehensive guidance for developing the complete frontend application.

---

## 1. Project Overview

**NEXORA** is a FastAPI-based network observability platform that monitors devices, collects metrics (CPU, RAM, disk, network, latency), manages alerts, and provides a dashboard for network administrators.

### Technology Stack
- **Frontend Framework**: React (recommended) or Vanilla JavaScript
- **Backend**: FastAPI running on `backend:8000` (Docker container)
- **Database**: PostgreSQL + InfluxDB (time-series metrics)
- **Authentication**: JWT-based OAuth2
- **Styling**: Tailwind CSS or Bootstrap

### Docker Configuration
The backend runs in a Docker container named `backend` on an internal network. All API calls should be made to:
```
http://backend:8000
```
For local development, you may use `http://localhost:8000`

---

## 2. Authentication System

### Login Endpoint
```
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=your_username&password=your_password
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "admin@nexora",
    "role": "admin"
  }
}
```

### Register Endpoint
```
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

### Check Auth Endpoint
```
GET /auth/check-auth
Headers: Authorization: Bearer <token>
```

**Response:**
```json
{
  "authenticated": true,
  "username": "admin@nexora",
  "role": "admin"
}
```

### Default Credentials
- **Admin**: `admin@nexora` / `admin`
- **Secondary Admin**: `derradji@nexora` / `admin`

---

## 3. Complete API Reference

### Base URL
```
http://backend:8000
```

### All Endpoints

#### 3.1 System Health
```
GET /health
```
Returns: `{"status": "ok", "service": "nexora-backend"}`

#### 3.2 Authentication (`/auth`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/register` | Public | Register new user |
| POST | `/auth/login` | Public | Login, returns JWT token |
| GET | `/auth/check-auth` | Bearer | Verify current token |

#### 3.3 Users (`/users`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/users/me` | Bearer | Get current user info |
| PUT | `/users/me` | Bearer | Update current user profile |
| POST | `/users/change-password` | Bearer | Change password |
| GET | `/users/` | Admin | List all users |
| DELETE | `/users/{user_id}` | Admin | Delete user |

**GET /users/me Response:**
```json
{
  "id": 1,
  "email": "admin@nexora",
  "role": "admin",
  "username": "admin"
}
```

#### 3.4 Devices (`/devices`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/devices/count` | Public | Get total device count |
| POST | `/devices/create` | Admin | Create new device |
| GET | `/devices/` | Admin/Viewer | List all devices |
| GET | `/devices/{mac_address}` | Admin/Viewer | Get device by MAC |
| PUT | `/devices/{mac_address}` | Admin | Update device |
| DELETE | `/devices/{mac_address}` | Admin | Delete device |

**Device Create Request:**
```json
{
  "hostname": "router-01",
  "device_type": "router",
  "ip_address": "192.168.1.1",
  "mac_address": "00:11:22:33:44:55"
}
```

**GET /devices/ Response (List):**
```json
[
  {
    "id": 1,
    "hostname": "gateway-router",
    "device_type": "router",
    "ip_address": "192.168.1.1",
    "mac_address": "00:11:22:33:44:55",
    "status": 1,
    "status_text": "UP",
    "last_seen": "2026-03-17T10:30:00",
    "interval": 30
  }
]
```

#### 3.5 Alerts (`/alerts`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/alerts/` | Bearer | List all alerts (paginated) |
| GET | `/alerts/stats` | Bearer | Get alert statistics |
| GET | `/alerts/{device_hostname}` | Bearer | Get alerts for device |
| DELETE | `/alerts/{device_hostname}` | Bearer | Delete alerts for device |

**GET /alerts/ Parameters:**
- `page` (query): Page number (default: 1)
- `page_size` (query): Items per page (default: 20, max: 100)

**GET /alerts/ Response:**
```json
{
  "alerts": [
    {
      "id": 1,
      "message": "CPU usage high",
      "alert_message": "CPU usage high",
      "severity": "CRITICAL",
      "alert_level": "CRITICAL",
      "timestamp": "2026-03-17T10:30:00",
      "created_at": "2026-03-17T10:30:00",
      "alert_time": "2026-03-17T10:30:00",
      "device_id": 1
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5,
  "has_next": true,
  "has_prev": false
}
```

**GET /alerts/stats Response:**
```json
{
  "critical": 5,
  "warnings": 10,
  "info": 15,
  "total": 30
}
```

#### 3.6 Dashboard (`/dashboard`)

All dashboard endpoints require Bearer token authentication (admin or viewer role).

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/dashboard/summary` | Bearer | Get dashboard summary |
| GET | `/dashboard/device-metrics` | Bearer | Get all device metrics |
| GET | `/dashboard/topology` | Bearer | Get network topology |

**GET /dashboard/summary Response:**
```json
{
  "total_devices": 10,
  "online_devices": 8,
  "offline_devices": 2,
  "active_alerts": 5,
  "critical_alerts": 2,
  "warning_alerts": 3,
  "system_health": 80.0,
  "avg_cpu": 45.5,
  "avg_ram": 62.3,
  "avg_disk": 35.8,
  "avg_latency": 12.5
}
```

**GET /dashboard/device-metrics Response:**
```json
{
  "devices": [
    {
      "id": 1,
      "hostname": "gateway-router",
      "ip_address": "192.168.1.1",
      "mac_address": "00:11:22:33:44:55",
      "device_type": "router",
      "status": "UP",
      "status_value": 1,
      "status_text": "UP",
      "last_seen": "2026-03-17T10:30:00",
      "cpu_usage": 45.5,
      "ram_usage": 62.3,
      "disk_usage": 35.8,
      "latency": 12.5
    }
  ]
}
```

**GET /dashboard/topology Response:**
```json
{
  "core": {
    "id": "core",
    "name": "Core",
    "type": "core",
    "status": "online",
    "ip": "172.18.0.30"
  },
  "collector": {
    "id": "collector",
    "name": "Collector",
    "type": "collector",
    "status": "online",
    "ip": "172.18.0.40"
  },
  "databases": [
    {
      "id": "postgres",
      "name": "PostgreSQL",
      "type": "postgres",
      "status": "online",
      "ip": "172.18.0.20"
    },
    {
      "id": "influxdb",
      "name": "InfluxDB",
      "type": "influxdb",
      "status": "online",
      "ip": "172.18.0.10"
    }
  ],
  "devices": [
    {
      "id": "1",
      "name": "gateway-router",
      "type": "device",
      "status": "online",
      "ip": "192.168.1.1",
      "mac": "00:11:22:33:44:55",
      "device_type": "router"
    }
  ]
}
```

#### 3.7 Metrics (`/metrics`)

All metrics endpoints require Bearer token authentication (admin or viewer role).

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/metrics/cpu` | Bearer | CPU usage metrics |
| GET | `/metrics/ram` | Bearer | RAM usage metrics |
| GET | `/metrics/disk` | Bearer | Disk usage metrics |
| GET | `/metrics/network` | Bearer | Network I/O metrics |
| GET | `/metrics/latency` | Bearer | Latency metrics |
| GET | `/metrics/packet-loss` | Bearer | Packet loss metrics |
| GET | `/metrics/all` | Bearer | All metrics at once |

**Metrics Parameters:**
- `duration` (query): Time range - `5m`, `15m`, `30m`, `1h`, `6h`, `24h`, `7d` (default: `1h`)
- `device` (query): Filter by device hostname (optional)

**GET /metrics/cpu Response:**
```json
{
  "metric": "cpu",
  "duration": "1h",
  "devices": [
    {
      "device": "gateway-router",
      "data": [
        {"timestamp": "2026-03-17T10:00:00Z", "value": 45.5},
        {"timestamp": "2026-03-17T10:05:00Z", "value": 46.2}
      ]
    }
  ]
}
```

**GET /metrics/all Response:**
```json
{
  "metric": "all",
  "duration": "1h",
  "cpu": {"metric": "cpu", "devices": [...]},
  "ram": {"metric": "ram", "devices": [...]},
  "disk": {"metric": "disk", "devices": [...]},
  "latency": {"metric": "latency", "devices": [...]},
  "packet_loss": {"metric": "packet_loss", "devices": [...]},
  "network": {"metric": "network", "devices": [...]}
}
```

---

## 4. Frontend Requirements

### 4.1 Pages Required

1. **Login Page**
   - Username/password form
   - Remember me option
   - Error handling for invalid credentials

2. **Dashboard Page**
   - Summary cards (total devices, online, offline, alerts)
   - System health gauge
   - Device table with status indicators
   - Quick metrics charts (CPU, RAM)
   - Auto-refresh capability

3. **Devices Page**
   - Full device list with search/filter
   - Device details modal
   - Add/Edit/Delete device (admin only)
   - Device status indicators
   - Last seen timestamps

4. **Alerts Page**
   - Alert list with severity badges (CRITICAL, WARNING, INFO)
   - Filter by severity
   - Pagination
   - Alert statistics summary

5. **Topology Page**
   - Visual network topology diagram
   - Core, Collector, Databases shown
   - All monitored devices
   - Online/offline status indicators

6. **Metrics Page**
   - Time-series charts for each metric type
   - Duration selector (5m, 15m, 30m, 1h, 6h, 24h, 7d)
   - Per-device or aggregate view
   - CPU, RAM, Disk, Network, Latency, Packet Loss

7. **Settings Page**
   - User profile update
   - Password change
   - Theme toggle (light/dark)

8. **Admin Panel** (Admin only)
   - User management (list, add, delete)
   - System configuration

### 4.2 UI/UX Requirements

- **Responsive Design**: Works on desktop and mobile
- **Dark/Light Theme**: Toggle between themes
- **Loading States**: Show spinners during API calls
- **Error Handling**: Display user-friendly error messages
- **Real-time Updates**: Auto-refresh dashboard data

### 4.3 Authentication Flow

1. User enters credentials on login page
2. Call `POST /auth/login` with form data
3. Store JWT token in localStorage
4. Include token in Authorization header for subsequent requests
5. Redirect to dashboard on success
6. Show error message on failure
7. Check auth on app load via `GET /auth/check-auth`

---

## 5. API Service Implementation

### JavaScript Example

```javascript
const API_BASE_URL = 'http://backend:8000';

const API = {
  setToken(token) {
    localStorage.setItem('token', token);
  },

  getHeaders() {
    const token = localStorage.getItem('token');
    const headers = { 'Content-Type': 'application/json' };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
  },

  async request(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const config = {
      headers: this.getHeaders(),
      ...options
    };

    const response = await fetch(url, config);

    if (response.status === 401) {
      this.logout();
      window.location.reload();
      throw new Error('Unauthorized');
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `HTTP error ${response.status}`);
    }

    return response.json();
  },

  auth: {
    async login(username, password) {
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);

      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'Login failed');
      }

      const data = await response.json();
      API.setToken(data.access_token);
      return data;
    },

    async checkAuth() {
      return API.request('/auth/check-auth');
    }
  },

  dashboard: {
    async getSummary() {
      return API.request('/dashboard/summary');
    },
    async getDeviceMetrics() {
      return API.request('/dashboard/device-metrics');
    },
    async getTopology() {
      return API.request('/dashboard/topology');
    }
  },

  devices: {
    async getAll() {
      return API.request('/devices/');
    },
    async create(deviceData) {
      return API.request('/devices/create', {
        method: 'POST',
        body: JSON.stringify(deviceData)
      });
    },
    async delete(macAddress) {
      return API.request(`/devices/${macAddress}`, { method: 'DELETE' });
    }
  },

  alerts: {
    async getAll(page = 1, pageSize = 100) {
      return API.request(`/alerts/?page=${page}&page_size=${pageSize}`);
    },
    async getStats() {
      return API.request('/alerts/stats');
    }
  },

  metrics: {
    async getCpu(duration = '1h') {
      return API.request(`/metrics/cpu?duration=${duration}`);
    },
    async getAll(duration = '1h') {
      return API.request(`/metrics/all?duration=${duration}`);
    }
  },

  logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  }
};
```

---

## 6. Important Notes

1. **Docker Network**: The frontend must communicate with `backend:8000` when running in Docker. Update the API base URL accordingly.

2. **Authentication**: Most endpoints require a valid JWT token in the Authorization header. The login endpoint uses OAuth2 password flow with form-encoded data, not JSON.

3. **Roles**: Two user roles exist - `admin` and `viewer`. Admin has full access including device CRUD. Viewer can only view data.

4. **Device Status**: Device status is calculated based on the `status` field and `last_seen` timestamp. If `status` is "UP" and `last_seen` is within 30 seconds, device is online.

5. **Alert Levels**: Alert severity levels are CRITICAL/HIGH, WARNING/MID, and INFO.

6. **Time Ranges**: Metrics support 5m, 15m, 30m, 1h, 6h, 24h, and 7d durations.

---

## 7. Deliverables

Build a complete frontend application that:

1. Provides a clean, modern login interface
2. Shows dashboard with real-time metrics and device status
3. Lists all devices with CRUD operations (admin only for create/update/delete)
4. Displays alerts with filtering and pagination
5. Shows network topology visualization
6. Provides detailed metrics charts with time range selection
7. Includes user settings and profile management
8. Has admin panel for user management (admin role only)
9. Handles authentication securely
10. Works seamlessly in Docker environment with backend:8000

Use modern UI libraries like Chart.js for metrics visualization, and ensure responsive design for all screen sizes.