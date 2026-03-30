import React from 'react';
import type { LucideIcon } from 'lucide-react';

interface StatCardProps {
  label: string;
  value: string | number;
  icon: LucideIcon;
  color: 'cyan' | 'emerald' | 'red' | 'amber' | 'blue' | 'violet';
  sub?: string;
  trend?: { value: number; positive: boolean };
}

const colorMap = {
  cyan:    { bg: 'rgba(6,182,212,0.1)',   border: 'rgba(6,182,212,0.2)',   icon: 'text-cyan-400',    text: 'text-cyan-400' },
  emerald: { bg: 'rgba(16,185,129,0.1)',  border: 'rgba(16,185,129,0.2)',  icon: 'text-emerald-400', text: 'text-emerald-400' },
  red:     { bg: 'rgba(239,68,68,0.1)',   border: 'rgba(239,68,68,0.2)',   icon: 'text-red-400',     text: 'text-red-400' },
  amber:   { bg: 'rgba(245,158,11,0.1)',  border: 'rgba(245,158,11,0.2)',  icon: 'text-amber-400',   text: 'text-amber-400' },
  blue:    { bg: 'rgba(59,130,246,0.1)',  border: 'rgba(59,130,246,0.2)',  icon: 'text-blue-400',    text: 'text-blue-400' },
  violet:  { bg: 'rgba(139,92,246,0.1)',  border: 'rgba(139,92,246,0.2)',  icon: 'text-violet-400',  text: 'text-violet-400' },
};

export function StatCard({ label, value, icon: Icon, color, sub, trend }: StatCardProps) {
  const c = colorMap[color];
  return (
    <div className="rounded-xl border p-4 flex flex-col gap-3"
      style={{ background: 'rgba(12,18,37,0.8)', borderColor: c.border }}>
      <div className="flex items-center justify-between">
        <span className="text-sm text-slate-400">{label}</span>
        <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: c.bg }}>
          <Icon className={`w-4 h-4 ${c.icon}`} />
        </div>
      </div>
      <div>
        <div className={`text-2xl font-semibold ${c.text}`}>{value}</div>
        {sub && <div className="text-xs text-slate-500 mt-0.5">{sub}</div>}
      </div>
      {trend && (
        <div className={`text-xs ${trend.positive ? 'text-emerald-400' : 'text-red-400'}`}>
          {trend.positive ? '↑' : '↓'} {Math.abs(trend.value)}% from last hour
        </div>
      )}
    </div>
  );
}
