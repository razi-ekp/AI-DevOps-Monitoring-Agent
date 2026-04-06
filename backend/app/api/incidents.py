import uuid
from datetime import datetime

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field

from app.core.broadcaster import broadcast
from app.core.state import store

router = APIRouter()


@router.get("/")
async def get_incidents(limit: int = Query(50, ge=1, le=200)):
    return {"incidents": store.get_incidents(limit)}


@router.get("/{incident_id}")
async def get_incident(incident_id: str):
    for inc in store.get_incidents(200):
        if inc["id"] == incident_id:
            return inc
    raise HTTPException(status_code=404, detail="Incident not found")


class InjectIncidentRequest(BaseModel):
    service: str = Field(default="platform", min_length=1, max_length=60)
    severity: str = Field(default="CRITICAL", min_length=1, max_length=20)
    description: str = Field(
        default="Manual incident injected from API",
        min_length=3,
        max_length=300,
    )
    root_cause: str | None = Field(default="Manual test trigger")
    recommended_action: str | None = Field(default="restart")
    create_alert: bool = True


@router.post("/inject/manual")
async def inject_incident(req: InjectIncidentRequest):
    severity = req.severity.upper().strip()
    if severity not in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}:
        raise HTTPException(status_code=400, detail="Invalid severity. Use LOW|MEDIUM|HIGH|CRITICAL.")

    incident = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "service": req.service.strip(),
        "severity": severity,
        "description": req.description.strip(),
        "status": "RESOLVING" if store.auto_heal else "ONGOING",
        "confidence": 99.0,
        "root_cause": (req.root_cause or "").strip() or "Manual test trigger",
        "recommended_action": (req.recommended_action or "").strip() or "restart",
        "logs_analysis": "Manual incident injection",
        "alerts_sent": store.alert_channels,
    }
    store.add_incident(incident)
    await broadcast({"type": "incident", "data": incident})

    alert = None
    if req.create_alert:
        alert = {
            "id": str(uuid.uuid4()),
            "timestamp": incident["timestamp"],
            "severity": incident["severity"],
            "service": incident["service"],
            "message": incident["description"],
            "channels": store.alert_channels,
        }
        store.add_alert(alert)
        await broadcast({"type": "alert", "data": alert})

    return {"ok": True, "incident": incident, "alert": alert}


@router.post("/{incident_id}/resolve")
async def resolve_incident(incident_id: str):
    store.update_incident(incident_id, {"status": "RESOLVED"})
    return {"ok": True, "incident_id": incident_id}
