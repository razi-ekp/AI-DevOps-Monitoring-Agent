import { useState, useMemo } from 'react';
import { Card, Badge, formatTime } from '../ui';

const SERVICES = ['all', 'api-gateway', 'auth-service', 'db-proxy', 'worker-queue', 'ml-inference', 'cache-layer'];
const LEVELS   = ['all', 'INFO', 'WARN', 'ERROR', 'CRITICAL'];

export default function LogsViewer({ logs }) {
  const [svcFilter, setSvcFilter]   = useState('all');
  const [lvlFilter, setLvlFilter]   = useState('all');

  const filtered = useMemo(() => {
    return logs.filter(l => {
      if (svcFilter !== 'all' && l.service !== svcFilter) return false;
      if (lvlFilter !== 'all' && l.level !== lvlFilter) return false;
      return true;
    });
  }, [logs, svcFilter, lvlFilter]);

  const summary = useMemo(() => {
    const counts = { INFO: 0, WARN: 0, ERROR: 0, CRITICAL: 0 };
    const serviceCounts = {};
    filtered.forEach(log => {
      counts[log.level] = (counts[log.level] || 0) + 1;
      serviceCounts[log.service] = (serviceCounts[log.service] || 0) + 1;
    });

    let busiestService = 'n/a';
    let maxCount = 0;
    Object.entries(serviceCounts).forEach(([svc, count]) => {
      if (count > maxCount) {
        busiestService = svc;
        maxCount = count;
      }
    });

    const lastError = filtered.find(log => log.level === 'ERROR' || log.level === 'CRITICAL');
    return { counts, busiestService, lastError };
  }, [filtered]);

  const intel = useMemo(() => {
    const patternCounts = {};
    const serviceErrorCounts = {};

    filtered.forEach(log => {
      const shortMsg = (log.message?.split(': ').slice(1).join(': ') || log.message || 'unknown').trim();
      patternCounts[shortMsg] = (patternCounts[shortMsg] || 0) + 1;
      if (log.level === 'ERROR' || log.level === 'CRITICAL') {
        serviceErrorCounts[log.service] = (serviceErrorCounts[log.service] || 0) + 1;
      }
    });

    const topPatterns = Object.entries(patternCounts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([message, count]) => ({ message, count }));

    const noisyServices = Object.entries(serviceErrorCounts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([service, count]) => ({ service, count }));

    return { topPatterns, noisyServices };
  }, [filtered]);

  return (
    <Card title="Live Log Stream" accent="cyan" className="span-2 log-card">
      <div className="log-filters">
        <select className="log-filter-select" value={svcFilter} onChange={e => setSvcFilter(e.target.value)}>
          {SERVICES.map(s => <option key={s} value={s}>{s}</option>)}
        </select>
        <select className="log-filter-select" value={lvlFilter} onChange={e => setLvlFilter(e.target.value)}>
          {LEVELS.map(l => <option key={l} value={l}>{l}</option>)}
        </select>
        <span style={{ marginLeft: 'auto', fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)' }}>
          {filtered.length} entries
        </span>
      </div>
      <div className="log-list">
        {filtered.slice(0, 80).map(log => (
          <div key={log.id} className={`log-entry level-${log.level}`}>
            <span className="log-time">{formatTime(log.timestamp)}</span>
            <Badge label={log.level} variant={log.level} />
            <span className="log-svc">{log.service}</span>
            <span className={`log-msg level-${log.level}`}>{log.message?.split(': ').slice(1).join(': ')}</span>
          </div>
        ))}
        {filtered.length === 0 && (
          <div style={{ color: 'var(--text-muted)', fontSize: 12, padding: '20px 0', textAlign: 'center' }}>
            No logs match current filters
          </div>
        )}
      </div>
      <div className="log-summary">
        <div className="log-summary-item">
          <div className="log-summary-label">Error Signals</div>
          <div className="log-summary-value">{summary.counts.ERROR + summary.counts.CRITICAL}</div>
          <div className="log-summary-meta">
            WARN {summary.counts.WARN} · INFO {summary.counts.INFO}
          </div>
        </div>
        <div className="log-summary-item">
          <div className="log-summary-label">Busiest Service</div>
          <div className="log-summary-value log-summary-service">{summary.busiestService}</div>
          <div className="log-summary-meta">{filtered.length} visible logs</div>
        </div>
        <div className="log-summary-item">
          <div className="log-summary-label">Last Error</div>
          <div className="log-summary-value">{summary.lastError ? formatTime(summary.lastError.timestamp) : '--:--:--'}</div>
          <div className="log-summary-meta">
            {summary.lastError ? summary.lastError.service : 'No error in current filter'}
          </div>
        </div>
      </div>
      <div className="log-intel">
        <div className="log-intel-panel">
          <div className="log-intel-title">Recurring Patterns</div>
          <div className="log-intel-list">
            {intel.topPatterns.length > 0 ? intel.topPatterns.map(item => (
              <div className="log-intel-item" key={`pattern-${item.message}`}>
                <span className="log-intel-text">{item.message}</span>
                <span className="log-intel-pill">{item.count}</span>
              </div>
            )) : (
              <div className="log-intel-empty">No pattern data for current filter</div>
            )}
          </div>
        </div>
        <div className="log-intel-panel">
          <div className="log-intel-title">Noisy Services</div>
          <div className="log-intel-list">
            {intel.noisyServices.length > 0 ? intel.noisyServices.map(item => (
              <div className="log-intel-item" key={`service-${item.service}`}>
                <span className="log-intel-text log-intel-service">{item.service}</span>
                <span className="log-intel-pill">{item.count}</span>
              </div>
            )) : (
              <div className="log-intel-empty">No active error signals</div>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
}
