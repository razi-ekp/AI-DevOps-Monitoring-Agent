"""
Background engine:
- simulated mode: synthetic metrics/logs/incidents
- real mode: Prometheus/Loki ingestion with rule-based incidents
"""
from __future__ import annotations

import asyncio
import logging
import os
import random
import uuid
from collections import defaultdict, deque
from datetime import datetime, timedelta

from app.core.broadcaster import broadcast
from app.core.integrations import (
    USE_REAL_LOGS,
    USE_REAL_METRICS,
    fetch_loki_logs,
    fetch_prometheus_metric,
)
from app.core.remediation import execute_action
from app.core.state import store

SERVICES = [
    "api-gateway",
    "auth-service",
    "db-proxy",
    "worker-queue",
    "ml-inference",
    "cache-layer",
]

LOG_TEMPLATES = {
    "INFO": [
        lambda s: f"{s}: Request processed in {random.randint(12, 80)}ms",
        lambda s: f"{s}: Health check passed",
        lambda s: f"{s}: Pod autoscaled to {random.randint(3, 8)} replicas",
        lambda s: f"{s}: Deployment rollout complete",
    ],
    "WARN": [
        lambda s: f"{s}: Memory usage at {random.randint(70, 84)}%",
        lambda s: f"{s}: High latency p99={random.randint(400, 800)}ms",
        lambda s: f"{s}: Retry #{random.randint(1, 3)} for upstream call",
        lambda s: f"{s}: Disk usage approaching 80% threshold",
    ],
    "ERROR": [
        lambda s: f"{s}: Connection timeout after {random.randint(3000, 9000)}ms",
        lambda s: f"{s}: Database query failed - deadlock detected",
        lambda s: f"{s}: gRPC stream broken - EOF",
        lambda s: f"{s}: JWT validation error - token expired",
    ],
    "CRITICAL": [
        lambda s: f"{s}: OOMKilled - container exceeded memory limit",
        lambda s: f"{s}: CrashLoopBackOff detected (restart #{random.randint(3, 10)})",
        lambda s: f"{s}: Disk full - writes failing",
        lambda s: f"{s}: All DB connections exhausted",
    ],
}

HEALING_ACTIONS = [
    {"action": "restart", "why": "CrashLoopBackOff or readiness failures detected"},
    {"action": "scale", "why": "Sustained pressure or timeout spikes"},
    {"action": "rollback", "why": "Error rate spiked after deployment"},
    {"action": "flush-cache", "why": "Stale cache entries causing cascades"},
]

SIMULATOR_TICK_SECONDS = float(os.getenv("SIMULATOR_TICK_SECONDS", "1.5"))
SIMULATOR_LOG_EVERY_N_TICKS = max(1, int(os.getenv("SIMULATOR_LOG_EVERY_N_TICKS", "3")))
SIMULATOR_INCIDENT_PROBABILITY = max(
    0.0,
    min(1.0, float(os.getenv("SIMULATOR_INCIDENT_PROBABILITY", "0.18"))),
)

INCIDENT_ERROR_BURST_COUNT = max(1, int(os.getenv("INCIDENT_ERROR_BURST_COUNT", "3")))
INCIDENT_ERROR_BURST_WINDOW_SECONDS = max(10, int(os.getenv("INCIDENT_ERROR_BURST_WINDOW_SECONDS", "300")))
INCIDENT_COOLDOWN_SECONDS = max(10, int(os.getenv("INCIDENT_COOLDOWN_SECONDS", "300")))

USE_REAL_AUTOHEAL = os.getenv("USE_REAL_AUTOHEAL", "false").strip().lower() in {"1", "true", "yes", "on"}

_cpu = 40.0
_mem = 55.0
_net = 120.0
_last_loki_ns = None
_error_windows = defaultdict(deque)  # service -> timestamps
_incident_cooldowns = {}  # (service, description) -> datetime
logger = logging.getLogger(__name__)


def _next_metric():
    global _cpu, _mem, _net
    _cpu = max(5, min(92, _cpu + random.uniform(-4, 4.5)))
    _mem = max(20, min(90, _mem + random.uniform(-2.5, 3)))
    _net = max(0, _net + random.uniform(-20, 28))
    return {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "cpu": round(_cpu, 2),
        "memory": round(_mem, 2),
        "network": round(_net, 2),
        "disk": round(random.uniform(40, 68), 2),
        "pods": {
            service: {
                "cpu": round(random.uniform(5, 88), 1),
                "memory": round(random.uniform(20, 82), 1),
                "status": random.choices(
                    ["Running", "Running", "Running", "Running", "Pending", "CrashLoop"],
                    weights=[72, 10, 8, 6, 3, 1],
                )[0],
                "restarts": random.randint(0, 3),
            }
            for service in SERVICES
        },
    }


def _record_error_and_check_burst(service: str, now: datetime) -> bool:
    window = _error_windows[service]
    cutoff = now - timedelta(seconds=INCIDENT_ERROR_BURST_WINDOW_SECONDS)
    while window and window[0] < cutoff:
        window.popleft()
    window.append(now)
    return len(window) >= INCIDENT_ERROR_BURST_COUNT


def _incident_allowed(service: str, description: str, now: datetime) -> bool:
    key = (service, description)
    last_time = _incident_cooldowns.get(key)
    if last_time and (now - last_time).total_seconds() < INCIDENT_COOLDOWN_SECONDS:
        return False
    _incident_cooldowns[key] = now
    return True


async def _emit_incident_from_log(entry: dict):
    now = datetime.utcnow()
    if entry["level"] not in {"ERROR", "CRITICAL"}:
        return

    description = entry["message"].split(": ", 1)[-1]
    is_burst = _record_error_and_check_burst(entry["service"], now)
    if not is_burst:
        return
    if not _incident_allowed(entry["service"], description, now):
        return

    severity = "CRITICAL" if entry["level"] == "CRITICAL" else "HIGH"
    incident = {
        "id": str(uuid.uuid4()),
        "timestamp": now.isoformat(),
        "service": entry["service"],
        "severity": severity,
        "description": description,
        "status": "RESOLVING" if store.auto_heal else "ONGOING",
        "confidence": round(random.uniform(72, 97), 1),
        "root_cause": _guess_root_cause(entry["message"]),
        "recommended_action": _recommend_action(entry["message"]),
        "logs_analysis": f"Pattern: {INCIDENT_ERROR_BURST_COUNT}+ errors within {INCIDENT_ERROR_BURST_WINDOW_SECONDS}s",
        "alerts_sent": store.alert_channels,
    }
    store.add_incident(incident)
    await broadcast({"type": "incident", "data": incident})

    alert = {
        "id": str(uuid.uuid4()),
        "timestamp": now.isoformat(),
        "severity": severity,
        "service": incident["service"],
        "message": incident["description"],
        "channels": store.alert_channels,
    }
    store.add_alert(alert)
    await broadcast({"type": "alert", "data": alert})

    if store.auto_heal:
        asyncio.create_task(_heal(incident))


async def _emit_simulated_log():
    service = random.choice(SERVICES)
    level = random.choices(["INFO", "WARN", "ERROR", "CRITICAL"], weights=[72, 20, 7, 1])[0]
    template = random.choice(LOG_TEMPLATES[level])
    entry = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "level": level,
        "service": service,
        "message": template(service),
    }
    store.add_log(entry)
    await broadcast({"type": "log", "data": entry})

    if level in ("ERROR", "CRITICAL") and random.random() < SIMULATOR_INCIDENT_PROBABILITY:
        await _emit_incident_from_log(entry)


async def _emit_real_logs():
    global _last_loki_ns
    try:
        logs, latest_ns = await fetch_loki_logs(since_ns=_last_loki_ns, limit=100)
    except Exception as exc:
        logger.warning("[loki] %s", exc)
        return

    _last_loki_ns = latest_ns
    for entry in logs:
        store.add_log(entry)
        await broadcast({"type": "log", "data": entry})
        await _emit_incident_from_log(entry)


async def _emit_metric():
    if USE_REAL_METRICS:
        latest = store.get_metrics(1)
        previous = latest[-1] if latest else None
        try:
            metric = await fetch_prometheus_metric(previous=previous)
        except Exception as exc:
            logger.warning("[prometheus] %s", exc)
            metric = None
        if metric is None:
            metric = _next_metric()
    else:
        metric = _next_metric()

    store.add_metric(metric)
    await broadcast({"type": "metric", "data": metric})


async def start_simulator():
    tick = 0
    while True:
        try:
            await _emit_metric()

            if tick % SIMULATOR_LOG_EVERY_N_TICKS == 0:
                if USE_REAL_LOGS:
                    await _emit_real_logs()
                else:
                    await _emit_simulated_log()

            tick += 1
        except Exception as exc:
            logger.exception("[simulator error] %s", exc)

        await asyncio.sleep(SIMULATOR_TICK_SECONDS)


async def _heal(incident: dict):
    await asyncio.sleep(random.uniform(1.0, 2.5))

    template = random.choice(HEALING_ACTIONS)
    action = template["action"]
    why = template["why"]

    if USE_REAL_AUTOHEAL:
        action_entry = await execute_action(
            service=incident["service"],
            action=action,
            why=why,
            incident_id=incident["id"],
            confidence=incident.get("confidence", 80.0),
            manual=False,
        )
        await broadcast({"type": "healing", "data": action_entry})
        await broadcast(
            {
                "type": "incident_update",
                "data": {"id": incident["id"], "status": action_entry["result"]},
            }
        )
        return

    result = random.choices(["RESOLVED", "RESOLVED", "ESCALATED"], weights=[70, 20, 10])[0]
    action_entry = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "incident_id": incident["id"],
        "service": incident["service"],
        "action": f"Auto: {action}",
        "why": why,
        "result": result,
        "validated": result == "RESOLVED",
        "confidence": incident.get("confidence", 80.0),
    }
    store.add_healing_action(action_entry)
    store.update_incident(incident["id"], {"status": result, "action_taken": action})
    await broadcast({"type": "healing", "data": action_entry})
    await broadcast({"type": "incident_update", "data": {"id": incident["id"], "status": result}})


def _guess_root_cause(msg: str) -> str:
    if "oom" in msg.lower() or "memory" in msg.lower():
        return "Memory pressure or leak pattern detected."
    if "crashloop" in msg.lower():
        return "Liveness/readiness instability likely causing restarts."
    if "timeout" in msg.lower():
        return "Upstream latency or saturation threshold exceeded."
    if "deadlock" in msg.lower():
        return "Concurrent transaction locking contention."
    if "disk" in msg.lower():
        return "Disk saturation and/or log growth pressure."
    return "Unknown root cause - requires operator review."


def _recommend_action(msg: str) -> str:
    text = msg.lower()
    if "oom" in text or "memory" in text:
        return "restart"
    if "crashloop" in text:
        return "restart"
    if "timeout" in text:
        return "scale"
    if "deadlock" in text:
        return "rollback"
    if "disk" in text:
        return "flush-cache"
    return "restart"
