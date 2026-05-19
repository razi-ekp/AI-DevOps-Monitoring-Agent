export type HealthStatus = 'HEALTHY' | 'WARNING' | 'CRITICAL' | string;

export interface Summary {
  system_health: HealthStatus;
  services_monitored: number;
  active_incidents: number;
  cpu?: number;
  memory?: number;
  network?: number;
  auto_heal?: boolean;
}

export interface PodInfo {
  cpu?: number;
  memory?: number;
  status?: string;
  restarts?: number;
}

export type PodMap = Record<string, PodInfo>;

export type MetricKey = 'cpu' | 'memory' | 'network' | 'disk';

export interface Metric {
  id: string;
  timestamp: string;
  cpu?: number;
  memory?: number;
  network?: number;
  disk?: number;
  pods?: PodMap;
  t?: string;
}

export interface LogEntry {
  id: string;
  timestamp: string;
  service: string;
  level: string;
  message?: string;
}

export interface Incident {
  id: string;
  timestamp: string;
  service: string;
  severity: string;
  description: string;
  status: string;
  confidence?: number;
  root_cause?: string;
  recommended_action?: string;
  action_taken?: string;
  alerts_sent?: string[];
}

export interface HealingAction {
  id: string;
  timestamp: string;
  incident_id: string;
  service: string;
  action: string;
  why: string;
  result: string;
  validated?: boolean;
  confidence?: number;
  detail?: string;
}

export interface Alert {
  id: string;
  timestamp: string;
  severity: string;
  service: string;
  message?: string;
  channels?: string[];
}

export interface AIInsight {
  id: string;
  severity: string;
  service: string;
  summary: string;
  root_cause: string;
  recommended_action: string;
  confidence: number;
  rag_match: string;
}

export interface UseApiReturn {
  get: <T = unknown>(path: string, params?: Record<string, unknown>) => Promise<T>;
  post: <T = unknown>(path: string, body: unknown) => Promise<T>;
}

export interface UseDevOpsDataReturn {
  summary: Summary;
  metrics: Metric[];
  logs: LogEntry[];
  incidents: Incident[];
  healing: HealingAction[];
  alerts: Alert[];
  pods: PodMap;
  connected: boolean;
}

export interface LogsViewerProps {
  logs: LogEntry[];
}

export interface IncidentTimelineProps {
  incidents: Incident[];
}

export interface HealingActionsPanelProps {
  actions: HealingAction[];
}

export interface OverviewPanelProps {
  summary: Summary;
}

export interface ControlPanelProps {
  autoHeal: boolean;
  onToggleHeal: (value: boolean) => void;
}

export interface MetricsChartProps {
  metrics: Metric[];
}

export interface PodStatusProps {
  pods: PodMap;
}

export interface AlertsPanelProps {
  alerts: Alert[];
}

export interface AIInsightsPanelProps {
  incidents: Incident[];
}
