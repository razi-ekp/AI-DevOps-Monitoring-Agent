# Real Data Setup

This project currently generates fake metrics, logs, and incidents in
`backend/app/core/simulator.py`. To connect real infrastructure data, keep the
same API shape and replace the simulator inputs.

Current status in this repo:
- Real ingestion hooks are already implemented behind env flags.
- Set `USE_REAL_METRICS=true` to pull from Prometheus.
- Set `USE_REAL_LOGS=true` to pull from Loki.
- Set `USE_REAL_AUTOHEAL=true` with `AUTOHEAL_EXECUTOR=kubectl` for real actions.
- Keep `AUTOHEAL_DRY_RUN=true` until you validate guardrails in staging.

## What to replace

The dashboard reads data from the in-memory store in:

- `backend/app/core/state.py`

The simulator currently writes into that store from:

- `backend/app/core/simulator.py`

To connect real sources, keep the store methods the same and change where the
data comes from:

- `store.add_metric(...)`
- `store.add_log(...)`
- `store.add_incident(...)`
- `store.add_alert(...)`

## Real metrics from Prometheus

Replace `_next_metric()` in `backend/app/core/simulator.py` with a function that
queries Prometheus and returns the same payload shape:

```python
import httpx
from datetime import datetime

PROMETHEUS_URL = "http://localhost:9090"


async def _prom_query(client: httpx.AsyncClient, query: str) -> float:
    resp = await client.get(
        f"{PROMETHEUS_URL}/api/v1/query",
        params={"query": query},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    results = data.get("data", {}).get("result", [])
    if not results:
        return 0.0
    return float(results[0]["value"][1])


async def _next_metric():
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

    return {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "cpu": round(cpu, 2),
        "memory": round(memory, 2),
        "network": round(network, 2),
        "disk": round(disk, 2),
        "pods": {},
    }
```

If you already have Kubernetes metrics in Prometheus, populate the `pods` object
from `kube_pod_container_resource_requests`, `container_memory_working_set_bytes`,
and `rate(container_cpu_usage_seconds_total[5m])`.

## Real logs from Loki

Replace the random log creation in `start_simulator()` with a Loki query and map
the results into the current log shape:

```python
LOKI_URL = "http://localhost:3100"


async def _fetch_logs() -> list[dict]:
    query = '{job="varlogs"} |= ""'
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{LOKI_URL}/loki/api/v1/query_range",
            params={
                "query": query,
                "limit": 20,
                "direction": "backward",
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

    entries = []
    for stream in data.get("data", {}).get("result", []):
        service = stream.get("stream", {}).get("app", "unknown-service")
        for ts, line in stream.get("values", []):
            entries.append(
                {
                    "id": str(uuid.uuid4()),
                    "timestamp": datetime.utcnow().isoformat(),
                    "level": _level_from_line(line),
                    "service": service,
                    "message": line,
                }
            )
    return entries
```

Add a small parser for log levels:

```python
def _level_from_line(line: str) -> str:
    lowered = line.lower()
    if "critical" in lowered or "panic" in lowered:
        return "CRITICAL"
    if "error" in lowered or "exception" in lowered:
        return "ERROR"
    if "warn" in lowered:
        return "WARN"
    return "INFO"
```

## Converting real logs into incidents

Right now incidents are created here:

- `backend/app/core/simulator.py`

This block:

1. checks for `ERROR` or `CRITICAL`
2. randomly creates an incident

For real data, replace the random condition with deterministic rules such as:

- create incident when `5xx rate > threshold`
- create incident when `pod restart count > threshold`
- create incident when a Loki query finds repeated exceptions in the last 5 minutes
- create incident when Prometheus alerts are firing

Example rule:

```python
if entry["level"] in ("ERROR", "CRITICAL"):
    repeated = recent_error_count_by_service[entry["service"]] >= 5
    if repeated:
        store.add_incident(...)
```

## Best next implementation path

If you want the safest upgrade path, do it in this order:

1. Replace metrics first and leave logs simulated.
2. Replace logs second and keep incident creation rule-based.
3. Replace incident generation with real alert/threshold logic.
4. Only then remove the simulator completely.

## Suggested environment variables

Add these to `backend/.env` when you wire in real sources:

```env
PROMETHEUS_URL=http://localhost:9090
LOKI_URL=http://localhost:3100
K8S_NAMESPACE=default
USE_REAL_METRICS=true
USE_REAL_LOGS=true
```
