from fastapi import APIRouter
from pydantic import BaseModel
from app.core.remediation import execute_action
from app.core.state import store

router = APIRouter()


@router.get("/actions")
async def get_healing_actions():
    return {"actions": store.get_healing_actions(50)}


class AutoHealToggle(BaseModel):
    enabled: bool


@router.post("/toggle")
async def toggle_auto_heal(body: AutoHealToggle):
    store.auto_heal = body.enabled
    return {"auto_heal": store.auto_heal}


class ManualAction(BaseModel):
    service: str
    action: str  # restart | scale | rollback | flush-cache


@router.post("/manual")
async def manual_action(body: ManualAction):
    """Manually trigger a healing action."""
    action = await execute_action(
        service=body.service,
        action=body.action,
        why="Triggered by operator via Control Panel",
        incident_id="manual",
        confidence=100.0,
        manual=True,
    )
    return {"ok": True, "action": action}
