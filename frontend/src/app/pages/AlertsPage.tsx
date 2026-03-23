import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { FixedSizeList as List } from 'react-window';
import { AlertCircle, Clock, RefreshCw, AlertTriangle, XCircle, Info, Filter, Settings } from 'lucide-react';
import { alertsAPI, Alert, AlertsResponse } from '../api/api';
import { useAlertWebSocket, WebSocketAlert } from '../hooks/useAlertWebSocket';

// ─── Constants ──────────────────────────────────────────────────────────────────

const MAX_ALERTS = 100;
const DEFAULT_PAGE_SIZE = 50;
const POLL_INTERVAL = 3000;
const INITIAL_FETCH_SIZE = 50;
const INCREMENTAL_FETCH_LIMIT = 20;

// ─── Helper Components ───────────────────────────────────────────────────────────

function SeverityBadge({ level }: { level?: string }) {
  const severity = (level || 'INFO').toUpperCase();
  const isCritical = severity === 'CRITICAL' || severity === 'HIGH';
  const isWarning = severity === 'WARNING' || severity === 'MID';

  let icon = <Info className="w-3 h-3" />;
  let bgClass = 'bg-blue-500/15 text-blue-400';
  let label = 'INFO';

  if (isCritical) {
    icon = <XCircle className="w-3 h-3" />;
    bgClass = 'bg-red-500/15 text-red-400';
    label = 'CRITICAL';
  } else if (isWarning) {
    icon = <AlertTriangle className="w-3 h-3" />;
    bgClass = 'bg-amber-500/15 text-amber-400';
    label = 'WARNING';
  }

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${bgClass}`}>
      {icon}
      {label}
    </span>
  );
}

function AlertCard({ alert, isNew }: { alert: Alert; isNew?: boolean }) {
  const timestamp = alert.alert_time || alert.timestamp;
  const time = timestamp ? new Date(timestamp) : null;

  return (
    <div className={`p-4 rounded-lg border transition-all hover:bg-white/5 ${isNew ? 'animate-pulse bg-amber-500/10' : ''}`} style={{
      background: 'rgba(12,18,37,0.6)',
      borderColor: isNew ? 'rgba(245,158,11,0.5)' : 'rgba(255,255,255,0.07)'
    }}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <SeverityBadge level={alert.alert_level || alert.severity} />
            <span className="text-xs text-slate-500">{alert.device_hostname || alert.device || 'Unknown Device'}</span>
            {alert.device_ip && <span className="text-xs text-slate-600">| {alert.device_ip}</span>}
            {alert.device_mac && <span className="text-xs text-slate-600">| {alert.device_mac}</span>}
          </div>
          <p className="text-slate-200 text-sm font-medium mb-1">{alert.message || alert.alert_message || 'No message'}</p>
          {time && (
            <p className="text-xs text-slate-500 flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {time.toLocaleTimeString()} • {time.toLocaleDateString()}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Main Page ─────────────────────────────────────────────────────────────────

export function AlertsPage() {
  const [lastRefresh, setLastRefresh] = useState(new Date());
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState({ critical: 0, warnings: 0, info: 0, total: 0 });
  const [filter, setFilter] = useState<'all' | 'critical' | 'warning' | 'info'>('all');
  const [newAlertIds, setNewAlertIds] = useState<Set<number>>(new Set());
  const prevAlertIds = useRef<Set<number>>(new Set());

  // OPTIMIZATION: Track the highest alert ID for incremental fetching
  // This allows us to fetch only NEW alerts instead of re-fetching the same page
  const lastAlertIdRef = useRef<number>(0);
  const isInitialLoadRef = useRef(true);

  // User configurable settings
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE);
  const [showSettings, setShowSettings] = useState(false);
  const [tempPageSize, setTempPageSize] = useState(DEFAULT_PAGE_SIZE);

  // WebSocket for real-time alerts
  const [wsAlert, setWsAlert] = useState<WebSocketAlert | null>(null);

  // Helper to map severity to frontend format
  const mapSeverityToFrontend = (severity: string | undefined): string => {
    const s = severity?.toUpperCase() || 'INFO';
    if (s === 'CRITICAL' || s === 'HIGH') return 'CRITICAL';
    if (s === 'MID' || s === 'WARNING') return 'WARNING';
    return 'INFO';
  };

  const handleNewAlert = useCallback((alert: WebSocketAlert) => {
    console.log('[AlertsPage] New alert from WebSocket:', alert);

    // Convert WebSocket alert to Alert type and add to the alerts list
    const newAlert: Alert = {
      id: alert.id,
      message: alert.message || alert.alert_message || '',
      alert_message: alert.alert_message || alert.message || '',
      alert_level: alert.alert_level || mapSeverityToFrontend(alert.severity),
      severity: alert.severity,
      device: alert.device_hostname || '',
      device_hostname: alert.device_hostname,
      device_ip: alert.device_ip,
      device_mac: alert.device_mac,
      timestamp: alert.timestamp,
      alert_time: alert.timestamp,
    };

    // Add new alert to the top of the list
    setAlerts(prev => {
      // Avoid duplicates
      const exists = prev.some(a => a.id === newAlert.id);
      if (exists) return prev;
      return [newAlert, ...prev].slice(0, pageSize); // Keep only pageSize alerts
    });

    setWsAlert(alert);

    // Mark the alert as new for highlighting
    if (alert.id) {
      setNewAlertIds(prev => {
        const updated = new Set(prev);
        updated.add(alert.id as number);
        return updated;
      });

      // Clear highlight after 3 seconds
      setTimeout(() => {
        setNewAlertIds(prev => {
          const remaining = new Set(prev);
          remaining.delete(alert.id as number);
          return remaining;
        });
      }, 3000);
    }
  }, [pageSize]);

  const { isConnected } = useAlertWebSocket({ onAlert: handleNewAlert });

  /**
   * CLEAN API USAGE - Two distinct modes:
   *
   * 1. INITIAL LOAD (isInitialLoadRef.current = true):
   *    GET /alerts?page=1&page_size=100
   *    → Returns full dataset, REPLACES state
   *
   * 2. INCREMENTAL UPDATES (after initial load):
   *    GET /alerts?after_id=LAST_ID&limit=20
   *    → Returns ONLY new alerts (id > last_id)
   *    → PREPENDS to existing state (never replaces)
   *
   * CRITICAL: Never mix pagination with after_id!
   */
  const fetchAlerts = async () => {
    try {
      let data: AlertsResponse;
      let newAlerts: Alert[];

      if (isInitialLoadRef.current) {
        // MODE 1: INITIAL LOAD - Use pagination
        // GET /alerts?page=1&page_size=100
        console.log('[Alerts] 📥 Initial bulk fetch (pagination mode)...');
        data = await alertsAPI.getAlerts(1, INITIAL_FETCH_SIZE);
        newAlerts = data.alerts || [];

        // Mark initial load as complete
        isInitialLoadRef.current = false;

        console.log(`[Alerts] 📥 Loaded ${newAlerts.length} initial alerts`);
      } else {
        // MODE 2: INCREMENTAL UPDATE - Use after_id
        // GET /alerts?after_id=LAST_ID&limit=20
        const lastId = lastAlertIdRef.current;

        if (lastId > 0) {
          console.log(`[Alerts] 🔄 Incremental fetch (after_id mode): after_id=${lastId}`);
          data = await alertsAPI.getAlertsAfter(lastId, INCREMENTAL_FETCH_LIMIT);
          newAlerts = data.alerts || [];
          console.log(`[Alerts] 🔄 Found ${newAlerts.length} new alerts`);
        } else {
          // Edge case: No lastId yet, fallback to initial load
          console.log('[Alerts] ⚠️ No lastId, falling back to initial load...');
          data = await alertsAPI.getAlerts(1, INITIAL_FETCH_SIZE);
          newAlerts = data.alerts || [];
        }
      }

      // Update the highest alert ID we've seen
      if (newAlerts.length > 0) {
        const maxId = Math.max(...newAlerts.map(a => a.id || 0));
        if (maxId > lastAlertIdRef.current) {
          lastAlertIdRef.current = maxId;
          console.log(`[Alerts] ✅ Updated lastAlertId to: ${maxId}`);
        }
      }

      // Track which alerts are new (for highlighting)
      const currentIds = new Set(newAlerts.map(a => a.id).filter(Boolean));
      const newIds = new Set<number>();

      currentIds.forEach(id => {
        if (id && !prevAlertIds.current.has(id)) {
          newIds.add(id);
        }
      });

      prevAlertIds.current = currentIds;

      // Keep existing new alert IDs and add new ones
      setNewAlertIds(prev => {
        const merged = new Set(prev);
        newIds.forEach(id => merged.add(id));
        return merged;
      });

      // Clear new alert highlight after 3 seconds (for each new alert)
      setTimeout(() => {
        setNewAlertIds(prev => {
          const remaining = new Set(prev);
          newIds.forEach(id => remaining.delete(id));
          return remaining;
        });
      }, 3000);

      // STATE UPDATE - Clean separation:
      // - Initial load: REPLACE state
      // - Incremental: PREPEND only if new alerts exist
      if (isInitialLoadRef.current) {
        // Just completed initial load OR initial load state check
        // Actually, since we set isInitialLoadRef.current = false above,
        // this branch won't execute. But kept for clarity.
        setAlerts(newAlerts);
      } else if (newAlerts.length > 0) {
        // INCREMENTAL: Prepend new alerts, filter duplicates
        setAlerts(prev => {
          const existingIds = new Set(prev.map(a => a.id));
          const uniqueNewAlerts = newAlerts.filter(a => !existingIds.has(a.id));
          return [...uniqueNewAlerts, ...prev].slice(0, pageSize);
        });
      }
      // ELSE: No new alerts → DO NOTHING (keep existing alerts)

      setError(null);
      setLastRefresh(new Date());
    } catch (e) {
      console.error('[Alerts] Error fetching alerts:', e);
      setError(e instanceof Error ? e.message : 'Failed to load alerts');
    }
  };

  const fetchStats = async () => {
    try {
      const data = await alertsAPI.getStats();
      setStats(data);
    } catch (e) {
      console.error('[Alerts] Error fetching stats:', e);
    }
  };

  const loadData = async () => {
    setLoading(true);
    await Promise.all([fetchAlerts(), fetchStats()]);
    setLoading(false);
  };

  const handleSaveSettings = () => {
    const size = Math.min(MAX_ALERTS, Math.max(1, tempPageSize));
    setPageSize(size);
    setShowSettings(false);
  };

  // Reset initial load flag when pageSize changes to refetch bulk data
  useEffect(() => {
    isInitialLoadRef.current = true;
    lastAlertIdRef.current = 0;
    loadData();
  }, [pageSize]);

  // Real-time polling with INCREMENTAL strategy
  // Uses after_id to fetch only new alerts - not the same page 1!
  useEffect(() => {
    const interval = setInterval(() => {
      fetchAlerts();
    }, POLL_INTERVAL);

    return () => clearInterval(interval);
  }, [pageSize]);

  const handleRefresh = () => {
    // Full reload - reset tracking variables and fetch fresh data
    isInitialLoadRef.current = true;
    lastAlertIdRef.current = 0;
    loadData();
  };

  // Filter alerts
  const filteredAlerts = alerts.filter(alert => {
    const level = (alert.alert_level || alert.severity || 'INFO').toUpperCase();
    if (filter === 'all') return true;
    if (filter === 'critical') return level === 'CRITICAL' || level === 'HIGH';
    if (filter === 'warning') return level === 'WARNING' || level === 'MID';
    if (filter === 'info') return level === 'INFO' || level === 'LOW';
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-slate-100">Real-Time Alerts</h1>
          <p className="text-sm text-slate-500 flex items-center gap-1.5 mt-0.5">
            {isConnected ? (
              <>
                <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" /> WebSocket • Last updated: {lastRefresh.toLocaleTimeString()}
              </>
            ) : (
              <>
                <Clock className="w-3.5 h-3.5" /> Polling every {POLL_INTERVAL / 1000}s • Last updated: {lastRefresh.toLocaleTimeString()}
              </>
            )}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              setTempPageSize(pageSize);
              setShowSettings(true);
            }}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm text-slate-300 border border-white/10 hover:border-cyan-500/40 hover:text-cyan-400 transition-all"
            style={{ background: 'rgba(255,255,255,0.03)' }}
          >
            <Settings className="w-4 h-4" />
            Settings
          </button>
          <button
            onClick={handleRefresh}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm text-slate-300 border border-white/10 hover:border-cyan-500/40 hover:text-cyan-400 transition-all"
            style={{ background: 'rgba(255,255,255,0.03)' }}
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Settings Modal */}
      {showSettings && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setShowSettings(false)} />
          <div className="relative rounded-xl border p-6 w-full max-w-md" style={{ background: '#0c1225', borderColor: 'rgba(255,255,255,0.1)' }}>
            <h3 className="text-lg font-semibold text-white mb-4">Alert Settings</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-slate-400 mb-2">
                  Number of alerts to fetch (1 - {MAX_ALERTS})
                </label>
                <input
                  type="number"
                  min={1}
                  max={MAX_ALERTS}
                  value={tempPageSize}
                  onChange={(e) => setTempPageSize(parseInt(e.target.value) || DEFAULT_PAGE_SIZE)}
                  className="w-full px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-slate-200 focus:border-cyan-500 focus:outline-none"
                />
                <p className="text-xs text-slate-500 mt-1">
                  Current: {pageSize} alerts • Polls every {POLL_INTERVAL / 1000} second(s) with incremental updates
                </p>
              </div>
            </div>
            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => setShowSettings(false)}
                className="px-4 py-2 rounded-lg text-sm text-slate-400 hover:text-white transition-all"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveSettings}
                className="px-4 py-2 rounded-lg text-sm bg-cyan-500 text-white hover:bg-cyan-600 transition-all"
              >
                Save
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="rounded-xl border p-4" style={{ background: 'rgba(12,18,37,0.8)', borderColor: 'rgba(255,255,255,0.07)' }}>
          <div className="flex items-center gap-2 mb-2">
            <XCircle className="w-4 h-4 text-red-400" />
            <span className="text-xs text-slate-500">Critical</span>
          </div>
          <div className="text-2xl font-semibold text-red-400">{stats.critical}</div>
        </div>
        <div className="rounded-xl border p-4" style={{ background: 'rgba(12,18,37,0.8)', borderColor: 'rgba(255,255,255,0.07)' }}>
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            <span className="text-xs text-slate-500">Warnings</span>
          </div>
          <div className="text-2xl font-semibold text-amber-400">{stats.warnings}</div>
        </div>
        <div className="rounded-xl border p-4" style={{ background: 'rgba(12,18,37,0.8)', borderColor: 'rgba(255,255,255,0.07)' }}>
          <div className="flex items-center gap-2 mb-2">
            <Info className="w-4 h-4 text-blue-400" />
            <span className="text-xs text-slate-500">Info</span>
          </div>
          <div className="text-2xl font-semibold text-blue-400">{stats.info}</div>
        </div>
        <div className="rounded-xl border p-4" style={{ background: 'rgba(12,18,37,0.8)', borderColor: 'rgba(255,255,255,0.07)' }}>
          <div className="flex items-center gap-2 mb-2">
            <AlertCircle className="w-4 h-4 text-slate-400" />
            <span className="text-xs text-slate-500">Total</span>
          </div>
          <div className="text-2xl font-semibold text-slate-300">{stats.total}</div>
        </div>
      </div>

      {/* Filter */}
      <div className="flex items-center gap-2">
        <Filter className="w-4 h-4 text-slate-500" />
        <span className="text-sm text-slate-500">Filter:</span>
        {(['all', 'critical', 'warning', 'info'] as const).map(f => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-3 py-1 rounded-full text-xs font-medium transition-all ${
              filter === f
                ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/40'
                : 'bg-white/5 text-slate-400 border border-white/10 hover:border-white/20'
            }`}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      {/* Error State */}
      {error && (
        <div className="rounded-xl border p-4" style={{ background: 'rgba(12,18,37,0.8)', borderColor: 'rgba(255,100,100,0.3)' }}>
          <div className="flex items-center gap-3 text-red-400">
            <AlertCircle className="w-5 h-5" />
            <span>{error}</span>
          </div>
        </div>
      )}

      {/* Alerts List */}
      <div className="rounded-xl border overflow-hidden" style={{ background: 'rgba(12,18,37,0.8)', borderColor: 'rgba(255,255,255,0.07)' }}>
        <div className="flex items-center justify-between px-5 py-4 border-b" style={{ borderColor: 'rgba(255,255,255,0.07)' }}>
          <h3 className="text-slate-300">Active Alerts (Latest {pageSize})</h3>
          <span className="text-xs text-slate-500">{filteredAlerts.length} alerts</span>
        </div>

        {loading && alerts.length === 0 ? (
          <div className="p-8 text-center text-slate-500">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2" />
            Loading alerts...
          </div>
        ) : filteredAlerts.length === 0 ? (
          <div className="p-8 text-center text-slate-500">
            <AlertCircle className="w-8 h-8 mx-auto mb-2 text-slate-600" />
            <p>No alerts to display</p>
            <p className="text-xs text-slate-600 mt-1">Alerts will appear here when triggered</p>
          </div>
        ) : (
          <List
            height={Math.min(filteredAlerts.length * 100, 800)}
            itemCount={filteredAlerts.length}
            itemSize={100}
            width="100%"
            className="py-2"
          >
            {({ index, style }: { index: number; style: React.CSSProperties }) => {
              const alert = filteredAlerts[index];
              const isNew = alert.id && newAlertIds.has(alert.id);
              return (
                <div style={style} className="px-1">
                  <AlertCard alert={alert} isNew={isNew} />
                </div>
              );
            }}
          </List>
        )}
      </div>
    </div>
  );
}
