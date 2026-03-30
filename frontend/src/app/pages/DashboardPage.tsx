import React, { useState } from 'react';
import { Link } from 'react-router';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts';
import {
  Server, CheckCircle, RefreshCw, Activity, Clock, Wifi, AlertCircle
} from 'lucide-react';
import { dashboardAPI, metricsAPI } from '../api/api';
import { useApi } from '../hooks/useApi';
import { StatCard } from '../components/StatCard';

function StatusBadge({ status }: { status: string }) {
  const up = status === 'UP' || status === 'up' || status === 1 || status === '1' || Number(status) === 1;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium ${up ? 'bg-emerald-500/15 text-emerald-400' : 'bg-red-500/15 text-red-400'}`}>
      {up ? (
        <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" /></svg>
      ) : (
        <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" /></svg>
      )}
      {up ? 'UP' : 'DOWN'}
    </span>
  );
}

function MetricBar({ value, color }: { value: number; color: string }) {
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 rounded-full bg-white/5">
        <div className="h-full rounded-full transition-all" style={{ width: `${Math.min(100, value)}%`, background: color }} />
      </div>
      <span className="text-xs text-slate-400 w-9 text-right">{value.toFixed(0)}%</span>
    </div>
  );
}

function HealthGauge({ value }: { value: number }) {
  const angle = (value / 100) * 180 - 90;
  const color = value >= 80 ? '#10b981' : value >= 60 ? '#f59e0b' : '#ef4444';
  return (
    <div className="flex flex-col items-center justify-center gap-2">
      <div className="relative w-32 h-20 overflow-hidden">
        <svg viewBox="0 0 120 70" className="w-full h-full">
          {/* Background arc */}
          <path d="M 10 60 A 50 50 0 0 1 110 60" fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="10" strokeLinecap="round" />
          {/* Value arc */}
          <path d="M 10 60 A 50 50 0 0 1 110 60" fill="none" stroke={color} strokeWidth="10" strokeLinecap="round"
            strokeDasharray="157"
            strokeDashoffset={157 - (value / 100) * 157}
            style={{ transition: 'stroke-dashoffset 1s ease, stroke 0.5s ease' }}
          />
          {/* Needle */}
          <line
            x1="60" y1="60"
            x2={60 + 40 * Math.cos(((angle - 90) * Math.PI) / 180)}
            y2={60 + 40 * Math.sin(((angle - 90) * Math.PI) / 180)}
            stroke={color} strokeWidth="2" strokeLinecap="round"
            style={{ transition: 'all 1s ease' }}
          />
          <circle cx="60" cy="60" r="4" fill={color} />
        </svg>
      </div>
      <div className="text-center">
        <div className="text-2xl font-semibold" style={{ color }}>{value}%</div>
        <div className="text-xs text-slate-500">System Health</div>
      </div>
    </div>
  );
}

export function DashboardPage() {
  const [lastRefresh, setLastRefresh] = useState(new Date());

  const { data: summary, loading: sumLoading, refetch: refetchSummary, error: sumError } = useApi(
    () => {
      console.log('[Dashboard] Fetching summary from API');
      return dashboardAPI.getSummary();
    },
    () => ({ total_devices: 0, online_devices: 0, offline_devices: 0, active_alerts: 0, critical_alerts: 0, warning_alerts: 0, system_health: 0, avg_cpu: 0, avg_ram: 0, avg_disk: 0, avg_latency: 0 }),
    [],
    { autoRefresh: 30000 }
  );

  console.log('[Dashboard] Rendering, summary:', summary);

  const { data: devMetrics, loading: devLoading, refetch: refetchDevices, error: devError } = useApi(
    () => {
      console.log('[Dashboard] Fetching device metrics from API');
      return dashboardAPI.getDeviceMetrics();
    },
    () => ({ devices: [] }),
    [],
    { autoRefresh: 30000 }
  );

  const { data: cpuMetric } = useApi(
    () => metricsAPI.getCpu('1h'),
    () => ({ metric: 'cpu', duration: '1h', devices: [] }),
    []
  );

  const { data: ramMetric } = useApi(
    () => metricsAPI.getRam('1h'),
    () => ({ metric: 'ram', duration: '1h', devices: [] }),
    []
  );

  const handleRefresh = () => {
    setLastRefresh(new Date());
    refetchSummary();
    refetchDevices();
  };

  // Show error state if API fails
  if (sumError || devError) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-slate-100">Dashboard</h1>
            <p className="text-sm text-slate-500 flex items-center gap-1.5 mt-0.5">
              <Clock className="w-3.5 h-3.5" /> Last updated: {lastRefresh.toLocaleTimeString()}
            </p>
          </div>
          <button
            onClick={handleRefresh}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm text-slate-300 border border-white/10 hover:border-cyan-500/40 hover:text-cyan-400 transition-all"
            style={{ background: 'rgba(255,255,255,0.03)' }}
          >
            <RefreshCw className={`w-4 h-4 ${sumLoading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>

        <div className="rounded-xl border p-8" style={{ background: 'rgba(12,18,37,0.8)', borderColor: 'rgba(255,100,100,0.3)' }}>
          <div className="flex items-center gap-3 text-red-400">
            <AlertCircle className="w-6 h-6" />
            <div>
              <h3 className="text-lg font-medium">Failed to load dashboard data</h3>
              <p className="text-sm text-slate-400 mt-1">{sumError || devError}</p>
              <p className="text-xs text-slate-500 mt-2">Please ensure the backend API is running and accessible.</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Build chart data from cpu/ram metrics
  const chartData = React.useMemo(() => {
    if (!cpuMetric || !ramMetric) return [];
    const cpuDevices = Array.isArray(cpuMetric?.devices) ? cpuMetric.devices : [];
    const ramDevices = Array.isArray(ramMetric?.devices) ? ramMetric.devices : [];
    if (!cpuDevices.length) return [];

    const cpuAgg = cpuDevices[0].data;
    return cpuAgg.map((point, i) => {
      const avgCpu = cpuDevices.reduce((s, d) => s + (d.data[i]?.value || 0), 0) / cpuDevices.length;
      const avgRam = ramDevices.reduce((s, d) => s + (d.data[i]?.value || 0), 0) / (ramDevices.length || 1);
      const label = new Date(point.timestamp);
      return {
        time: label.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        CPU: +avgCpu.toFixed(1),
        RAM: +avgRam.toFixed(1),
      };
    });
  }, [cpuMetric, ramMetric]);

  const devices = devMetrics?.devices || [];

  const tooltipStyle = {
    contentStyle: { background: '#0c1225', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', color: '#e2e8f0' },
    labelStyle: { color: '#94a3b8' },
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-slate-100">Dashboard</h1>
          <p className="text-sm text-slate-500 flex items-center gap-1.5 mt-0.5">
            <Clock className="w-3.5 h-3.5" /> Last updated: {lastRefresh.toLocaleTimeString()}
          </p>
        </div>
        <button
          onClick={handleRefresh}
          className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm text-slate-300 border border-white/10 hover:border-cyan-500/40 hover:text-cyan-400 transition-all"
          style={{ background: 'rgba(255,255,255,0.03)' }}
        >
          <RefreshCw className={`w-4 h-4 ${sumLoading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
        <StatCard label="Total Devices" value={summary?.total_devices ?? '—'} icon={Server} color="cyan" sub="Monitored endpoints" />
        <StatCard label="UP" value={summary?.online_devices ?? '—'} icon={CheckCircle} color="emerald" sub={`${summary ? Math.round((summary.online_devices / summary.total_devices) * 100) : 0}% uptime`} />
        <StatCard label="DOWN" value={summary?.offline_devices ?? '—'} icon={Wifi} color="red" sub="Need attention" />
      </div>

      {/* Second row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Health gauge */}
        <div className="rounded-xl border p-5" style={{ background: 'rgba(12,18,37,0.8)', borderColor: 'rgba(255,255,255,0.07)' }}>
          <h3 className="text-slate-300 mb-4">System Health</h3>
          <HealthGauge value={summary?.system_health ?? 0} />
          <div className="mt-4 grid grid-cols-2 gap-3">
            <div className="text-center">
              <div className="text-sm text-cyan-400">{summary?.avg_cpu?.toFixed(1) ?? 0}%</div>
              <div className="text-xs text-slate-500">Avg CPU</div>
            </div>
            <div className="text-center">
              <div className="text-sm text-blue-400">{summary?.avg_ram?.toFixed(1) ?? 0}%</div>
              <div className="text-xs text-slate-500">Avg RAM</div>
            </div>
            <div className="text-center">
              <div className="text-sm text-violet-400">{summary?.avg_disk?.toFixed(1) ?? 0}%</div>
              <div className="text-xs text-slate-500">Avg Disk</div>
            </div>
            <div className="text-center">
              <div className="text-sm text-amber-400">{summary?.avg_latency?.toFixed(1) ?? 0}ms</div>
              <div className="text-xs text-slate-500">Avg Latency</div>
            </div>
          </div>
        </div>

        {/* Chart */}
        <div className="lg:col-span-2 rounded-xl border p-5" style={{ background: 'rgba(12,18,37,0.8)', borderColor: 'rgba(255,255,255,0.07)' }}>
          <h3 className="text-slate-300 mb-4">CPU & RAM — Last 1h</h3>
          <ResponsiveContainer width="100%" height={180}>
            <AreaChart data={chartData} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="cpuGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#06b6d4" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="ramGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="time" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} domain={[0, 100]} />
              <Tooltip {...tooltipStyle} />
              <Legend wrapperStyle={{ color: '#94a3b8', fontSize: '12px' }} />
              <Area type="monotone" dataKey="CPU" stroke="#06b6d4" fill="url(#cpuGrad)" strokeWidth={2} dot={false} />
              <Area type="monotone" dataKey="RAM" stroke="#3b82f6" fill="url(#ramGrad)" strokeWidth={2} dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Device Table */}
      <div className="rounded-xl border overflow-hidden" style={{ background: 'rgba(12,18,37,0.8)', borderColor: 'rgba(255,255,255,0.07)' }}>
        <div className="flex items-center justify-between px-5 py-4 border-b" style={{ borderColor: 'rgba(255,255,255,0.07)' }}>
          <h3 className="text-slate-300">Device Status</h3>
          <span className="text-xs text-slate-500">{devices.length} devices</span>
        </div>
        {devLoading ? (
          <div className="p-8 text-center text-slate-500">Loading devices...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                  {['Hostname', 'Type', 'IP Address', 'Status', 'CPU', 'RAM', 'Latency'].map(h => (
                    <th key={h} className="text-left px-5 py-3 text-xs text-slate-500 font-medium uppercase tracking-wider">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y" style={{ borderColor: 'rgba(255,255,255,0.04)' }}>
                {devices.slice(0, 8).map(d => (
                  <tr key={d.id} className="hover:bg-white/2 transition-colors">
                    <td className="px-5 py-3 text-slate-200 font-medium">{d.hostname}</td>
                    <td className="px-5 py-3">
                      <span className="px-2 py-0.5 rounded text-xs bg-white/5 text-slate-400 capitalize">{d.device_type?.replace('_', ' ')}</span>
                    </td>
                    <td className="px-5 py-3 text-slate-400 font-mono text-xs">{d.ip_address}</td>
                    <td className="px-5 py-3"><StatusBadge status={String(d.status_text || d.status)} /></td>
                    <td className="px-5 py-3 min-w-24">
                      <MetricBar value={d.cpu_usage ?? 0} color="#06b6d4" />
                    </td>
                    <td className="px-5 py-3 min-w-24">
                      <MetricBar value={d.ram_usage ?? 0} color="#3b82f6" />
                    </td>
                    <td className="px-5 py-3 text-slate-400 text-xs">{d.latency != null ? `${d.latency.toFixed(1)}ms` : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}