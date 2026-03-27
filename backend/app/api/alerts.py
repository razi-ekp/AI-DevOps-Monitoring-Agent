from fastapi import APIRouter, Query
from pydantic import BaseModel
from app.core.state import store

router = APIRouter()


@router.get("/")
async def get_alerts(limit: int = Query(50, ge=1, le=200)):
    return {"alerts": store.get_alerts(limit)}


class ChannelConfig(BaseModel):
    channels: list[str]  # e.g. ["slack", "email"]


@router.post("/channels")
async def set_channels(cfg: ChannelConfig):
    store.alert_channels = cfg.channels
    return {"ok": True, "channels": store.alert_channels}
