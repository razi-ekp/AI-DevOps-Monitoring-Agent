import { Card, Badge, formatTime, truncate } from '../ui';

const SEV_ICON = { CRITICAL: '🔴', HIGH: '🟠', MEDIUM: '🟡', LOW: '🔵' };

export default function AlertsPanel({ alerts }) {
  return (
    <Card title="Alerts & Notifications" accent="orange">
      <div style={{ display: 'flex', gap: 8, marginBottom: 10 }}>
        <ChannelBadge icon="💬" label="Slack" active />
        <ChannelBadge icon="✉️" label="Email" active />
      </div>
      <div className="alert-list">
        {alerts.length === 0 && (
          <div style={{ color: 'var(--text-muted)', fontSize: 12, textAlign: 'center', padding: '20px 0' }}>
            No alerts fired yet
          </div>
        )}
        {alerts.map(a => (
          <div key={a.id} className={`alert-item sev-${a.severity}`}>
            <span className="alert-icon">{SEV_ICON[a.severity] || '⚪'}</span>
            <div className="alert-body">
              <div className="alert-msg">{truncate(a.message, 80)}</div>
              <div className="alert-meta">
                <span>{formatTime(a.timestamp)}</span>
                <Badge label={a.severity} />
                <span style={{ color: 'var(--accent-cyan)' }}>{a.service}</span>
                {a.channels?.map(c => (
                  <span key={c} className="channel-tag">→ {c}</span>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

function ChannelBadge({ icon, label, active }) {
  return (
    <div style={{
      display: 'inline-flex', alignItems: 'center', gap: 5, padding: '3px 10px',
      borderRadius: 4, fontFamily: 'var(--font-mono)', fontSize: 10,
      background: active ? 'rgba(34,197,94,0.1)' : 'rgba(255,255,255,0.04)',
      border: `1px solid ${active ? 'rgba(34,197,94,0.3)' : 'var(--border)'}`,
      color: active ? '#22c55e' : 'var(--text-muted)',
    }}>
      {icon} {label} {active ? '● LIVE' : '○ OFF'}
    </div>
  );
}
