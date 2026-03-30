import React, { useState } from 'react';
import { Server, Plus, Search, Trash2, Eye, X, Loader2, Edit, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import { devicesAPI } from '../api/api';
import type { Device } from '../api/api';
import { useApi } from '../hooks/useApi';
import { useAuth } from '../context/AuthContext';

const DEVICE_TYPES = ['router', 'switch', 'server', 'firewall', 'access_point', 'other'];

function DeviceModal({ device, onClose }: { device: Device; onClose: () => void }) {
  // Use consistent status check - status can be 1/0 (from devices API) or 'UP'/'DOWN' (from metrics)
  const isUp = device.status === 'UP' || device.status === 'up' || device.status === 1 || device.status === '1' || Number(device.status) === 1;
  const lastSeen = device.last_seen ? new Date(device.last_seen).toLocaleString() : '—';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="w-full max-w-lg rounded-2xl border shadow-2xl"
        style={{ background: '#0c1225', borderColor: 'rgba(255,255,255,0.1)' }}>
        <div className="flex items-center justify-between px-6 py-4 border-b" style={{ borderColor: 'rgba(255,255,255,0.07)' }}>
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-cyan-500/10 flex items-center justify-center">
              <Server className="w-5 h-5 text-cyan-400" />
            </div>
            <div>
              <h2 className="text-white">{device.hostname}</h2>
              <p className="text-xs text-slate-500 capitalize">{device.device_type?.replace('_', ' ')}</p>
            </div>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            {[
              { label: 'IP Address', value: device.ip_address, mono: true },
              { label: 'MAC Address', value: device.mac_address, mono: true },
              { label: 'Status', value: isUp ? 'UP' : 'DOWN', color: isUp ? 'text-emerald-400' : 'text-red-400' },
              { label: 'Last Seen', value: lastSeen },
              { label: 'CPU Usage', value: device.cpu_usage != null ? `${device.cpu_usage.toFixed(1)}%` : '—' },
              { label: 'RAM Usage', value: device.ram_usage != null ? `${device.ram_usage.toFixed(1)}%` : '—' },
              { label: 'Disk Usage', value: device.disk_usage != null ? `${device.disk_usage.toFixed(1)}%` : '—' },
              { label: 'Latency', value: device.latency != null ? `${device.latency.toFixed(1)}ms` : '—' },
            ].map(item => (
              <div key={item.label} className="rounded-lg p-3" style={{ background: 'rgba(255,255,255,0.03)' }}>
                <div className="text-xs text-slate-500 mb-1">{item.label}</div>
                <div className={`text-sm ${(item as any).color || 'text-slate-200'} ${(item as any).mono ? 'font-mono' : ''}`}>
                  {item.value || '—'}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function AddDeviceModal({ onClose, onAdd }: { onClose: () => void; onAdd: (d: Partial<Device>) => void }) {
  const [form, setForm] = useState({ hostname: '', device_type: 'router', ip_address: '', mac_address: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.hostname || !form.ip_address || !form.mac_address) { setError('All fields are required.'); return; }
    setLoading(true);
    try { await onAdd(form); onClose(); } catch (err) { setError(err instanceof Error ? err.message : 'Failed to add device'); }
    finally { setLoading(false); }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="w-full max-w-md rounded-2xl border shadow-2xl" style={{ background: '#0c1225', borderColor: 'rgba(255,255,255,0.1)' }}>
        <div className="flex items-center justify-between px-6 py-4 border-b" style={{ borderColor: 'rgba(255,255,255,0.07)' }}>
          <h2 className="text-white">Add New Device</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-white"><X className="w-5 h-5" /></button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {[
            { label: 'Hostname', key: 'hostname', placeholder: 'router-01' },
            { label: 'IP Address', key: 'ip_address', placeholder: '192.168.1.1' },
            { label: 'MAC Address', key: 'mac_address', placeholder: '00:11:22:33:44:55' },
          ].map(f => (
            <div key={f.key}>
              <label className="block text-sm text-slate-300 mb-1.5">{f.label}</label>
              <input
                value={(form as any)[f.key]}
                onChange={e => setForm(p => ({ ...p, [f.key]: e.target.value }))}
                placeholder={f.placeholder}
                className="w-full px-4 py-2.5 rounded-lg text-sm text-white placeholder-slate-500 border outline-none focus:border-cyan-500"
                style={{ background: 'rgba(255,255,255,0.05)', borderColor: 'rgba(255,255,255,0.1)' }}
              />
            </div>
          ))}
          <div>
            <label className="block text-sm text-slate-300 mb-1.5">Device Type</label>
            <select
              value={form.device_type}
              onChange={e => setForm(p => ({ ...p, device_type: e.target.value }))}
              className="w-full px-4 py-2.5 rounded-lg text-sm text-white border outline-none focus:border-cyan-500"
              style={{ background: '#0c1225', borderColor: 'rgba(255,255,255,0.1)' }}
            >
              {DEVICE_TYPES.map(t => <option key={t} value={t} className="capitalize">{t.replace('_', ' ')}</option>)}
            </select>
          </div>
          {error && <p className="text-sm text-red-400">{error}</p>}
          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose}
              className="flex-1 py-2.5 rounded-lg text-sm text-slate-400 border border-white/10 hover:border-white/20 transition-all">
              Cancel
            </button>
            <button type="submit" disabled={loading}
              className="flex-1 py-2.5 rounded-lg text-sm text-white transition-all flex items-center justify-center gap-2 disabled:opacity-60"
              style={{ background: 'linear-gradient(135deg, #06b6d4, #3b82f6)' }}>
              {loading ? <><Loader2 className="w-4 h-4 animate-spin" />Adding...</> : 'Add Device'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export function DevicesPage() {
  const { user } = useAuth();
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);

  const { data: devices, loading, refetch, error } = useApi(
    () => devicesAPI.getAll(),
    () => [],
    [],
    {}
  );

  const filtered = (devices || []).filter(d => {
    const matchSearch = !search || d.hostname.toLowerCase().includes(search.toLowerCase()) || d.ip_address.includes(search);
    const matchType = typeFilter === 'all' || d.device_type === typeFilter;
    // Use consistent status check - status can be 1/0 or 'UP'/'DOWN'
    const isUp = d.status === 'UP' || d.status === 'up' || d.status === 1 || d.status === '1' || Number(d.status) === 1;
    const matchStatus = statusFilter === 'all' || (statusFilter === 'online' ? isUp : !isUp);
    return matchSearch && matchType && matchStatus;
  });

  const handleAdd = async (data: Partial<Device>) => {
    await devicesAPI.create(data);
    refetch();
  };

  const handleDelete = async (mac: string) => {
    if (!confirm('Are you sure you want to delete this device?')) return;
    console.log('[DevicesPage] Attempting to delete device:', mac);
    try {
      await devicesAPI.delete(mac);
      console.log('[DevicesPage] Delete successful, refetching...');
      refetch();
    } catch (error: any) {
      console.error('[DevicesPage] Delete failed:', error);
      alert(`Failed to delete device: ${error.message || 'Unknown error'}`);
    }
  };

  const isAdmin = user?.role === 'admin';
  const types = Array.from(new Set((devices || []).map(d => d.device_type)));

  return (
    <div className="space-y-6">
      {selectedDevice && <DeviceModal device={selectedDevice} onClose={() => setSelectedDevice(null)} />}
      {showAddModal && <AddDeviceModal onClose={() => setShowAddModal(false)} onAdd={handleAdd} />}

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-slate-100">Devices</h1>
          <p className="text-sm text-slate-500 mt-0.5">{(devices || []).length} monitored endpoints</p>
        </div>
        {isAdmin && (
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm text-white transition-all"
            style={{ background: 'linear-gradient(135deg, #06b6d4, #3b82f6)' }}
          >
            <Plus className="w-4 h-4" /> Add Device
          </button>
        )}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-48">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search hostname or IP..."
            className="w-full pl-9 pr-4 py-2 rounded-lg text-sm text-white placeholder-slate-500 border outline-none focus:border-cyan-500"
            style={{ background: 'rgba(12,18,37,0.8)', borderColor: 'rgba(255,255,255,0.1)' }}
          />
        </div>
        <select
          value={typeFilter}
          onChange={e => setTypeFilter(e.target.value)}
          className="px-3 py-2 rounded-lg text-sm text-white border outline-none"
          style={{ background: 'rgba(12,18,37,0.8)', borderColor: 'rgba(255,255,255,0.1)' }}
        >
          <option value="all">All Types</option>
          {types.map(t => <option key={t} value={t} className="capitalize">{t.replace('_', ' ')}</option>)}
        </select>
        <select
          value={statusFilter}
          onChange={e => setStatusFilter(e.target.value)}
          className="px-3 py-2 rounded-lg text-sm text-white border outline-none"
          style={{ background: 'rgba(12,18,37,0.8)', borderColor: 'rgba(255,255,255,0.1)' }}
        >
          <option value="all">All Status</option>
          <option value="online">UP</option>
          <option value="offline">DOWN</option>
        </select>
      </div>

      {/* Table */}
      <div className="rounded-xl border overflow-hidden" style={{ background: 'rgba(12,18,37,0.8)', borderColor: 'rgba(255,255,255,0.07)' }}>
        {error ? (
          <div className="flex items-center justify-center py-16 text-red-400 gap-3">
            <AlertCircle className="w-5 h-5" />
            <div>
              <p>Failed to load devices</p>
              <p className="text-xs text-slate-500 mt-1">{error}</p>
            </div>
          </div>
        ) : loading ? (
          <div className="flex items-center justify-center py-16 text-slate-500 gap-3">
            <Loader2 className="w-5 h-5 animate-spin" /> Loading devices...
          </div>
        ) : filtered.length === 0 ? (
          <div className="py-16 text-center text-slate-500">No devices found.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
                  {['Hostname', 'Type', 'IP Address', 'MAC Address', 'Status', 'Last Seen', 'Actions'].map(h => (
                    <th key={h} className="text-left px-5 py-3 text-xs text-slate-500 font-medium uppercase tracking-wider">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.map(d => {
                  const isUp = d.status === 'UP' || d.status === 'up' || d.status === 1 || d.status === '1' || Number(d.status) === 1;
                  return (
                    <tr key={d.id} className="border-b hover:bg-white/2 transition-colors" style={{ borderColor: 'rgba(255,255,255,0.04)' }}>
                      <td className="px-5 py-3 text-slate-200 font-medium">{d.hostname}</td>
                      <td className="px-5 py-3">
                        <span className="px-2 py-0.5 rounded bg-white/5 text-slate-400 text-xs capitalize">{d.device_type?.replace('_', ' ')}</span>
                      </td>
                      <td className="px-5 py-3 text-slate-400 font-mono text-xs">{d.ip_address}</td>
                      <td className="px-5 py-3 text-slate-500 font-mono text-xs">{d.mac_address}</td>
                      <td className="px-5 py-3">
                        <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs ${isUp ? 'bg-emerald-500/15 text-emerald-400' : 'bg-red-500/15 text-red-400'}`}>
                          {isUp ? <CheckCircle className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
                          {isUp ? 'UP' : 'DOWN'}
                        </span>
                      </td>
                      <td className="px-5 py-3 text-slate-500 text-xs">
                        {d.last_seen ? new Date(d.last_seen).toLocaleString() : '—'}
                      </td>
                      <td className="px-5 py-3">
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => setSelectedDevice(d)}
                            className="p-1.5 rounded-lg text-slate-400 hover:text-cyan-400 hover:bg-cyan-500/10 transition-all"
                            title="View details"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                          {isAdmin && (
                            <button
                              onClick={() => handleDelete(d.mac_address)}
                              className="p-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition-all"
                              title="Delete device"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
