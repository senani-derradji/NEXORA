import { apiLogger } from '../utils/logger';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/';

apiLogger.info('API initialized with base URL:', API_BASE_URL);


export interface User {
  id: number;
  email: string;
  username?: string;
  role: 'admin' | 'viewer';
}

export interface Device {
  id: number;
  hostname: string;
  device_type: string;
  ip_address: string;
  mac_address: string;
  status: number | string;
  status_text?: string;
  status_value?: number;
  last_seen?: string;
  interval?: number;
  cpu_usage?: number;
  ram_usage?: number;
  disk_usage?: number;
  latency?: number;
}

export interface DashboardSummary {
  total_devices: number;
  online_devices: number;
  offline_devices: number;
  active_alerts: number;
  critical_alerts: number;
  warning_alerts: number;
  system_health: number;
  avg_cpu: number;
  avg_ram: number;
  avg_disk: number;
  avg_latency: number;
}

export interface MetricDataPoint {
  timestamp: string;
  value: number;
  value_in?: number;
  value_out?: number;
}

export interface DeviceMetric {
  device: string;
  data: MetricDataPoint[];
}

export interface MetricResponse {
  metric: string;
  duration: string;
  devices: DeviceMetric[];
}

export interface TopologyNode {
  id: string;
  name: string;
  type: string;
  status: string;
  ip?: string;
  mac?: string;
  device_type?: string;
}

export interface TopologyData {
  core: TopologyNode;
  collector: TopologyNode;
  databases: TopologyNode[];
  devices: TopologyNode[];
}


function getToken(): string | null {
  return localStorage.getItem('nexora_token');
}

function getHeaders(contentType = 'application/json'): HeadersInit {
  const token = getToken();
  const headers: Record<string, string> = {};
  if (contentType !== 'form') {
    headers['Content-Type'] = contentType;
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const baseUrl = API_BASE_URL.replace(/\/$/, '');
  const url = `${baseUrl}${endpoint}`;
  console.log('[API] Request:', options.method || 'GET', url);

  const token = getToken();
  console.log('[API] Token:', token ? 'present' : 'missing');

  const config: RequestInit = {
    headers: getHeaders(),
    ...options,
  };

  const response = await fetch(url, config);
  console.log('[API] Response:', response.status, response.statusText);

  if (response.status === 401) {
    console.warn('[API] 401 Unauthorized');
    localStorage.removeItem('nexora_token');
    localStorage.removeItem('nexora_user');
    window.location.href = '/login';
    throw new Error('Unauthorized');
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    console.error('[API] Error:', error);
    throw new Error((error as any).detail || `HTTP error ${response.status}`);
  }

  const data = await response.json();
  console.log('[API] Data:', data);
  return data;
}

// ─── Auth ─────────────────────────────────────────────────────────────────────

export const authAPI = {
  async login(username: string, password: string): Promise<{ access_token: string; token_type: string; user: User }> {
    console.log('[authAPI.login] Starting login for:', username);
    console.log('[authAPI.login] API_BASE_URL:', API_BASE_URL);

    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const url = `${API_BASE_URL.replace(/\/$/, '')}/auth/login`;
    console.log('[authAPI.login] Making request to:', url);

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData,
      });

      console.log('[authAPI.login] Response status:', response.status);

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        console.error('[authAPI.login] Error response:', error);
        throw new Error((error as any).detail || 'Login failed');
      }

      const data = await response.json();
      console.log('[authAPI.login] Success, data:', data);
      localStorage.setItem('nexora_token', data.access_token);
      localStorage.setItem('nexora_user', JSON.stringify(data.user));
      return data;
    } catch (err) {
      console.error('[authAPI.login] Exception:', err);
      throw err;
    }
  },

  async checkAuth(): Promise<{ authenticated: boolean; username: string; role: string }> {
    return request('/auth/check-auth');
  },

  logout() {
    localStorage.removeItem('nexora_token');
    localStorage.removeItem('nexora_user');
  },
};

// ─── Users ────────────────────────────────────────────────────────────────────

export const usersAPI = {
  async getMe(): Promise<User> {
    return request('/users/me');
  },
  async updateMe(data: Partial<User>): Promise<User> {
    return request('/users/me', { method: 'PUT', body: JSON.stringify(data) });
  },
  async changePassword(oldPassword: string, newPassword: string): Promise<void> {
    return request('/users/change-password', {
      method: 'POST',
      body: JSON.stringify({ old_password: oldPassword, new_password: newPassword }),
    });
  },
  async getAll(): Promise<User[]> {
    return request('/users/');
  },
  async delete(userId: number): Promise<void> {
    return request(`/users/${userId}`, { method: 'DELETE' });
  },
  async register(email: string, password: string): Promise<User> {
    return request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  },
};

// ─── Devices ──────────────────────────────────────────────────────────────────

export const devicesAPI = {
  async getAll(): Promise<Device[]> {
    return request('/devices/');
  },
  async getByMac(mac: string): Promise<Device> {
    return request(`/devices/${mac}`);
  },
  async create(data: Partial<Device>): Promise<Device> {
    return request('/devices/create', { method: 'POST', body: JSON.stringify(data) });
  },
  async update(mac: string, data: Partial<Device>): Promise<Device> {
    return request(`/devices/${mac}`, { method: 'PUT', body: JSON.stringify(data) });
  },
  async delete(mac: string): Promise<void> {
    return request(`/devices/${mac}`, { method: 'DELETE' });
  },
  async getCount(): Promise<{ count: number }> {
    return request('/devices/count');
  },
};

// ─── Dashboard ────────────────────────────────────────────────────────────────

export const dashboardAPI = {
  async getSummary(): Promise<DashboardSummary> {
    return request('/dashboard/summary');
  },
  async getDeviceMetrics(): Promise<{ devices: Device[] }> {
    return request('/dashboard/device-metrics');
  },
  async getTopology(): Promise<TopologyData> {
    return request('/dashboard/topology');
  },
};

// ─── Metrics ──────────────────────────────────────────────────────────────────

export const metricsAPI = {
  async getCpu(duration = '1h', device?: string): Promise<MetricResponse> {
    const q = device ? `&device=${device}` : '';
    return request(`/metrics/cpu?duration=${duration}${q}`);
  },
  async getRam(duration = '1h', device?: string): Promise<MetricResponse> {
    const q = device ? `&device=${device}` : '';
    return request(`/metrics/ram?duration=${duration}${q}`);
  },
  async getDisk(duration = '1h', device?: string): Promise<MetricResponse> {
    const q = device ? `&device=${device}` : '';
    return request(`/metrics/disk?duration=${duration}${q}`);
  },
  async getNetwork(duration = '1h', device?: string): Promise<MetricResponse> {
    const q = device ? `&device=${device}` : '';
    return request(`/metrics/network?duration=${duration}${q}`);
  },
  async getLatency(duration = '1h', device?: string): Promise<MetricResponse> {
    const q = device ? `&device=${device}` : '';
    return request(`/metrics/latency?duration=${duration}${q}`);
  },
  async getPacketLoss(duration = '1h', device?: string): Promise<MetricResponse> {
    const q = device ? `&device=${device}` : '';
    return request(`/metrics/packet-loss?duration=${duration}${q}`);
  },
  async getAll(duration = '1h', device?: string): Promise<any> {
    const q = device ? `&device=${device}` : '';
    return request(`/metrics/all?duration=${duration}${q}`);
  },
};

// ─── Alerts ───────────────────────────────────────────────────────────────────

export interface Alert {
  id?: number;
  device?: string;
  device_hostname?: string;
  device_ip?: string;
  device_mac?: string;
  metric?: string;
  value?: number;
  threshold?: number;
  severity?: string;
  alert_level?: string;
  timestamp?: string;
  alert_time?: string;
  message?: string;
  alert_message?: string;
  acknowledged?: boolean;
}

export interface AlertsResponse {
  alerts: Alert[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface AlertsStats {
  critical: number;
  warnings: number;
  info: number;
  total: number;
}

export interface RealtimeAlertsResponse {
  alerts: Alert[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

export const alertsAPI = {
  async getAll(): Promise<Alert[]> {
    const res = await request<AlertsResponse>('/alerts/');
    return res.alerts || [];
  },
  async getStats(): Promise<AlertsStats> {
    try {
      const res = await request<AlertsStats>('/alerts/stats');
      // Handle case where response is wrapped in object or is not valid
      if (res && typeof res === 'object' && !Array.isArray(res)) {
        return {
          critical: Number(res.critical) || 0,
          warnings: Number(res.warnings) || Number(res.warning) || 0,  // Handle both plural and singular
          info: Number(res.info) || 0,
          total: Number(res.total) || 0
        };
      }
      return res || { critical: 0, warnings: 0, info: 0, total: 0 };
    } catch (e) {
      console.error('Error fetching alert stats:', e);
      return { critical: 0, warnings: 0, info: 0, total: 0 };
    }
  },
  async getByDevice(deviceHostname: string): Promise<Alert[]> {
    const res = await request<{ alerts: Alert[] }>(`/alerts/${deviceHostname}`);
    return res.alerts || [];
  },
  async delete(deviceHostname: string): Promise<void> {
    return request(`/alerts/${deviceHostname}`, { method: 'DELETE' });
  },
  async getRealtime(page = 1): Promise<RealtimeAlertsResponse> {
    return request(`/alerts/realtime?page=${page}`);
  },
  async getLatest(limit = 50): Promise<{ alerts: Alert[]; total: number; limit: number }> {
    return request(`/alerts/latest?limit=${limit}`);
  },
  async getAlerts(page = 1, pageSize = 50): Promise<AlertsResponse> {
    return request(`/alerts/?page=${page}&page_size=${pageSize}`);
  },
  // Get alerts after a specific ID (for efficient updates)
  async getAlertsAfter(afterId: number, limit = 100): Promise<AlertsResponse> {
    return request(`/alerts/?after_id=${afterId}&limit=${limit}`);
  },
  // Get alerts after a specific timestamp (for efficient updates)
  async getAlertsAfterTimestamp(afterTimestamp: string, limit = 100): Promise<AlertsResponse> {
    return request(`/alerts/?after_timestamp=${encodeURIComponent(afterTimestamp)}&limit=${limit}`);
  },
};
