export function Badge({ label, variant }) {
  return <span className={`badge badge-${variant || label}`}>{label}</span>;
}

export function Card({ title, accent, className = '', children, style }) {
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

export function StatusDot({ status }) {
  const colors = { Running: '#22c55e', Pending: '#fbbf24', CrashLoop: '#ef4444' };
  const c = colors[status] || '#64748b';
  return (
    <span style={{
      display: 'inline-block', width: 7, height: 7, borderRadius: '50%',
      background: c, boxShadow: `0 0 5px ${c}`, flexShrink: 0,
    }} />
  );
}

export function HealthBadge({ status }) {
  const icons = { HEALTHY: '●', WARNING: '●', CRITICAL: '●' };
  return (
    <span className={`health-badge health-${status}`}>
      <span style={{ fontSize: 8 }}>{icons[status] || '●'}</span>
      {status}
    </span>
  );
}

export function formatTime(iso) {
  if (!iso) return '';
  try {
    return new Date(iso).toLocaleTimeString('en', { hour12: false });
  } catch {
    return iso;
  }
}

export function truncate(str, n = 80) {
  return str && str.length > n ? str.slice(0, n) + '…' : str;
}
