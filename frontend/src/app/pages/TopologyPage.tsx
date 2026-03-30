import React, { useState } from 'react';
import { Network, Database, Server, Router, Cpu, RefreshCw, AlertCircle } from 'lucide-react';
import { dashboardAPI } from '../api/api';
import type { TopologyNode, TopologyData } from '../api/api';
import { useApi } from '../hooks/useApi';

const TYPE_ICONS: Record<string, React.ReactNode> = {
  core:      <Cpu className="w-4 h-4" />,
  collector: <Server className="w-4 h-4" />,
  postgres:  <Database className="w-4 h-4" />,
  influxdb:  <Database className="w-4 h-4" />,
  device:    <Server className="w-3.5 h-3.5" />,
};

const TYPE_COLORS: Record<string, { bg: string; border: string; text: string }> = {
  core:      { bg: '#0e1f3a', border: '#3b82f6', text: '#60a5fa' },
  collector: { bg: '#1a1035', border: '#8b5cf6', text: '#a78bfa' },
  postgres:  { bg: '#0e2a20', border: '#10b981', text: '#34d399' },
  influxdb:  { bg: '#1a1f0e', border: '#84cc16', text: '#a3e635' },
  device:    { bg: '#0c1225', border: '#06b6d4', text: '#22d3ee' },
  device_offline: { bg: '#1a0d0d', border: '#ef4444', text: '#f87171' },
};

function getNodeStyle(node: TopologyNode) {
  const isOffline = !(node.status === 'UP' || node.status === 'up' || node.status === 1 || node.status === '1' || node.status === 'online' || Number(node.status) === 1);
  if (node.type === 'device' && isOffline) return TYPE_COLORS.device_offline;
  return TYPE_COLORS[node.type] || TYPE_COLORS.device;
}

interface NodeCardProps {
  node: TopologyNode;
  x: number;
  y: number;
  onClick: (n: TopologyNode) => void;
  small?: boolean;
}

function NodeCard({ node, x, y, onClick, small }: NodeCardProps) {
  const style = getNodeStyle(node);
  const isOnline = node.status === 'UP' || node.status === 'up' || node.status === 1 || node.status === '1' || node.status === 'online' || Number(node.status) === 1;
  const w = small ? 110 : 130;
  const h = small ? 52 : 62;

  return (
    <g transform={`translate(${x - w / 2}, ${y - h / 2})`} onClick={() => onClick(node)} style={{ cursor: 'pointer' }}>
      {/* Glow effect */}
      <defs>
        <filter id={`glow-${node.id}`} x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
          <feMerge>
            <feMergeNode in="coloredBlur"/>
            <feMergeNode in="SourceGraphic"/>
          </feMerge>
        </filter>
      </defs>
      <rect
        width={w}
        height={h}
        rx={8}
        fill={style.bg}
        stroke={style.border}
        strokeWidth={1.5}
        opacity={0.95}
        filter={`url(#glow-${node.id})`}
      />
      <circle cx={w - 10} cy={10} r={4} fill={isOnline ? '#10b981' : '#ef4444'}>
        {isOnline && <animate attributeName="opacity" values="1;0.4;1" dur="2s" repeatCount="indefinite" />}
      </circle>
      <foreignObject x={8} y={8} width={w - 20} height={h - 16}>
        <div style={{ color: style.text, fontSize: small ? '10px' : '11px', fontFamily: 'monospace' }}>
          <div style={{ opacity: 0.8, marginBottom: 2 }}>{node.type.toUpperCase()}</div>
          <div style={{ color: 'white', fontFamily: 'sans-serif', fontSize: small ? '10px' : '11px', fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {node.name}
          </div>
          {node.ip && <div style={{ opacity: 0.6, fontSize: '9px', marginTop: 2 }}>{node.ip}</div>}
        </div>
      </foreignObject>
    </g>
  );
}

// Animated connection line with flowing light effect
function AnimatedLine({ x1, y1, x2, y2, color = '#3b82f6', reverse = false }: {
  x1: number; y1: number; x2: number; y2: number; color?: string; reverse?: boolean;
}) {
  const gradientId = `gradient-${x1}-${y1}-${x2}-${y2}`;
  const animId = `anim-${x1}-${y1}-${x2}-${y2}`;

  return (
    <g>
      <defs>
        <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor={color} stopOpacity="0.1" />
          <stop offset="50%" stopColor={color} stopOpacity="0.8" />
          <stop offset="100%" stopColor={color} stopOpacity="0.1" />
        </linearGradient>
      </defs>

      {/* Base line */}
      <line
        x1={x1} y1={y1} x2={x2} y2={y2}
        stroke={color}
        strokeWidth={2}
        opacity={0.3}
      />

      {/* Animated flowing light */}
      <line
        x1={x1} y1={y1} x2={x2} y2={y2}
        stroke="url(#gradient)"
        strokeWidth={2}
        strokeLinecap="round"
      >
        <animate
          id={animId}
          attributeName="stroke-dasharray"
          values="0,200;200,0;0,200"
          dur="2s"
          repeatCount="indefinite"
          begin={reverse ? '1s' : '0s'}
        />
      </line>

      {/* Light particle effect */}
      <circle r="3" fill={color}>
        <animateMotion
          dur="2s"
          repeatCount="indefinite"
          path={`M${x1},${y1} L${x2},${y2}`}
          begin={reverse ? '1s' : '0s'}
        />
        <animate attributeName="opacity" values="1;0;1" dur="2s" repeatCount="indefinite" begin={reverse ? '1s' : '0s'} />
      </circle>
    </g>
  );
}

// Simple static line for fallback
function Line({ x1, y1, x2, y2, color = 'rgba(255,255,255,0.1)', dashed = false }: {
  x1: number; y1: number; x2: number; y2: number; color?: string; dashed?: boolean;
}) {
  return (
    <line
      x1={x1} y1={y1} x2={x2} y2={y2}
      stroke={color} strokeWidth={1.5}
      strokeDasharray={dashed ? '5,4' : undefined}
      opacity={0.6}
    />
  );
}

export function TopologyPage() {
  const [selected, setSelected] = useState<TopologyNode | null>(null);
  const { data: topology, loading, refetch, error } = useApi(
    () => dashboardAPI.getTopology(),
    () => ({ core: { id: 'core', name: 'Core', type: 'core', status: 'offline' }, collector: { id: 'collector', name: 'Collector', type: 'collector', status: 'offline' }, databases: [], devices: [] }),
    [],
    {}
  );

  if (loading || !topology) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-500 gap-3">
        <RefreshCw className="w-5 h-5 animate-spin" /> Loading topology...
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-slate-100">Network Topology</h1>
          </div>
          <button
            onClick={refetch}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm text-slate-300 border border-white/10 hover:border-cyan-500/40 hover:text-cyan-400 transition-all"
            style={{ background: 'rgba(255,255,255,0.03)' }}
          >
            <RefreshCw className="w-4 h-4" /> Retry
          </button>
        </div>
        <div className="rounded-xl border p-8" style={{ background: 'rgba(12,18,37,0.8)', borderColor: 'rgba(255,100,100,0.3)' }}>
          <div className="flex items-center gap-3 text-red-400">
            <AlertCircle className="w-6 h-6" />
            <div>
              <h3 className="text-lg font-medium">Failed to load topology</h3>
              <p className="text-sm text-slate-400 mt-1">{error}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Layout positions
  const SVG_W = 900;
  const SVG_H = 600;

  // Core at top center
  const CORE = { x: SVG_W / 2, y: 60 };

  // Databases on left and right of Core
  const POSTGRES = { x: SVG_W / 2 - 200, y: 60 };
  const INFLUXDB = { x: SVG_W / 2 + 200, y: 60 };

  // Collector below Core
  const COLLECTOR = { x: SVG_W / 2, y: 180 };

  // Devices grid below collector
  const devices = topology.devices || [];
  const DEVICE_Y_START = 320;
  const DEVICE_COLS = Math.min(6, devices.length);
  const DEVICE_ROW_HEIGHT = 80;
  const DEVICE_COL_WIDTH = Math.min(130, (SVG_W - 80) / DEVICE_COLS);

  const devicePositions = devices.map((_, i) => {
    const col = i % DEVICE_COLS;
    const row = Math.floor(i / DEVICE_COLS);
    const totalInRow = Math.min(DEVICE_COLS, devices.length - row * DEVICE_COLS);
    const rowStart = (SVG_W - totalInRow * DEVICE_COL_WIDTH) / 2 + DEVICE_COL_WIDTH / 2;
    return {
      x: rowStart + col * DEVICE_COL_WIDTH,
      y: DEVICE_Y_START + row * DEVICE_ROW_HEIGHT,
    };
  });

  const onlineCount = devices.filter(d => d.status === 'UP' || d.status === 'up' || d.status === 1 || d.status === '1' || d.status === 'online' || Number(d.status) === 1).length;
  const offlineCount = devices.length - onlineCount;

  // Find postgres and influxdb from databases array
  const postgres = topology.databases?.find(db => db.type === 'postgres');
  const influxdb = topology.databases?.find(db => db.type === 'influxdb');

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-slate-100">Network Topology</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            {devices.length} devices · {onlineCount} online · {offlineCount} offline
          </p>
        </div>
        <button
          onClick={refetch}
          className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm text-slate-300 border border-white/10 hover:border-cyan-500/40 hover:text-cyan-400 transition-all"
          style={{ background: 'rgba(255,255,255,0.03)' }}
        >
          <RefreshCw className="w-4 h-4" /> Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-4 gap-4">
        {/* Topology SVG */}
        <div className="xl:col-span-3 rounded-xl border overflow-hidden" style={{ background: 'rgba(12,18,37,0.8)', borderColor: 'rgba(255,255,255,0.07)' }}>
          <div className="px-5 py-3 border-b flex items-center gap-2" style={{ borderColor: 'rgba(255,255,255,0.07)' }}>
            <Network className="w-4 h-4 text-cyan-400" />
            <span className="text-sm text-slate-300">Infrastructure Map</span>
            <div className="ml-auto flex items-center gap-4 text-xs text-slate-500">
              <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-emerald-400" />UP</span>
              <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-red-400" />DOWN</span>
            </div>
          </div>
          <div className="overflow-x-auto p-2">
            <svg
              viewBox={`0 0 ${SVG_W} ${Math.max(SVG_H, DEVICE_Y_START + Math.ceil(devices.length / DEVICE_COLS) * DEVICE_ROW_HEIGHT + 60)}`}
              className="w-full"
              style={{ minHeight: 450 }}
            >
              {/* Background grid */}
              <defs>
                <pattern id="topo-grid" width="40" height="40" patternUnits="userSpaceOnUse">
                  <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(255,255,255,0.03)" strokeWidth="1" />
                </pattern>

                {/* Glow filters for animated lines */}
                <filter id="blue-glow" x="-50%" y="-50%" width="200%" height="200%">
                  <feGaussianBlur stdDeviation="2" result="blur"/>
                  <feMerge>
                    <feMergeNode in="blur"/>
                    <feMergeNode in="SourceGraphic"/>
                  </feMerge>
                </filter>
                <filter id="green-glow" x="-50%" y="-50%" width="200%" height="200%">
                  <feGaussianBlur stdDeviation="2" result="blur"/>
                  <feMerge>
                    <feMergeNode in="blur"/>
                    <feMergeNode in="SourceGraphic"/>
                  </feMerge>
                </filter>
                <filter id="purple-glow" x="-50%" y="-50%" width="200%" height="200%">
                  <feGaussianBlur stdDeviation="2" result="blur"/>
                  <feMerge>
                    <feMergeNode in="blur"/>
                    <feMergeNode in="SourceGraphic"/>
                  </feMerge>
                </filter>
              </defs>
              <rect width="100%" height="100%" fill="url(#topo-grid)" />

              {/* === ANIMATED CONNECTIONS === */}

              {/* Core → PostgreSQL (left) - animated blue */}
              <g filter="url(#blue-glow)">
                <line
                  x1={CORE.x - 65} y1={CORE.y}
                  x2={POSTGRES.x + 65} y2={POSTGRES.y}
                  stroke="#3b82f6"
                  strokeWidth={2}
                  opacity={0.4}
                />
                {/* Animated light packet */}
                <circle r="4" fill="#3b82f6" filter="url(#blue-glow)">
                  <animateMotion
                    dur="1.5s"
                    repeatCount="indefinite"
                    path={`M${CORE.x - 65},${CORE.y} L${POSTGRES.x + 65},${POSTGRES.y}`}
                  />
                  <animate attributeName="opacity" values="1;0.3;1" dur="1.5s" repeatCount="indefinite" />
                </circle>
                {/* Second light packet (reverse direction) */}
                <circle r="3" fill="#10b981" filter="url(#green-glow)">
                  <animateMotion
                    dur="1.5s"
                    repeatCount="indefinite"
                    path={`M${POSTGRES.x + 65},${POSTGRES.y} L${CORE.x - 65},${CORE.y}`}
                    begin="0.75s"
                  />
                  <animate attributeName="opacity" values="1;0.3;1" dur="1.5s" repeatCount="indefinite" begin="0.75s" />
                </circle>
              </g>

              {/* Core → InfluxDB (right) - animated green */}
              <g filter="url(#green-glow)">
                <line
                  x1={CORE.x + 65} y1={CORE.y}
                  x2={INFLUXDB.x - 65} y2={INFLUXDB.y}
                  stroke="#10b981"
                  strokeWidth={2}
                  opacity={0.4}
                />
                {/* Animated light packet */}
                <circle r="4" fill="#10b981" filter="url(#green-glow)">
                  <animateMotion
                    dur="1.2s"
                    repeatCount="indefinite"
                    path={`M${CORE.x + 65},${CORE.y} L${INFLUXDB.x - 65},${INFLUXDB.y}`}
                  />
                  <animate attributeName="opacity" values="1;0.3;1" dur="1.2s" repeatCount="indefinite" />
                </circle>
                {/* Second light packet (reverse direction) */}
                <circle r="3" fill="#84cc16" filter="url(#green-glow)">
                  <animateMotion
                    dur="1.2s"
                    repeatCount="indefinite"
                    path={`M${INFLUXDB.x - 65},${INFLUXDB.y} L${CORE.x + 65},${CORE.y}`}
                    begin="0.6s"
                  />
                  <animate attributeName="opacity" values="1;0.3;1" dur="1.2s" repeatCount="indefinite" begin="0.6s" />
                </circle>
              </g>

              {/* Core → Collector - animated purple */}
              <g filter="url(#purple-glow)">
                <line
                  x1={CORE.x} y1={CORE.y + 31}
                  x2={COLLECTOR.x} y2={COLLECTOR.y - 31}
                  stroke="#8b5cf6"
                  strokeWidth={2}
                  opacity={0.4}
                />
                {/* Animated light packet */}
                <circle r="4" fill="#8b5cf6" filter="url(#purple-glow)">
                  <animateMotion
                    dur="1s"
                    repeatCount="indefinite"
                    path={`M${CORE.x},${CORE.y + 31} L${COLLECTOR.x},${COLLECTOR.y - 31}`}
                  />
                  <animate attributeName="opacity" values="1;0.3;1" dur="1s" repeatCount="indefinite" />
                </circle>
                {/* Second light packet (reverse direction) */}
                <circle r="3" fill="#a78bfa" filter="url(#purple-glow)">
                  <animateMotion
                    dur="1s"
                    repeatCount="indefinite"
                    path={`M${COLLECTOR.x},${COLLECTOR.y - 31} L${CORE.x},${CORE.y + 31}`}
                    begin="0.5s"
                  />
                  <animate attributeName="opacity" values="1;0.3;1" dur="1s" repeatCount="indefinite" begin="0.5s" />
                </circle>
              </g>

              {/* Collector → Devices */}
              {devicePositions.map((pos, i) => (
                <g key={i}>
                  <line
                    x1={COLLECTOR.x} y1={COLLECTOR.y + 31}
                    x2={pos.x} y2={pos.y - 26}
                    stroke={(devices[i]?.status === 'UP' || devices[i]?.status === 'up' || devices[i]?.status === 1 || devices[i]?.status === '1' || devices[i]?.status === 'online' || Number(devices[i]?.status) === 1) ? '#06b6d4' : '#ef4444'}
                    strokeWidth={1.5}
                    opacity={0.3}
                  />
                  {/* Animated light packet: Collector → Device */}
                  {(devices[i]?.status === 'UP' || devices[i]?.status === 'up' || devices[i]?.status === 1 || devices[i]?.status === '1' || devices[i]?.status === 'online' || Number(devices[i]?.status) === 1) && (
                    <circle r="2" fill="#06b6d4">
                      <animateMotion
                        dur="0.8s"
                        repeatCount="indefinite"
                        path={`M${COLLECTOR.x},${COLLECTOR.y + 31} L${pos.x},${pos.y - 26}`}
                        begin={`${i * 0.1}s`}
                      />
                      <animate attributeName="opacity" values="1;0.2;1" dur="0.8s" repeatCount="indefinite" begin={`${i * 0.1}s`} />
                    </circle>
                  )}
                  {/* Animated light packet: Device → Collector (reverse direction) */}
                  {(devices[i]?.status === 'UP' || devices[i]?.status === 'up' || devices[i]?.status === 1 || devices[i]?.status === '1' || devices[i]?.status === 'online' || Number(devices[i]?.status) === 1) && (
                    <circle r="2" fill="#10b981">
                      <animateMotion
                        dur="0.8s"
                        repeatCount="indefinite"
                        path={`M${pos.x},${pos.y - 26} L${COLLECTOR.x},${COLLECTOR.y + 31}`}
                        begin={`${i * 0.1 + 0.4}s`}
                      />
                      <animate attributeName="opacity" values="1;0.2;1" dur="0.8s" repeatCount="indefinite" begin={`${i * 0.1 + 0.4}s`} />
                    </circle>
                  )}
                </g>
              ))}

              {/* === RENDER NODES === */}

              {/* Core */}
              <NodeCard node={topology.core} x={CORE.x} y={CORE.y} onClick={setSelected} />

              {/* PostgreSQL (left of core) */}
              <NodeCard
                node={postgres || { id: 'postgres', name: 'PostgreSQL', type: 'postgres', status: 'online' }}
                x={POSTGRES.x}
                y={POSTGRES.y}
                onClick={setSelected}
              />

              {/* InfluxDB (right of core) */}
              <NodeCard
                node={influxdb || { id: 'influxdb', name: 'InfluxDB', type: 'influxdb', status: 'online' }}
                x={INFLUXDB.x}
                y={INFLUXDB.y}
                onClick={setSelected}
              />

              {/* Collector */}
              <NodeCard node={topology.collector} x={COLLECTOR.x} y={COLLECTOR.y} onClick={setSelected} />

              {/* Devices */}
              {devices.map((dev, i) => devicePositions[i] && (
                <NodeCard key={dev.id} node={dev} x={devicePositions[i].x} y={devicePositions[i].y} onClick={setSelected} small />
              ))}

              {/* Layer labels */}
              {/* <text x={SVG_W / 2} y={30} textAnchor="middle" fill="rgba(255,255,255,0.2)" fontSize="11" fontFamily="monospace">DATA LAYER</text>
              <text x={SVG_W / 2} y={145} textAnchor="middle" fill="rgba(255,255,255,0.15)" fontSize="10" fontFamily="monospace">COLLECTION LAYER</text>
              <text x={SVG_W / 2} y={290} textAnchor="middle" fill="rgba(255,255,255,0.15)" fontSize="10" fontFamily="monospace">DEVICE LAYER</text> */}
            </svg>
          </div>
        </div>

        {/* Info panel */}
        <div className="space-y-4">
          {/* Selected node info */}
          <div className="rounded-xl border p-4" style={{ background: 'rgba(12,18,37,0.8)', borderColor: 'rgba(255,255,255,0.07)' }}>
            <h3 className="text-slate-300 mb-3 text-sm">
              {selected ? 'Node Details' : 'Click a node to inspect'}
            </h3>
            {selected ? (
              <div className="space-y-2.5">
                {[
                  { label: 'Name', value: selected.name },
                  { label: 'Type', value: selected.type },
                  { label: 'Status', value: selected.status },
                  { label: 'IP Address', value: selected.ip || '—' },
                  ...(selected.mac ? [{ label: 'MAC', value: selected.mac }] : []),
                  ...(selected.device_type ? [{ label: 'Device Type', value: selected.device_type }] : []),
                ].map(item => (
                  <div key={item.label} className="flex justify-between items-start gap-2">
                    <span className="text-xs text-slate-500">{item.label}</span>
                    <span className={`text-xs font-mono text-right ${
                      item.label === 'Status'
                        ? (selected.status === 'UP' || selected.status === 'up' || selected.status === 1 || selected.status === '1' || selected.status === 'online' || Number(selected.status) === 1) ? 'text-emerald-400' : 'text-red-400'
                        : 'text-slate-300'
                    }`}>{item.value}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-600">Select any node in the topology diagram to view its details here.</p>
            )}
          </div>

          {/* Legend */}
          <div className="rounded-xl border p-4 space-y-2" style={{ background: 'rgba(12,18,37,0.8)', borderColor: 'rgba(255,255,255,0.07)' }}>
            <h3 className="text-slate-300 text-sm mb-3">Legend</h3>
            {[
              { label: 'Core Backend', color: '#3b82f6' },
              { label: 'PostgreSQL DB', color: '#10b981' },
              { label: 'InfluxDB', color: '#84cc16' },
              { label: 'Collector', color: '#8b5cf6' },
              { label: 'Device (UP)', color: '#06b6d4' },
              { label: 'Device (DOWN)', color: '#ef4444' },
            ].map(item => (
              <div key={item.label} className="flex items-center gap-2">
                <div className="w-3 h-3 rounded flex-shrink-0" style={{ background: item.color, opacity: 0.8 }} />
                <span className="text-xs text-slate-400">{item.label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
