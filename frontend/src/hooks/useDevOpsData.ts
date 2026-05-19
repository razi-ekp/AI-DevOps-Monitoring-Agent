import { useState, useEffect, useRef, useCallback } from 'react';
import axios, { AxiosResponse } from 'axios';

import {
  Alert,
  HealingAction,
  Incident,
  LogEntry,
  Metric,
  PodMap,
  Summary,
  UseApiReturn,
  UseDevOpsDataReturn,
} from '../types';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const WS_TOKEN = import.meta.env.VITE_WS_TOKEN || '';
const WS = (import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws') + (WS_TOKEN ? `?token=${WS_TOKEN}` : '');

function countActiveIncidents(items: Incident[]): number {
  return items.filter((i) => i && i.status !== 'RESOLVED').length;
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

function isMetric(value: unknown): value is Metric {
  return (
    isObject(value) &&
    typeof value.timestamp === 'string' &&
    (typeof value.cpu === 'number' || typeof value.memory === 'number' || typeof value.network === 'number')
  );
}

function isLogEntry(value: unknown): value is LogEntry {
  return (
    isObject(value) &&
    typeof value.id === 'string' &&
    typeof value.timestamp === 'string' &&
    typeof value.service === 'string' &&
    typeof value.level === 'string'
  );
}

function isIncident(value: unknown): value is Incident {
  return (
    isObject(value) &&
    typeof value.id === 'string' &&
    typeof value.service === 'string' &&
    typeof value.severity === 'string' &&
    typeof value.description === 'string' &&
    typeof value.status === 'string'
  );
}

function isHealingAction(value: unknown): value is HealingAction {
  return (
    isObject(value) &&
    typeof value.id === 'string' &&
    typeof value.service === 'string' &&
    typeof value.action === 'string' &&
    typeof value.why === 'string' &&
    typeof value.result === 'string'
  );
}

function isAlert(value: unknown): value is Alert {
  return (
    isObject(value) &&
    typeof value.id === 'string' &&
    typeof value.service === 'string' &&
    typeof value.message === 'string' &&
    typeof value.severity === 'string'
  );
}

function isPodMap(value: unknown): value is PodMap {
  return (
    isObject(value) &&
    Object.values(value).every(
      (item) => isObject(item) &&
        (typeof item.cpu === 'number' || typeof item.memory === 'number' || typeof item.restarts === 'number')
    )
  );
}

function parseWebSocketData(raw: unknown): { type: string; data: unknown } | null {
  if (!isObject(raw)) {
    return null;
  }

  const type = raw.type;
  const data = raw.data;

  if (typeof type !== 'string') {
    return null;
  }

  return { type, data };
}

export function useApi(): UseApiReturn {
  const get = useCallback(<T = unknown>(path: string, params?: Record<string, unknown>) => {
    return axios.get<T>(`${API}${path}`, { params }).then((response: AxiosResponse<T>) => response.data);
  }, []);

  const post = useCallback(<T = unknown>(path: string, body: unknown) => {
    return axios.post<T>(`${API}${path}`, body).then((response: AxiosResponse<T>) => response.data);
  }, []);

  return { get, post };
}

export function useDevOpsData(): UseDevOpsDataReturn {
  const { get } = useApi();

  const [summary, setSummary] = useState<Summary>({
    system_health: 'HEALTHY',
    services_monitored: 6,
    active_incidents: 0,
    cpu: 0,
    memory: 0,
    network: 0,
    auto_heal: true,
  });
  const [metrics, setMetrics] = useState<Metric[]>([]);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [healing, setHealing] = useState<HealingAction[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [pods, setPods] = useState<PodMap>({});
  const [connected, setConnected] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    Promise.all([
      get<Summary>('/api/metrics/summary'),
      get<{ metrics: Metric[] }>('/api/metrics', { limit: 60 }),
      get<{ logs: LogEntry[] }>('/api/logs', { limit: 100 }),
      get<{ incidents: Incident[] }>('/api/incidents', { limit: 50 }),
      get<{ actions: HealingAction[] }>('/api/healing/actions'),
      get<{ alerts: Alert[] }>('/api/alerts', { limit: 50 }),
      get<{ pods: PodMap }>('/api/metrics/pods'),
    ])
      .then(([sum, met, log, inc, heal, alrt, pod]) => {
        const incomingIncidents = Array.isArray(inc.incidents) ? inc.incidents.filter(isIncident) : [];

        setSummary({
          ...sum,
          active_incidents: countActiveIncidents(incomingIncidents),
        });
        setMetrics(Array.isArray(met.metrics) ? met.metrics.filter(isMetric) : []);
        setLogs(Array.isArray(log.logs) ? log.logs.filter(isLogEntry) : []);
        setIncidents(incomingIncidents);
        setHealing(Array.isArray(heal.actions) ? heal.actions.filter(isHealingAction) : []);
        setAlerts(Array.isArray(alrt.alerts) ? alrt.alerts.filter(isAlert) : []);
        setPods(isPodMap(pod.pods) ? pod.pods : {});
      })
      .catch((err) => console.warn('Initial load error:', err));
  }, [get]);

  useEffect(() => {
    const activeCount = countActiveIncidents(incidents);
    setSummary((prev) => ({
      ...prev,
      active_incidents: activeCount,
      system_health: activeCount === 0 ? 'HEALTHY' : prev.system_health,
    }));
  }, [incidents]);

  useEffect(() => {
    let pingInterval: number | undefined;
    let retryTimeout: number | undefined;

    function connect() {
      const ws = new WebSocket(WS);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
        pingInterval = window.setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send('ping');
          }
        }, 25000);
      };

      ws.onclose = () => {
        setConnected(false);
        if (pingInterval !== undefined) {
          window.clearInterval(pingInterval);
        }
        retryTimeout = window.setTimeout(connect, 3000);
      };

      ws.onerror = () => ws.close();

      ws.onmessage = (event) => {
        try {
          const raw = JSON.parse(event.data) as unknown;
          const message = parseWebSocketData(raw);
          if (!message) {
            return;
          }

          const { type, data } = message;

          if (type === 'metric' && isMetric(data)) {
            setMetrics((previous) => {
              const next = [
                ...previous,
                {
                  ...data,
                  t: data.t ?? new Date(data.timestamp).toLocaleTimeString('en', { hour12: false }),
                },
              ];
              return next.slice(-60);
            });
            setPods(isPodMap(data.pods) ? data.pods : {});
            setSummary((prev) => ({
              ...prev,
              cpu: data.cpu ?? prev.cpu,
              memory: data.memory ?? prev.memory,
              network: data.network ?? prev.network,
            }));
          }

          if (type === 'log' && isLogEntry(data)) {
            setLogs((previous) => [data, ...previous].slice(0, 200));
          }

          if (type === 'incident' && isIncident(data)) {
            setIncidents((previous) => [data, ...previous].slice(0, 100));
            setSummary((prev) => ({
              ...prev,
              system_health:
                data.severity === 'CRITICAL'
                  ? 'CRITICAL'
                  : prev.system_health === 'CRITICAL'
                  ? 'CRITICAL'
                  : 'WARNING',
            }));
          }

          if (type === 'incident_update' && isIncident(data)) {
            setIncidents((previous) => previous.map((item) => (item.id === data.id ? { ...item, ...data } : item)));
          }

          if (type === 'healing' && isHealingAction(data)) {
            setHealing((previous) => [data, ...previous].slice(0, 100));
          }

          if (type === 'alert' && isAlert(data)) {
            setAlerts((previous) => [data, ...previous].slice(0, 100));
          }
        } catch (err) {
          console.warn('WS parse error:', err);
        }
      };
    }

    connect();
    return () => {
      if (pingInterval !== undefined) {
        window.clearInterval(pingInterval);
      }
      if (retryTimeout !== undefined) {
        window.clearTimeout(retryTimeout);
      }
      wsRef.current?.close();
    };
  }, []);

  return { summary, metrics, logs, incidents, healing, alerts, pods, connected };
}
