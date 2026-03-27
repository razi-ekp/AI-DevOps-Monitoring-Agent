import { useState } from 'react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { Card } from '../ui';

const TABS = [
  { key: 'cpu',     label: 'CPU',     color: '#22d3ee', unit: '%' },
  { key: 'memory',  label: 'Memory',  color: '#a78bfa', unit: '%' },
  { key: 'network', label: 'Network', color: '#22c55e', unit: 'KB/s' },
  { key: 'disk',    label: 'Disk',    color: '#fbbf24', unit: '%' },
];

const CustomTooltip = ({ active, payload, label, unit }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: '#0d1117', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, padding: '8px 12px', fontFamily: 'var(--font-mono)', fontSize: 11 }}>
      <div style={{ color: '#64748b', marginBottom: 3 }}>{label}</div>
      {payload.map(p => (
        <div key={p.dataKey} style={{ color: p.color }}>
          {typeof p.value === 'number' ? p.value.toFixed(1) : p.value}{unit}
        </div>
      ))}
    </div>
  );
};

export default function MetricsChart({ metrics }) {
  const [active, setActive] = useState('cpu');
  const tab = TABS.find(t => t.key === active);

  const data = metrics.map(m => ({
    t: m.t || new Date(m.timestamp).toLocaleTimeString('en', { hour12: false }),
    [active]: m[active],
  }));

  return (
    <Card title="Metrics — Real-time" accent="cyan" className="span-2">
      <div className="metric-tabs">
        {TABS.map(t => (
          <button
            key={t.key}
            className={`metric-tab ${active === t.key ? 'active' : ''}`}
            onClick={() => setActive(t.key)}
          >
            {t.label}
          </button>
        ))}
      </div>
      <ResponsiveContainer width="100%" height={180}>
        <AreaChart data={data} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
          <defs>
            <linearGradient id={`grad-${active}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor={tab.color} stopOpacity={0.25} />
              <stop offset="95%" stopColor={tab.color} stopOpacity={0.01} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
          <XAxis dataKey="t" tick={{ fontSize: 9, fontFamily: 'IBM Plex Mono', fill: '#475569' }} tickLine={false} axisLine={false} interval={9} />
          <YAxis tick={{ fontSize: 9, fontFamily: 'IBM Plex Mono', fill: '#475569' }} tickLine={false} axisLine={false} domain={[0, active === 'network' ? 'auto' : 100]} />
          <Tooltip content={<CustomTooltip unit={tab.unit} />} />
          <Area
            type="monotone"
            dataKey={active}
            stroke={tab.color}
            strokeWidth={2}
            fill={`url(#grad-${active})`}
            dot={false}
            isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </Card>
  );
}
