from fastapi import APIRouter, Query
from app.core.state import store

router = APIRouter()


@router.get("/")
async def get_metrics(limit: int = Query(60, ge=1, le=300)):
    """Return the last N metric data points."""
    return {"metrics": store.get_metrics(limit)}


@router.get("/summary")
async def get_summary():
    """Return system-level summary for the overview panel."""
    return store.get_summary()


@router.get("/pods")
async def get_pods():
    """Return current pod statuses from the latest metric snapshot."""
    metrics = store.get_metrics(1)
    if not metrics:
        return {"pods": {}}
    return {"pods": metrics[-1].get("pods", {})}
