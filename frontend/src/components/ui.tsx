import { CSSProperties, PropsWithChildren } from 'react';

interface BadgeProps {
  label: string;
  variant?: string;
}

interface CardProps {
  title?: string;
  accent?: string;
  className?: string;
  style?: CSSProperties;
}

interface StatusDotProps {
  status?: string;
}

interface HealthBadgeProps {
  status: string;
}

export function Badge({ label, variant }: BadgeProps) {
  return <span className={`badge badge-${variant || label}`}>{label}</span>;
}

export function Card({ title, accent, className = '', children, style }: PropsWithChildren<CardProps>) {
  return (
    <div className={`card ${accent ? `card-accent-${accent}` : ''} ${className}`} style={style}>
      {title && <div className="card-title">{title}</div>}
      {children}
    </div>
  );
}

export function Spinner() {
  return <span className="spinner" />;
}

export function StatusDot({ status }: StatusDotProps) {
  const colors: Record<string, string> = { Running: '#22c55e', Pending: '#fbbf24', CrashLoop: '#ef4444' };
  const c = colors[status || ''] || '#64748b';
  return (
    <span
      style={{
        display: 'inline-block',
        width: 7,
        height: 7,
        borderRadius: '50%',
        background: c,
        boxShadow: `0 0 5px ${c}`,
        flexShrink: 0,
      }}
    />
  );
}

export function HealthBadge({ status }: HealthBadgeProps) {
  const icons: Record<string, string> = { HEALTHY: '●', WARNING: '●', CRITICAL: '●' };
  return (
    <span className={`health-badge health-${status}`}>
      <span style={{ fontSize: 8 }}>{icons[status] || '●'}</span>
      {status}
    </span>
  );
}

export function formatTime(iso?: string) {
  if (!iso) return '';
  try {
    return new Date(iso).toLocaleTimeString('en', { hour12: false });
  } catch {
    return iso;
  }
}

export function truncate(str?: string, n = 80) {
  if (!str) return '';
  return str.length > n ? str.slice(0, n) + '…' : str;
}
