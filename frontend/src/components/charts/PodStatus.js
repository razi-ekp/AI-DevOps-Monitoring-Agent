import { Card, StatusDot } from '../ui';

const STATUS_COLOR = { Running: '#22c55e', Pending: '#fbbf24', CrashLoop: '#ef4444' };

export default function PodStatus({ pods }) {
  const entries = Object.entries(pods);

  return (
    <Card title="Kubernetes Pods" accent="cyan">
      {entries.length === 0 ? (
        <div style={{ color: 'var(--text-muted)', fontSize: 12, textAlign: 'center', padding: 20 }}>Connecting…</div>
      ) : (
        <div className="pod-grid">
          {entries.map(([name, pod]) => (
            <div key={name} className="pod-item">
              <div className="pod-name" title={name}>
                {name.length > 14 ? name.slice(0, 14) + '…' : name}
              </div>
              <div className="pod-status-row">
                <StatusDot status={pod.status} />
                <span style={{ fontSize: 10, fontFamily: 'var(--font-mono)', color: STATUS_COLOR[pod.status] || '#64748b' }}>
                  {pod.status}
                </span>
                {pod.restarts > 0 && (
                  <span style={{ fontSize: 10, fontFamily: 'var(--font-mono)', color: '#ef4444', marginLeft: 'auto' }}>
                    ↺{pod.restarts}
                  </span>
                )}
              </div>
              <div className="pod-bar-wrap">
                <PodBar label="CPU" value={pod.cpu} color="#22d3ee" />
                <PodBar label="MEM" value={pod.memory} color="#a78bfa" />
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}

function PodBar({ label, value, color }) {
  const pct = Math.min(100, Math.round(value || 0));
  const c = pct > 85 ? '#ef4444' : pct > 65 ? '#fbbf24' : color;
  return (
    <div style={{ marginBottom: 4 }}>
      <div className="pod-bar-label">
        <span>{label}</span>
        <span style={{ color: c }}>{pct}%</span>
      </div>
      <div className="pod-bar">
        <div className="pod-bar-fill" style={{ width: `${pct}%`, background: c }} />
      </div>
    </div>
  );
}
