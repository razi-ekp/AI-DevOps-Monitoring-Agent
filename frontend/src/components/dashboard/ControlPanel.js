import { useState } from 'react';
import { Card } from '../ui';
import { useApi } from '../../hooks/useDevOpsData';

const SERVICES = ['api-gateway', 'auth-service', 'db-proxy', 'worker-queue', 'ml-inference', 'cache-layer'];
const ACTIONS  = ['restart', 'scale', 'rollback', 'flush-cache'];

export default function ControlPanel({ autoHeal, onToggleHeal }) {
  const { post } = useApi();
  const [selSvc, setSelSvc]     = useState(SERVICES[0]);
  const [selAction, setSelAction] = useState(ACTIONS[0]);
  const [feedback, setFeedback] = useState('');

  const triggerManual = async () => {
    try {
      await post('/api/healing/manual', { service: selSvc, action: selAction });
      setFeedback(`✓ ${selAction} triggered on ${selSvc}`);
      setTimeout(() => setFeedback(''), 3000);
    } catch {
      setFeedback('✗ Action failed');
      setTimeout(() => setFeedback(''), 3000);
    }
  };

  const toggle = async () => {
    try {
      await post('/api/healing/toggle', { enabled: !autoHeal });
      onToggleHeal(!autoHeal);
    } catch {}
  };

  return (
    <Card title="Control Panel" accent="cyan">
      <div className="control-panel">
        <div className="toggle-row">
          <div>
            <div className="toggle-label">Auto-Healing</div>
            <div className="toggle-sub">Automated remediation engine</div>
          </div>
          <button className={`toggle-switch ${autoHeal ? 'on' : ''}`} onClick={toggle} />
        </div>

        <div style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', marginTop: 4 }}>
          MANUAL OVERRIDE
        </div>

        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <select
            className="log-filter-select"
            value={selSvc}
            onChange={e => setSelSvc(e.target.value)}
            style={{ flex: 1 }}
          >
            {SERVICES.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
          <select
            className="log-filter-select"
            value={selAction}
            onChange={e => setSelAction(e.target.value)}
          >
            {ACTIONS.map(a => <option key={a} value={a}>{a}</option>)}
          </select>
        </div>

        <button
          onClick={triggerManual}
          style={{
            background: 'rgba(34,211,238,0.1)', border: '1px solid rgba(34,211,238,0.3)',
            borderRadius: 6, color: 'var(--accent-cyan)', padding: '8px 16px',
            fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 600,
            cursor: 'pointer', transition: 'all 0.15s',
          }}
        >
          ▶ Execute Action
        </button>

        {feedback && (
          <div style={{
            fontFamily: 'var(--font-mono)', fontSize: 11,
            color: feedback.startsWith('✓') ? '#22c55e' : '#ef4444',
            padding: '6px 10px', background: 'rgba(255,255,255,0.03)',
            borderRadius: 4, border: '1px solid var(--border)',
          }}>
            {feedback}
          </div>
        )}
      </div>
    </Card>
  );
}
