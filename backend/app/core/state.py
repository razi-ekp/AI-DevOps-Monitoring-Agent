"""
Central in-memory state store.
In production, replace with Redis / a real database.
"""
from typing import List, Dict, Any
from collections import deque
import threading

class StateStore:
    def __init__(self):
        self._lock = threading.Lock()

        # Circular buffers
        self.metrics: deque = deque(maxlen=300)       # last 300 data points
        self.logs: deque = deque(maxlen=1000)          # last 1000 log entries
        self.incidents: deque = deque(maxlen=200)
        self.healing_actions: deque = deque(maxlen=200)
        self.alerts: deque = deque(maxlen=200)

        # Config flags
        self.auto_heal: bool = True
        self.alert_channels: List[str] = ["slack", "email"]

        # Connected websocket clients
        self.ws_clients: List[Any] = []

    def add_metric(self, point: dict):
        with self._lock:
            self.metrics.append(point)

    def add_log(self, entry: dict):
        with self._lock:
            self.logs.appendleft(entry)

    def add_incident(self, inc: dict):
        with self._lock:
            self.incidents.appendleft(inc)

    def update_incident(self, inc_id: str, updates: dict):
        with self._lock:
            for i, inc in enumerate(self.incidents):
                if inc["id"] == inc_id:
                    self.incidents[i] = {**inc, **updates}
                    break

    def add_healing_action(self, action: dict):
        with self._lock:
            self.healing_actions.appendleft(action)

    def add_alert(self, alert: dict):
        with self._lock:
            self.alerts.appendleft(alert)

    def get_metrics(self, limit: int = 60) -> List[dict]:
        with self._lock:
            items = list(self.metrics)
            return items[-limit:]

    def get_logs(self, limit: int = 100, service: str = None, level: str = None) -> List[dict]:
        with self._lock:
            items = list(self.logs)
            if service:
                items = [l for l in items if l.get("service") == service]
            if level:
                items = [l for l in items if l.get("level") == level]
            return items[:limit]

    def get_incidents(self, limit: int = 50) -> List[dict]:
        with self._lock:
            return list(self.incidents)[:limit]

    def get_healing_actions(self, limit: int = 50) -> List[dict]:
        with self._lock:
            return list(self.healing_actions)[:limit]

    def get_alerts(self, limit: int = 50) -> List[dict]:
        with self._lock:
            return list(self.alerts)[:limit]

    def get_summary(self) -> dict:
        with self._lock:
            incs = list(self.incidents)
            active = [i for i in incs if i.get("status") in ("ONGOING", "RESOLVING")]
            latest = list(self.metrics)[-1] if self.metrics else {}
            critical = any(i.get("severity") == "CRITICAL" for i in active)
            return {
                "system_health": "CRITICAL" if critical else ("WARNING" if active else "HEALTHY"),
                "services_monitored": 6,
                "active_incidents": len(active),
                "total_incidents": len(incs),
                "auto_heal": self.auto_heal,
                "cpu": latest.get("cpu", 0),
                "memory": latest.get("memory", 0),
                "network": latest.get("network", 0),
            }

# Singleton
store = StateStore()
