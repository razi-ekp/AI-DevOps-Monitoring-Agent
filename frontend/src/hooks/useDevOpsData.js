import { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';

const API = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const WS  = process.env.REACT_APP_WS_URL  || 'ws://localhost:8000/ws';

function countActiveIncidents(items) {
  return items.filter(i => i && i.status !== 'RESOLVED').length;
}

export function useApi() {
  const get  = useCallback((path, params) => axios.get(`${API}${path}`, { params }).then(r => r.data), []);
  const post = useCallback((path, body)   => axios.post(`${API}${path}`, body).then(r => r.data), []);
  return { get, post };
}

export function useDevOpsData() {
  const { get } = useApi();

  const [summary,  setSummary]  = useState({ system_health: 'HEALTHY', services_monitored: 6, active_incidents: 0, cpu: 0, memory: 0, network: 0, auto_heal: true });
  const [metrics,  setMetrics]  = useState([]);
  const [logs,     setLogs]     = useState([]);
  const [incidents,setIncidents]= useState([]);
  const [healing,  setHealing]  = useState([]);
  const [alerts,   setAlerts]   = useState([]);
  const [pods,     setPods]     = useState({});
  const [connected,setConnected]= useState(false);

  const wsRef = useRef(null);

  // Initial data load
  useEffect(() => {
    Promise.all([
      get('/api/metrics/summary'),
      get('/api/metrics', { limit: 60 }),
      get('/api/logs', { limit: 100 }),
      get('/api/incidents', { limit: 50 }),
      get('/api/healing/actions'),
      get('/api/alerts', { limit: 50 }),
      get('/api/metrics/pods'),
    ]).then(([sum, met, log, inc, heal, alrt, pod]) => {
      const incomingIncidents = inc.incidents || [];
      setSummary({
        ...sum,
        active_incidents: countActiveIncidents(incomingIncidents),
      });
      setMetrics(met.metrics || []);
      setLogs(log.logs || []);
      setIncidents(incomingIncidents);
      setHealing(heal.actions || []);
      setAlerts(alrt.alerts || []);
      setPods(pod.pods || {});
    }).catch(err => console.warn('Initial load error:', err));
  }, [get]);

  useEffect(() => {
    const activeCount = countActiveIncidents(incidents);
    setSummary(prev => ({
      ...prev,
      active_incidents: activeCount,
      system_health: activeCount === 0 ? 'HEALTHY' : prev.system_health,
    }));
  }, [incidents]);

  // WebSocket live updates
  useEffect(() => {
    let pingInterval;
    let retryTimeout;

    function connect() {
      const ws = new WebSocket(WS);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
        pingInterval = setInterval(() => ws.readyState === 1 && ws.send('ping'), 25000);
      };

      ws.onclose = () => {
        setConnected(false);
        clearInterval(pingInterval);
        retryTimeout = setTimeout(connect, 3000);
      };

      ws.onerror = () => ws.close();

      ws.onmessage = (e) => {
        try {
          const { type, data } = JSON.parse(e.data);

          if (type === 'metric') {
            setMetrics(m => {
              const next = [...m, {
                ...data,
                t: new Date(data.timestamp).toLocaleTimeString('en', { hour12: false }),
              }];
              return next.slice(-60);
            });
            setPods(data.pods || {});
            setSummary(prev => ({
              ...prev,
              cpu: data.cpu,
              memory: data.memory,
              network: data.network,
            }));
          }

          if (type === 'log') {
            setLogs(prev => [data, ...prev].slice(0, 200));
          }

          if (type === 'incident') {
            setIncidents(prev => [data, ...prev].slice(0, 100));
            setSummary(prev => ({
              ...prev,
              system_health: data.severity === 'CRITICAL' ? 'CRITICAL' : prev.system_health === 'CRITICAL' ? 'CRITICAL' : 'WARNING',
            }));
          }

          if (type === 'incident_update') {
            setIncidents(prev => prev.map(i => i.id === data.id ? { ...i, ...data } : i));
          }

          if (type === 'healing') {
            setHealing(prev => [data, ...prev].slice(0, 100));
          }

          if (type === 'alert') {
            setAlerts(prev => [data, ...prev].slice(0, 100));
          }
        } catch (err) {
          console.warn('WS parse error:', err);
        }
      };
    }

    connect();
    return () => {
      clearInterval(pingInterval);
      clearTimeout(retryTimeout);
      wsRef.current?.close();
    };
  }, []);

  return { summary, metrics, logs, incidents, healing, alerts, pods, connected };
}
