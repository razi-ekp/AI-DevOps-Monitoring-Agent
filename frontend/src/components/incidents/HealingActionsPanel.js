import { Card, Badge, formatTime, truncate } from '../ui';

const RESULT_COLOR = { RESOLVED: '#22c55e', ESCALATED: '#a78bfa', FAILED: '#ef4444' };

export default function HealingActionsPanel({ actions }) {
  return (
    <Card title="Auto-Healing Engine" accent="green">
      <div className="healing-list">
        {actions.length === 0 && (
          <div style={{ color: 'var(--text-muted)', fontSize: 12, textAlign: 'center', padding: '20px 0' }}>
            No healing actions triggered yet
          </div>
        )}
        {actions.map(a => (
          <div key={a.id} className="healing-item">
            <div className="healing-action-name">⚡ {a.action}</div>
            <div className="healing-why">
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)' }}>WHY: </span>
              {truncate(a.why, 80)}
            </div>
            <div className="healing-footer">
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--accent-cyan)' }}>
                {a.service}
              </span>
              <Badge label={a.result} variant={a.result} />
              {a.validated && (
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: '#22c55e' }}>✓ validated</span>
              )}
              <span style={{ marginLeft: 'auto', fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)' }}>
                {formatTime(a.timestamp)}
              </span>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
