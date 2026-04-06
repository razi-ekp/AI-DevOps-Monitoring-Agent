import { Card, Badge, formatTime, truncate } from '../ui';

const SEV_ICON = { CRITICAL: '[!]', HIGH: '[^]', MEDIUM: '[-]', LOW: '[i]', INFO: '[i]' };

export default function AlertsPanel({ alerts }) {
  const criticalCount = alerts.filter((a) => a.severity === 'CRITICAL').length;
  const highCount = alerts.filter((a) => a.severity === 'HIGH').length;
  const lastCritical = alerts.find((a) => a.severity === 'CRITICAL');

  return (
    <Card title="Alerts & Notifications" accent="orange">
      <div style={{ display: 'flex', gap: 8, marginBottom: 10, flexWrap: 'wrap', alignItems: 'center' }}>
        <ChannelBadge label="Slack" active />
        <ChannelBadge label="Email" active />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: 8, marginBottom: 10 }}>
        <MiniStat label="Critical Alerts" value={String(criticalCount)} tone="#ef4444" />
        <MiniStat label="High Alerts" value={String(highCount)} tone="#f97316" />
        <MiniStat
          label="Last Critical"
          value={lastCritical ? formatTime(lastCritical.timestamp) : 'None'}
          tone={lastCritical ? '#ef4444' : 'var(--text-muted)'}
        />
      </div>

      <div style={{ marginBottom: 10, fontSize: 11, color: 'var(--text-secondary)' }}>
        Auto email notifications are sent for <span style={{ color: '#ef4444' }}>CRITICAL</span> incidents.
      </div>

      <div className="alert-list">
        {alerts.length === 0 && (
          <div style={{ color: 'var(--text-muted)', fontSize: 12, textAlign: 'center', padding: '20px 0' }}>
            No alerts fired yet
          </div>
        )}
        {alerts.map((a) => (
          <div key={a.id} className={`alert-item sev-${a.severity}`}>
            <span className="alert-icon">{SEV_ICON[a.severity] || '[ ]'}</span>
            <div className="alert-body">
              <div className="alert-msg">{truncate(a.message, 80)}</div>
              <div className="alert-meta">
                <span>{formatTime(a.timestamp)}</span>
                <Badge label={a.severity} />
                <span style={{ color: 'var(--accent-cyan)' }}>{a.service}</span>
                {a.channels?.map((c) => (
                  <span key={c} className="channel-tag">-&gt; {c}</span>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

function ChannelBadge({ label, active }) {
  return (
    <div
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 5,
        padding: '3px 10px',
        borderRadius: 4,
        fontFamily: 'var(--font-mono)',
        fontSize: 10,
        background: active ? 'rgba(34,197,94,0.1)' : 'rgba(255,255,255,0.04)',
        border: `1px solid ${active ? 'rgba(34,197,94,0.3)' : 'var(--border)'}`,
        color: active ? '#22c55e' : 'var(--text-muted)',
      }}
    >
      {label} {active ? 'LIVE' : 'OFF'}
    </div>
  );
}

function MiniStat({ label, value, tone }) {
  return (
    <div
      style={{
        background: 'rgba(255,255,255,0.025)',
        border: '1px solid var(--border)',
        borderRadius: 6,
        padding: '8px 10px',
      }}
    >
      <div
        style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 10,
          color: 'var(--text-muted)',
          textTransform: 'uppercase',
          letterSpacing: '0.08em',
        }}
      >
        {label}
      </div>
      <div style={{ marginTop: 4, fontSize: 13, color: tone }}>{value}</div>
    </div>
  );
}
