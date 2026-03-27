import { useState, useEffect } from 'react';
import { useDevOpsData } from './hooks/useDevOpsData';
import { useApi } from './hooks/useDevOpsData';

import OverviewPanel       from './components/dashboard/OverviewPanel';
import ControlPanel        from './components/dashboard/ControlPanel';
import MetricsChart        from './components/charts/MetricsChart';
import PodStatus           from './components/charts/PodStatus';
import LogsViewer          from './components/logs/LogsViewer';
import AIInsightsPanel     from './components/ai/AIInsightsPanel';
import AIChatbot           from './components/ai/AIChatbot';
import IncidentTimeline    from './components/incidents/IncidentTimeline';
import HealingActionsPanel from './components/incidents/HealingActionsPanel';
import AlertsPanel         from './components/alerts/AlertsPanel';

function Clock() {
  const [t, setT] = useState('');
  useEffect(() => {
    const tick = () => setT(new Date().toLocaleTimeString('en', { hour12: false }));
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);
  return <span className="topbar-time">{t}</span>;
}

export default function App() {
  const { post } = useApi();
  const { summary, metrics, logs, incidents, healing, alerts, pods, connected } = useDevOpsData();
  const [autoHeal, setAutoHeal] = useState(true);

  const handleToggleHeal = (val) => {
    setAutoHeal(val);
  };

  // Sync autoHeal from summary
  useEffect(() => {
    setAutoHeal(summary.auto_heal ?? true);
  }, [summary.auto_heal]);

  return (
    <div className="app-shell">
      {/* Background grid */}
      <div className="grid-bg" />

      {/* Ambient glows */}
      <div className="glow-blob" style={{ top: -150, left: -100, width: 500, height: 500, background: 'radial-gradient(circle, rgba(34,211,238,0.045) 0%, transparent 70%)' }} />
      <div className="glow-blob" style={{ bottom: -100, right: -100, width: 400, height: 400, background: 'radial-gradient(circle, rgba(167,139,250,0.04) 0%, transparent 70%)' }} />

      <div className="content-wrap">
        {/* ── Top bar ───────────────────────────────────────────── */}
        <header className="topbar">
          <div className="topbar-logo">
            <div className="topbar-logo-dot" />
            AI DevOps Agent
            <span style={{ fontSize: 10, color: 'var(--text-muted)', fontWeight: 400 }}>v1.0</span>
          </div>
          <div className="topbar-right">
            <span style={{
              display: 'inline-flex', alignItems: 'center', gap: 5,
              fontFamily: 'var(--font-mono)', fontSize: 10,
              color: connected ? '#22c55e' : '#ef4444',
            }}>
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: connected ? '#22c55e' : '#ef4444', boxShadow: `0 0 5px ${connected ? '#22c55e' : '#ef4444'}` }} />
              {connected ? 'LIVE' : 'RECONNECTING'}
            </span>
            <Clock />
          </div>
        </header>

        {/* ── Main grid ─────────────────────────────────────────── */}
        <main className="main-grid">

          {/* Row 1 — Overview stats */}
          <OverviewPanel summary={{ ...summary, auto_heal: autoHeal }} />

          {/* Row 2 — Metrics + Pods */}
          <MetricsChart metrics={metrics} />
          <PodStatus pods={pods} />

          {/* Row 3 — Logs + AI Insights */}
          <LogsViewer logs={logs} />
          <AIInsightsPanel incidents={incidents} />

          {/* Row 4 — Incidents + Healing + Alerts */}
          <IncidentTimeline incidents={incidents} />
          <HealingActionsPanel actions={healing} />
          <AlertsPanel alerts={alerts} />

          {/* Row 5 — Control panel (full width) */}
          <ControlPanel autoHeal={autoHeal} onToggleHeal={handleToggleHeal} />

        </main>
      </div>

      {/* Floating AI chatbot */}
      <AIChatbot />
    </div>
  );
}
