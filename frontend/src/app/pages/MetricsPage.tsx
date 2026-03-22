import React, { useState } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
  AreaChart, Area
} from 'recharts';
import { BarChart2, Cpu, MemoryStick, HardDrive, Wifi, Activity, Radio, RefreshCw, AlertCircle } from 'lucide-react';
import { metricsAPI } from '../api/api';
import type { MetricResponse } from '../api/api';
import { metricsAPI } from '../api/api';
import { useApi } from '../hooks/useApi';

const DURATIONS = ['5m', '15m', '30m', '1h', '6h', '24h', '7d'];

const METRIC_COLORS = ['#06b6d4', '#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b'];

const METRIC_TABS = [
  { key: 'cpu', label: 'CPU', icon: Cpu, unit: '%', color: '#06b6d4', description: 'CPU utilization per device' },
  { key: 'ram', label: 'RAM', icon: MemoryStick, unit: '%', color: '#3b82f6', description: 'Memory usage per device' },
  { key: 'disk', label: 'Disk', icon: HardDrive, unit: '%', color: '#8b5cf6', description: 'Disk utilization per device' },
  { key: 'latency', label: 'Latency', icon: Activity, unit: 'ms', color: '#f59e0b', description: 'Network round-trip time' },
  { key: 'network', label: 'Network I/O', icon: Wifi, unit: 'Mbps', color: '#10b981', description: 'Network throughput' },
  { key: 'packet-loss', label: 'Packet Loss', icon: Radio, unit: '%', color: '#ef4444', description: 'Packet loss percentage' },
];

// Helper to convert bytes to Mbps (module-level for reuse)
const bytesToMbps = (bytes: number): number => {
  return (bytes * 8) / 1_000_000;
};

function MetricChart({ data, unit, color, metricType }: { data: MetricResponse; unit: string; color: string; metricType?: string }) {
  const devices = data.devices.slice(0, 5);

  // Merge all device data by timestamp index
  const merged = React.useMemo(() => {
    if (!devices.length) return [];

    // Special handling for network metrics
    if (metricType === 'network') {
      const allTimestamps = new Set<string>();
      devices.forEach(dev => {
        dev.data.forEach(point => allTimestamps.add(point.timestamp));
      });
      const sortedTimestamps = Array.from(allTimestamps).sort();

      return sortedTimestamps.map((ts, idx) => {
        const row: Record<string, number> = {
          time: new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        };
        devices.forEach(dev => {
          const inPoint = dev.data.find(d => d.timestamp === ts);
          const outPoint = dev.data.find(d => d.timestamp === ts);
          // Convert bytes to Mbps
          row[`${dev.device}_in`] = inPoint ? +bytesToMbps(inPoint.value_in ?? 0).toFixed(2) : 0;
          row[`${dev.device}_out`] = outPoint ? +bytesToMbps(outPoint.value_out ?? 0).toFixed(2) : 0;
        });
        return row;
      });
    }

    // Standard handling for other metrics
    const base = devices[0]?.data || [];
    return base.map((point, i) => {
      const row: Record<string, string | number> = {
        time: new Date(point.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      devices.forEach(dev => {
        const val = dev.data[i]?.value;
        row[dev.device] = val !== undefined && val !== null ? +val.toFixed(2) : 0;
      });
      return row;
    });
  }, [data, metricType]);

  const tooltipStyle = {
    contentStyle: { background: '#0c1225', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', color: '#e2e8f0', fontSize: '12px' },
    labelStyle: { color: '#94a3b8', marginBottom: 4 },
    formatter: (val: number) => [`${val}${unit}`, ''],
  };

  return (
    <ResponsiveContainer width="100%" height={260}>
      <AreaChart data={merged} margin={{ top: 5, right: 10, left: -15, bottom: 0 }}>
        <defs>
          {devices.map((dev, i) => (
            <linearGradient key={dev.device} id={`grad-${i}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={METRIC_COLORS[i]} stopOpacity={0.25} />
              <stop offset="95%" stopColor={METRIC_COLORS[i]} stopOpacity={0} />
            </linearGradient>
          ))}
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
        <XAxis dataKey="time" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} interval="preserveStartEnd" />
        <YAxis tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} unit={unit} />
        <Tooltip {...tooltipStyle} />
        <Legend wrapperStyle={{ color: '#94a3b8', fontSize: '11px', paddingTop: 8 }} />
        {metricType === 'network' ? (
          // Network: show IN and OUT lines for each device
          devices.map((dev, i) => (
            <React.Fragment key={dev.device}>
              <Area
                type="monotone"
                dataKey={`${dev.device}_in`}
                name={`${dev.device} IN`}
                stroke={METRIC_COLORS[i]}
                fill={`url(#grad-${i})`}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4 }}
              />
              <Area
                type="monotone"
                dataKey={`${dev.device}_out`}
                name={`${dev.device} OUT`}
                stroke={METRIC_COLORS[i]}
                strokeDasharray="5 5"
                fill="transparent"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4 }}
              />
            </React.Fragment>
          ))
        ) : (
          devices.map((dev, i) => (
            <Area
              key={dev.device}
              type="monotone"
              dataKey={dev.device}
              stroke={METRIC_COLORS[i]}
              fill={`url(#grad-${i})`}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
            />
          ))
        )}
      </AreaChart>
    </ResponsiveContainer>
  );
}

function StatSummary({ data, unit, metricType }: { data: MetricResponse; unit: string; metricType?: string }) {
  // For network metrics, show combined in/out summary
  if (metricType === 'network') {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
        {data.devices.slice(0, 5).map((dev, i) => {
          const inVals = dev.data.map(d => d.value_in ?? 0);
          const outVals = dev.data.map(d => d.value_out ?? 0);
          const avgIn = inVals.length ? bytesToMbps(inVals.reduce((a, b) => a + b, 0) / inVals.length) : 0;
          const avgOut = outVals.length ? bytesToMbps(outVals.reduce((a, b) => a + b, 0) / outVals.length) : 0;
          return (
            <div key={dev.device} className="rounded-lg p-3 border" style={{ background: 'rgba(255,255,255,0.02)', borderColor: 'rgba(255,255,255,0.06)' }}>
              <div className="text-xs text-slate-500 truncate mb-2" title={dev.device}>{dev.device}</div>
              <div className="text-lg font-medium" style={{ color: METRIC_COLORS[i] }}>↓{avgIn.toFixed(1)}{unit} / ↑{avgOut.toFixed(1)}{unit}</div>
              <div className="text-xs text-slate-600 mt-1">
                Total: {(avgIn + avgOut).toFixed(1)}{unit}
              </div>
            </div>
          );
        })}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
      {data.devices.slice(0, 5).map((dev, i) => {
        const vals = dev.data.map(d => d.value ?? 0);
        const avg = vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : 0;
        const max = vals.length ? Math.max(...vals) : 0;
        const min = vals.length ? Math.min(...vals) : 0;
        return (
          <div key={dev.device} className="rounded-lg p-3 border" style={{ background: 'rgba(255,255,255,0.02)', borderColor: 'rgba(255,255,255,0.06)' }}>
            <div className="text-xs text-slate-500 truncate mb-2" title={dev.device}>{dev.device}</div>
            <div className="text-lg font-medium" style={{ color: METRIC_COLORS[i] }}>{avg.toFixed(1)}{unit}</div>
            <div className="text-xs text-slate-600 mt-1">
              ↑{max.toFixed(1)} / ↓{min.toFixed(1)}
            </div>
          </div>
        );
      })}
    </div>
  );
}

export function MetricsPage() {
  const [activeTab, setActiveTab] = useState('cpu');
  const [duration, setDuration] = useState('1h');

  const tab = METRIC_TABS.find(t => t.key === activeTab)!;

  const fetchers: Record<string, () => Promise<MetricResponse>> = {
    cpu: () => metricsAPI.getCpu(duration),
    ram: () => metricsAPI.getRam(duration),
    disk: () => metricsAPI.getDisk(duration),
    latency: () => metricsAPI.getLatency(duration),
    network: () => metricsAPI.getNetwork(duration),
    'packet-loss': () => metricsAPI.getPacketLoss(duration),
  };

  const { data, loading, refetch, error } = useApi(
    fetchers[activeTab],
    () => ({ metric: activeTab, duration, devices: [] }),
    [activeTab, duration],
    {}
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-slate-100">Metrics</h1>
          <p className="text-sm text-slate-500 mt-0.5">Time-series performance data across all monitored devices</p>
        </div>
        <button
          onClick={refetch}
          className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm text-slate-300 border border-white/10 hover:border-cyan-500/40 hover:text-cyan-400 transition-all"
          style={{ background: 'rgba(255,255,255,0.03)' }}
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} /> Refresh
        </button>
      </div>

      {/* Metric Tabs */}
      <div className="flex flex-wrap gap-2">
        {METRIC_TABS.map(tab => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm transition-all border ${
                activeTab === tab.key
                  ? 'border-cyan-500/40 text-cyan-400'
                  : 'border-white/8 text-slate-400 hover:border-white/15 hover:text-slate-200'
              }`}
              style={{ background: activeTab === tab.key ? 'rgba(6,182,212,0.08)' : 'rgba(255,255,255,0.02)' }}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Duration Selector */}
      <div className="flex items-center gap-3">
        <span className="text-sm text-slate-400">Time range:</span>
        <div className="flex gap-1 p-1 rounded-lg" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)' }}>
          {DURATIONS.map(d => (
            <button
              key={d}
              onClick={() => setDuration(d)}
              className={`px-3 py-1 rounded-md text-sm transition-all ${
                duration === d ? 'text-white' : 'text-slate-500 hover:text-slate-300'
              }`}
              style={duration === d ? { background: 'rgba(6,182,212,0.2)', color: '#22d3ee' } : {}}
            >
              {d}
            </button>
          ))}
        </div>
      </div>

      {/* Main Chart */}
      <div className="rounded-xl border p-5" style={{ background: 'rgba(12,18,37,0.8)', borderColor: 'rgba(255,255,255,0.07)' }}>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            {React.createElement(tab.icon, { className: 'w-4 h-4', style: { color: tab.color } })}
            <h3 className="text-slate-300">{tab.label} — {duration}</h3>
            <span className="text-xs text-slate-500">({tab.description})</span>
          </div>
        </div>
        {error ? (
          <div className="h-64 flex items-center justify-center text-red-400 gap-3">
            <AlertCircle className="w-5 h-5" />
            <div>
              <p>Failed to load {tab.label} metrics</p>
              <p className="text-xs text-slate-500 mt-1">{error}</p>
            </div>
          </div>
        ) : loading ? (
          <div className="h-64 flex items-center justify-center text-slate-500">
            <RefreshCw className="w-5 h-5 animate-spin mr-2" /> Loading metrics...
          </div>
        ) : data ? (
          <MetricChart data={data} unit={tab.unit} color={tab.color} metricType={activeTab} />
        ) : null}
      </div>

      {/* Per-device summary */}
      {data && !loading && (
        <div className="rounded-xl border p-5" style={{ background: 'rgba(12,18,37,0.8)', borderColor: 'rgba(255,255,255,0.07)' }}>
          <h3 className="text-slate-300 mb-4">Per-Device Summary — {tab.label}</h3>
          <StatSummary data={data} unit={tab.unit} metricType={activeTab} />
        </div>
      )}
    </div>
  );
}
