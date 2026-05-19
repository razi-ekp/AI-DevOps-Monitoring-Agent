
from fastapi import APIRouter, Query

from app.core.state import store

router = APIRouter()


@router.get("")
async def get_logs(
    limit: int = Query(100, ge=1, le=500),
    service: str | None = Query(None),
    level: str | None = Query(None),
):
    """Return filtered log entries."""
    return {"logs": store.get_logs(limit=limit, service=service, level=level)}


@router.get("/services")
async def get_services():
    """Return list of known services."""
    return {
        "services": [
            "api-gateway", "auth-service", "db-proxy",
            "worker-queue", "ml-inference", "cache-layer",
        ]
    }
