"""
Optional real data integrations for metrics and logs.
Falls back gracefully when providers are unavailable.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Optional

import httpx


SERVICES = [
    "api-gateway",
    "auth-service",
    "db-proxy",
    "worker-queue",
    "ml-inference",
    "cache-layer",
]


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


USE_REAL_METRICS = _env_bool("USE_REAL_METRICS", False)
USE_REAL_LOGS = _env_bool("USE_REAL_LOGS", False)

PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://localhost:9090").rstrip("/")
LOKI_URL = os.getenv("LOKI_URL", "http://localhost:3100").rstrip("/")
LOKI_QUERY = os.getenv("LOKI_QUERY", '{job="varlogs"}')
LOKI_LABEL_SERVICE_KEY = os.getenv("LOKI_LABEL_SERVICE_KEY", "app")

METRICS_TIMEOUT_SECONDS = float(os.getenv("REAL_METRICS_TIMEOUT_SECONDS", "10"))
LOGS_TIMEOUT_SECONDS = float(os.getenv("REAL_LOGS_TIMEOUT_SECONDS", "10"))


async def _prom_query(client: httpx.AsyncClient, query: str) -> Optional[float]:
    response = await client.get(
        f"{PROMETHEUS_URL}/api/v1/query",
        params={"query": query},
        timeout=METRICS_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    payload = response.json()
    results = payload.get("data", {}).get("result", [])
    if not results:
        return None
    try:
        return float(results[0]["value"][1])
    except Exception:
        return None


async def fetch_prometheus_metric(previous: Optional[dict] = None) -> Optional[dict]:
    """
    Return a metric point in the same shape as simulator output, or None.
    """
    async with httpx.AsyncClient() as client:
        cpu = await _prom_query(
            client,
            '100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)',
        )
        memory = await _prom_query(
            client,
            '(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100',
        )
        network = await _prom_query(
            client,
            'sum(rate(node_network_receive_bytes_total[5m]) + rate(node_network_transmit_bytes_total[5m])) / 1024',
        )
        disk = await _prom_query(
            client,
            '(1 - (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"})) * 100',
        )

    if cpu is None and memory is None and network is None and disk is None:
        return None

    pods = previous.get("pods", {}) if previous else {}
    if not pods:
        pods = {
            service: {
                "cpu": round(max(0.0, min(95.0, (cpu or 0.0) * 0.7)), 1),
                "memory": round(max(0.0, min(95.0, (memory or 0.0) * 0.7)), 1),
                "status": "Running",
                "restarts": 0,
            }
            for service in SERVICES
        }

    return {
        "id": f"metric-{datetime.now(timezone.utc).timestamp()}",
        "timestamp": datetime.utcnow().isoformat(),
        "cpu": round(cpu or 0.0, 2),
        "memory": round(memory or 0.0, 2),
        "network": round(network or 0.0, 2),
        "disk": round(disk or 0.0, 2),
        "pods": pods,
    }


def _to_iso_utc(ns: str) -> str:
    # Loki timestamp in nanoseconds as string.
    value = int(ns)
    seconds = value / 1_000_000_000
    return datetime.fromtimestamp(seconds, tz=timezone.utc).replace(tzinfo=None).isoformat()


def _level_from_line(line: str) -> str:
    text = line.lower()
    if "critical" in text or "panic" in text or "oomkilled" in text:
        return "CRITICAL"
    if "error" in text or "exception" in text or "failed" in text or "timeout" in text:
        return "ERROR"
    if "warn" in text or "warning" in text:
        return "WARN"
    return "INFO"


async def fetch_loki_logs(
    since_ns: Optional[int] = None,
    limit: int = 100,
) -> tuple[list[dict], Optional[int]]:
    params = {
        "query": LOKI_QUERY,
        "limit": limit,
        "direction": "forward",
    }
    if since_ns:
        params["start"] = str(since_ns + 1)

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{LOKI_URL}/loki/api/v1/query_range",
            params=params,
            timeout=LOGS_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()

    logs = []
    latest_ns = since_ns
    for stream in payload.get("data", {}).get("result", []):
        service = stream.get("stream", {}).get(LOKI_LABEL_SERVICE_KEY, "unknown-service")
        for ts_ns, line in stream.get("values", []):
            ts_int = int(ts_ns)
            latest_ns = max(latest_ns or ts_int, ts_int)
            logs.append(
                {
                    "id": f"log-{ts_ns}-{abs(hash(line)) % 100000}",
                    "timestamp": _to_iso_utc(ts_ns),
                    "level": _level_from_line(line),
                    "service": service,
                    "message": f"{service}: {line}",
                }
            )

    logs.sort(key=lambda item: item["timestamp"], reverse=True)
    return logs, latest_ns
