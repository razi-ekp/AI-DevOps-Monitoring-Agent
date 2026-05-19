import { HealthBadge } from '../ui';
import { OverviewPanelProps } from '../../types';

export default function OverviewPanel({ summary }: OverviewPanelProps) {
  const { system_health, services_monitored, active_incidents, cpu = 0, memory = 0, network = 0, auto_heal = true } = summary;

  const stats = [
    {
      label: 'System Health',
      value: <HealthBadge status={system_health} />,
      sub: `Auto-heal: ${auto_heal ? 'ON' : 'OFF'}`,
      accent: system_health === 'HEALTHY' ? '#22c55e' : system_health === 'WARNING' ? '#fbbf24' : '#ef4444',
    },
    {
      label: 'Active Incidents',
      value: active_incidents,
      sub: `${services_monitored} services monitored`,
      accent: active_incidents > 0 ? '#ef4444' : '#22c55e',
    },
    {
      label: 'CPU Usage',
      value: `${cpu.toFixed(1)}%`,
      sub: <MiniBar value={cpu} />,
      accent: cpu > 85 ? '#ef4444' : cpu > 65 ? '#fbbf24' : '#22d3ee',
    },
    {
      label: 'Memory Usage',
      value: `${memory.toFixed(1)}%`,
      sub: <MiniBar value={memory} color={memory > 85 ? '#ef4444' : memory > 65 ? '#fbbf24' : '#22c55e'} />,
      accent: memory > 85 ? '#ef4444' : memory > 65 ? '#fbbf24' : '#22c55e',
    },
  ];

  return (
    <div className="stat-row">
      {stats.map((s, i) => (
        <div key={i} className="stat-card" style={{ borderTop: `2px solid ${s.accent}` }}>
          <div className="stat-label">{s.label}</div>
          <div className="stat-value" style={{ fontSize: typeof s.value === 'object' ? 14 : 28, display: 'flex', alignItems: 'center' }}>
            {s.value}
          </div>
          <div className="stat-sub">{s.sub}</div>
        </div>
      ))}
    </div>
  );
}

interface MiniBarProps {
  value?: number;
  color?: string;
}

function MiniBar({ value = 0, color }: MiniBarProps) {
  const c = color || (value > 85 ? '#ef4444' : value > 65 ? '#fbbf24' : '#22d3ee');
  return (
    <div style={{ background: 'rgba(255,255,255,0.06)', borderRadius: 2, height: 4, marginTop: 4, overflow: 'hidden' }}>
      <div style={{ width: `${Math.min(100, value)}%`, height: '100%', background: c, borderRadius: 2, transition: 'width 0.5s ease' }} />
    </div>
  );
}
