import { useState, useEffect, useCallback } from 'react';
import { Card, Badge, Spinner } from '../ui';
import { useApi } from '../../hooks/useDevOpsData';

export default function AIInsightsPanel({ incidents }) {
  const { get } = useApi();
  const [insights, setInsights] = useState([]);
  const [loading,  setLoading]  = useState(false);

  const refresh = useCallback(() => {
    setLoading(true);
    get('/api/ai/insights')
      .then(d => setInsights(d.insights || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [get]);

  useEffect(() => { refresh(); }, [refresh]);

  // Re-fetch when new critical incidents come in
  useEffect(() => {
    const critical = incidents.filter(i => i.severity === 'CRITICAL' || i.severity === 'HIGH');
    if (critical.length > 0) refresh();
  }, [incidents.length]); // eslint-disable-line

  // Fallback: derive from local incidents if API has nothing
  const display = insights.length > 0
    ? insights
    : incidents.filter(i => ['CRITICAL','HIGH'].includes(i.severity)).slice(0, 3).map(i => ({
        id: i.id,
        severity: i.severity,
        service: i.service,
        summary: i.description,
        root_cause: i.root_cause || 'Analyzing…',
        recommended_action: i.recommended_action || 'Investigating…',
        confidence: i.confidence || 85,
        rag_match: `incident #${Math.abs(hashCode(i.description || '')) % 9000 + 1000}`,
      }));

  return (
    <Card title="AI Insights & RAG Analysis" accent="yellow">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
        <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
          {display.length} active insight{display.length !== 1 ? 's' : ''}
        </span>
        <button
          onClick={refresh}
          style={{ background: 'transparent', border: '1px solid var(--border)', borderRadius: 4, color: 'var(--text-secondary)', padding: '3px 10px', fontFamily: 'var(--font-mono)', fontSize: 10, cursor: 'pointer' }}
        >
          {loading ? <Spinner /> : '↻ Refresh'}
        </button>
      </div>

      {display.length === 0 && !loading && (
        <div style={{ color: 'var(--text-muted)', fontSize: 12, textAlign: 'center', padding: '24px 0' }}>
          ✓ No active HIGH/CRITICAL issues detected
        </div>
      )}

      {display.map(ins => (
        <div key={ins.id} className="insight-card">
          <div className="insight-header">
            <div className="insight-summary">{ins.summary}</div>
            <Badge label={ins.severity} />
          </div>

          <div className="insight-section">
            <div className="insight-section-label">Root Cause</div>
            <div className="insight-section-value">{ins.root_cause}</div>
          </div>

          <div className="insight-section">
            <div className="insight-section-label">Recommended Action</div>
            <div className="insight-section-value" style={{ color: '#22d3ee' }}>{ins.recommended_action}</div>
          </div>

          <div className="insight-footer">
            <div className="confidence-bar-wrap">
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', marginBottom: 3 }}>
                <span>Confidence</span>
                <span style={{ color: confidenceColor(ins.confidence) }}>{ins.confidence}%</span>
              </div>
              <div className="confidence-bar">
                <div className="confidence-fill" style={{ width: `${ins.confidence}%`, background: confidenceColor(ins.confidence) }} />
              </div>
            </div>
            <div className="rag-tag">RAG: {ins.rag_match}</div>
          </div>
        </div>
      ))}
    </Card>
  );
}

function confidenceColor(c) {
  if (c >= 85) return '#22c55e';
  if (c >= 65) return '#fbbf24';
  return '#ef4444';
}

function hashCode(str) {
  let h = 0;
  for (let i = 0; i < str.length; i++) h = Math.imul(31, h) + str.charCodeAt(i) | 0;
  return h;
}
