# NEXORA Frontend (VIBE CODING - Created by AI)

> **React-based observability platform frontend** — v0.2.0
> Modern, responsive dashboard for monitoring network devices, alerts, and metrics in real-time.

---

## Architecture Overview

```
frontend/
├── src/
│   ├── main.tsx                    # App entry point — React root render
│   ├── app/
│   │   ├── App.tsx                 # Main app component
│   │   ├── routes.tsx              # React Router configuration with theme provider
│   │   ├── api/
│   │   │   └── api.ts              # API client — all backend API calls (auth, devices, alerts, metrics, dashboard)
│   │   ├── components/
│   │   │   ├── Layout.tsx          # Main layout with sidebar navigation
│   │   │   ├── StatCard.tsx        # Reusable stat card component
│   │   │   └── ui/                 # Shadcn/ui component library (50+ components)
│   │   ├── context/
│   │   │   └── AuthContext.tsx      # Authentication context provider
│   │   ├── hooks/
│   │   │   ├── useAlertWebSocket.ts # WebSocket hook for real-time alerts
│   │   │   └── useApi.ts           # Generic API hook
│   │   ├── pages/
│   │   │   ├── LoginPage.tsx       # User authentication page
│   │   │   ├── DashboardPage.tsx   # Main dashboard with device overview and metrics
│   │   │   ├── AlertsPage.tsx      # Alert management and monitoring
│   │   │   ├── DevicesPage.tsx     # Device inventory and management
│   │   │   ├── TopologyPage.tsx    # Network topology visualization
│   │   │   ├── MetricsPage.tsx     # Detailed metrics charts and graphs
│   │   │   ├── SettingsPage.tsx    # User settings and preferences
│   │   │   └── AdminPage.tsx       # Admin panel for user management
│   │   └── utils/
│   │       └── logger.ts           # Logging utility
│   ├── imports/
│   │   └── pasted_text/
│   │       └── nexora-frontend-guide.md  # Frontend development guide
│   └── styles/
│       ├── index.css               # Global styles
│       ├── tailwind.css            # Tailwind CSS imports
│       └── theme.css               # Theme variables and custom styles
├── public/                         # Static assets
├── package.json                    # Dependencies and scripts
├── vite.config.ts                  # Vite build configuration
├── tailwind.config.js              # Tailwind CSS configuration
├── postcss.config.mjs              # PostCSS configuration
├── nginx.conf                      # Nginx configuration for production
└── Dockerfile                      # Container image definition
```

---

## Features

### Authentication
- JWT-based authentication with token storage
- Login/logout functionality
- Protected routes with authentication guards
- User profile management

### Dashboard
- Real-time device status overview
- System health metrics (CPU, RAM, disk, latency)
- Active alerts summary (critical, warnings)
- Device count statistics (online/offline)
- Network topology visualization

### Device Management
- Device inventory with search and filter
- Device status monitoring (online/offline)
- Device details (IP, MAC, type, last seen)
- Create, update, and delete devices (admin only)

### Alerts
- Real-time alert monitoring via WebSocket
- Alert statistics and filtering
- Alert history with pagination
- Alert acknowledgment and deletion
- Critical and warning alert highlighting

### Metrics
- Time-series metric visualization
- CPU, RAM, disk usage charts
- Network traffic (in/out bytes)
- Latency and packet loss monitoring
- Configurable time ranges (1m, 5m, 15m, 30m, 1h, 6h, 24h, 7d)
- Per-device metric filtering

### Topology
- Interactive network topology map
- Device status visualization
- Core, collector, and database node display
- Real-time status updates

### Settings
- Theme switching (dark/light mode)
- User preferences persistence
- Profile management

### Admin Panel
- User management (list, delete users)
- Role-based access control (admin/viewer)

---

## API Integration

The frontend communicates with the NEXORA backend via REST API:

| API Module | Endpoints | Description |
|---|---|---|
| `authAPI` | `/auth/login`, `/auth/check-auth` | Authentication and token management |
| `usersAPI` | `/users/me`, `/users/`, `/users/{id}` | User profile and management |
| `devicesAPI` | `/devices/`, `/devices/{mac}`, `/devices/create` | Device CRUD operations |
| `dashboardAPI` | `/dashboard/summary`, `/dashboard/device-metrics`, `/dashboard/topology` | Dashboard data |
| `metricsAPI` | `/metrics/cpu`, `/metrics/ram`, `/metrics/disk`, `/metrics/network`, `/metrics/latency`, `/metrics/packet-loss`, `/metrics/all` | Time-series metrics |
| `alertsAPI` | `/alerts/`, `/alerts/stats`, `/alerts/realtime`, `/alerts/latest`, `/alerts/{hostname}` | Alert management |

### WebSocket

Real-time alerts are received via WebSocket connection to `/ws/alerts`:

```typescript
// Example: Using the useAlertWebSocket hook
const { alerts, isConnected } = useAlertWebSocket();
```

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `VITE_API_BASE_URL` | ❌ | `/` | Backend API base URL (use `http://localhost:8000` for local dev) |

**Example `.env`:**
```env
VITE_API_BASE_URL=http://localhost:8000
```

---

## Running Locally

### With Docker (recommended)
```bash
docker build -t nexora-frontend .
docker run -p 3000:80 nexora-frontend
```

### Without Docker
```bash
cd frontend
npm install
npm run dev
```

The development server starts at `http://localhost:5173`.

### Production Build
```bash
cd frontend
npm run build
```

The built files will be in the `dist/` directory.

---

## Key Dependencies

| Package | Purpose |
|---|---|
| `react` + `react-dom` | UI framework |
| `react-router` | Client-side routing |
| `@tanstack/react-query` | Data fetching and caching |
| `recharts` | Chart and graph visualization |
| `tailwindcss` | Utility-first CSS framework |
| `shadcn/ui` | Pre-built UI component library |
| `lucide-react` | Icon library |
| `vite` | Build tool and dev server |

---

## Pages

| Page | Route | Description |
|---|---|---|
| Login | `/login` | User authentication |
| Dashboard | `/dashboard` | Main overview with device stats and metrics |
| Alerts | `/alerts` | Alert monitoring and management |
| Devices | `/devices` | Device inventory and management |
| Topology | `/topology` | Network topology visualization |
| Metrics | `/metrics` | Detailed metric charts and graphs |
| Settings | `/settings` | User preferences and theme |
| Admin | `/admin` | User management (admin only) |

---

## Theme Support

The frontend supports both dark and light themes:

- **Dark mode** (default): Deep blue/slate color scheme
- **Light mode**: Clean white/gray color scheme

Theme preference is persisted in `localStorage` and can be toggled from the sidebar or settings page.

---

## Development

### Code Structure

- **Components**: Reusable UI components in `src/app/components/`
- **Pages**: Page-level components in `src/app/pages/`
- **API**: Backend API client in `src/app/api/api.ts`
- **Hooks**: Custom React hooks in `src/app/hooks/`
- **Context**: React context providers in `src/app/context/`

### Adding New Pages

1. Create a new page component in `src/app/pages/`
2. Add the route in `src/app/routes.tsx`
3. Add navigation link in `src/app/components/Layout.tsx`

### Adding New API Endpoints

1. Add the API function in `src/app/api/api.ts`
2. Use the `request<T>()` helper for type-safe API calls
3. Import and use in your components or hooks
