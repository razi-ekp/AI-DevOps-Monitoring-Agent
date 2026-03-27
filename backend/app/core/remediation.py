"""
Safe remediation executor.
Supports dry-run and optional kubectl-backed actions with guardrails.
"""
from __future__ import annotations

import asyncio
import os
import uuid
from collections import deque
from datetime import datetime, timedelta

from app.core.state import store


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


AUTOHEAL_EXECUTOR = os.getenv("AUTOHEAL_EXECUTOR", "dry-run").strip().lower()  # dry-run | kubectl
AUTOHEAL_DRY_RUN = _env_bool("AUTOHEAL_DRY_RUN", True)
AUTOHEAL_NAMESPACE = os.getenv("AUTOHEAL_NAMESPACE", "default")
AUTOHEAL_KUBECTL_PATH = os.getenv("AUTOHEAL_KUBECTL_PATH", "kubectl")
AUTOHEAL_SCALE_REPLICAS = int(os.getenv("AUTOHEAL_SCALE_REPLICAS", "3"))
AUTOHEAL_COOLDOWN_SECONDS = int(os.getenv("AUTOHEAL_COOLDOWN_SECONDS", "180"))
AUTOHEAL_MAX_ACTIONS_PER_HOUR = int(os.getenv("AUTOHEAL_MAX_ACTIONS_PER_HOUR", "20"))
AUTOHEAL_ALLOWLIST = {
    item.strip()
    for item in os.getenv("AUTOHEAL_SERVICE_ALLOWLIST", "").split(",")
    if item.strip()
}

_ACTION_TIMELINE = deque(maxlen=500)
_LAST_ACTION_AT = {}


def _guardrail_violation(service: str, action: str) -> str | None:
    if AUTOHEAL_ALLOWLIST and service not in AUTOHEAL_ALLOWLIST:
        return f"Service '{service}' is not in AUTOHEAL_SERVICE_ALLOWLIST."

    now = datetime.utcnow()
    cutoff = now - timedelta(hours=1)
    while _ACTION_TIMELINE and _ACTION_TIMELINE[0] < cutoff:
        _ACTION_TIMELINE.popleft()

    if len(_ACTION_TIMELINE) >= AUTOHEAL_MAX_ACTIONS_PER_HOUR:
        return "Hourly action limit exceeded. Escalating."

    last_at = _LAST_ACTION_AT.get(service)
    if last_at and (now - last_at).total_seconds() < AUTOHEAL_COOLDOWN_SECONDS:
        return f"Cooldown active for {service}. Escalating."

    if action not in {"restart", "scale", "rollback", "flush-cache"}:
        return f"Unsupported action '{action}'."

    return None


async def _run_kubectl(*args: str) -> tuple[int, str]:
    proc = await asyncio.create_subprocess_exec(
        AUTOHEAL_KUBECTL_PATH,
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    output = (stdout or b"").decode("utf-8", errors="replace").strip()
    err = (stderr or b"").decode("utf-8", errors="replace").strip()
    merged = output if output else err
    return proc.returncode, merged


async def _execute_real_action(service: str, action: str) -> tuple[bool, str]:
    deployment = f"deployment/{service}"
    ns_args = ("-n", AUTOHEAL_NAMESPACE)

    if action == "restart":
        code, out = await _run_kubectl("rollout", "restart", deployment, *ns_args)
        return code == 0, out or "rollout restart executed"

    if action == "rollback":
        code, out = await _run_kubectl("rollout", "undo", deployment, *ns_args)
        return code == 0, out or "rollout undo executed"

    if action == "scale":
        code, out = await _run_kubectl(
            "scale",
            deployment,
            *ns_args,
            f"--replicas={AUTOHEAL_SCALE_REPLICAS}",
        )
        return code == 0, out or f"scaled to {AUTOHEAL_SCALE_REPLICAS}"

    if action == "flush-cache":
        return False, "flush-cache requires service-specific runbook integration"

    return False, f"unknown action '{action}'"


async def execute_action(
    *,
    service: str,
    action: str,
    why: str,
    incident_id: str,
    confidence: float,
    manual: bool = False,
) -> dict:
    """
    Execute (or simulate) a remediation action and persist it into store.
    """
    violation = _guardrail_violation(service, action)
    now = datetime.utcnow()
    if violation:
        result = "ESCALATED"
        validated = False
        detail = violation
    else:
        if AUTOHEAL_DRY_RUN or AUTOHEAL_EXECUTOR == "dry-run":
            result = "RESOLVED"
            validated = False
            detail = f"DRY_RUN: would execute '{action}' on {service}"
        elif AUTOHEAL_EXECUTOR == "kubectl":
            ok, detail = await _execute_real_action(service, action)
            result = "RESOLVED" if ok else "ESCALATED"
            validated = ok
        else:
            result = "ESCALATED"
            validated = False
            detail = f"Unknown AUTOHEAL_EXECUTOR='{AUTOHEAL_EXECUTOR}'"

    if result == "RESOLVED":
        _ACTION_TIMELINE.append(now)
        _LAST_ACTION_AT[service] = now

    action_entry = {
        "id": str(uuid.uuid4()),
        "timestamp": now.isoformat(),
        "incident_id": incident_id,
        "service": service,
        "action": f"{'Manual' if manual else 'Auto'}: {action}",
        "why": why,
        "result": result,
        "validated": validated,
        "confidence": confidence,
        "detail": detail,
    }
    store.add_healing_action(action_entry)
    if incident_id and incident_id != "manual":
        store.update_incident(
            incident_id,
            {
                "status": result,
                "action_taken": action,
                "action_detail": detail,
            },
        )
    return action_entry
