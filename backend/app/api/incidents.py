from fastapi import APIRouter, Query, HTTPException
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


@router.post("/{incident_id}/resolve")
async def resolve_incident(incident_id: str):
    store.update_incident(incident_id, {"status": "RESOLVED"})
    return {"ok": True, "incident_id": incident_id}
