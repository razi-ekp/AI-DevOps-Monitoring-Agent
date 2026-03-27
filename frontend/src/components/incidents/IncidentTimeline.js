import { Card, Badge, formatTime, truncate } from '../ui';

export default function IncidentTimeline({ incidents }) {
  return (
    <Card title="Incident Timeline" accent="red">
      <div className="incident-list">
        {incidents.length === 0 && (
          <div style={{ color: 'var(--text-muted)', fontSize: 12, textAlign: 'center', padding: '20px 0' }}>
            ✓ No incidents detected
          </div>
        )}
        {incidents.map(inc => (
          <div key={inc.id} className={`incident-item sev-${inc.severity}`}>
            <div className="incident-header">
              <span className="incident-svc">{inc.service}</span>
              <Badge label={inc.severity} />
              <Badge label={inc.status} variant={inc.status} />
            </div>
            <div className="incident-desc">{truncate(inc.description, 90)}</div>
            {inc.root_cause && (
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>
                <span style={{ color: 'var(--accent-yellow)', fontFamily: 'var(--font-mono)' }}>cause: </span>
                {truncate(inc.root_cause, 80)}
              </div>
            )}
            {inc.action_taken && (
              <div style={{ fontSize: 11, color: '#22c55e', marginBottom: 4 }}>
                <span style={{ fontFamily: 'var(--font-mono)' }}>→ </span>{inc.action_taken}
              </div>
            )}
            <div className="incident-meta">
              <span>{formatTime(inc.timestamp)}</span>
              {inc.confidence && <span>confidence: {inc.confidence}%</span>}
              {inc.alerts_sent?.length > 0 && <span>alerts: {inc.alerts_sent.join(', ')}</span>}
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
