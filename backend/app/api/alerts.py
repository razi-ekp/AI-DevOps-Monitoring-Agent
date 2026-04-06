import logging
import os
import smtplib
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.core.broadcaster import broadcast
from app.core.notifications import send_test_email as send_test_email_message
from app.core.state import store

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/")
async def get_alerts(limit: int = Query(50, ge=1, le=200)):
    return {"alerts": store.get_alerts(limit)}


class ChannelConfig(BaseModel):
    channels: list[str]  # e.g. ["slack", "email"]


@router.post("/channels")
async def set_channels(cfg: ChannelConfig):
    store.alert_channels = cfg.channels
    return {"ok": True, "channels": store.alert_channels}


class TestEmailRequest(BaseModel):
    to: str | None = None
    subject: str = "AI DevOps Agent Test Alert"
    message: str = (
        "This is a test email alert from AI DevOps Agent. "
        "If you received this, SMTP delivery is working."
    )


class TestAlertRequest(BaseModel):
    severity: str = "INFO"
    service: str = "notifications"
    message: str = "Manual test alert from dashboard"


@router.post("/test")
async def send_test_alert(req: TestAlertRequest):
    severity = (req.severity or "INFO").upper()
    if severity not in {"INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"}:
        raise HTTPException(status_code=400, detail="Invalid severity value.")

    alert = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "severity": severity,
        "service": req.service or "notifications",
        "message": req.message or "Manual test alert from dashboard",
        "channels": [],
    }
    store.add_alert(alert)
    await broadcast({"type": "alert", "data": alert})
    return {"ok": True, "alert": alert}


@router.post("/test-email")
async def send_test_email(req: TestEmailRequest):
    target = req.to or os.getenv("ALERT_EMAIL_TO", "").strip()
    if not target:
        raise HTTPException(
            status_code=400,
            detail="No recipient configured. Set ALERT_EMAIL_TO or provide 'to' in request.",
        )

    try:
        await send_test_email_message(str(target), req.subject, req.message)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except smtplib.SMTPException as exc:
        logger.warning("SMTP error while sending test email: %s", exc)
        raise HTTPException(status_code=502, detail=f"SMTP delivery failed: {exc}")
    except OSError as exc:
        logger.warning("SMTP network error while sending test email: %s", exc)
        raise HTTPException(status_code=502, detail=f"SMTP connection failed: {exc}")

    alert = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "severity": "INFO",
        "service": "notifications",
        "message": f"Test email sent to {target}",
        "channels": ["email"],
    }
    store.add_alert(alert)
    await broadcast({"type": "alert", "data": alert})
    return {"ok": True, "recipient": str(target)}
