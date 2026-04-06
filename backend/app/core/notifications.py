from __future__ import annotations

import asyncio
import logging
import os
import smtplib
from email.message import EmailMessage

logger = logging.getLogger(__name__)

_SEVERITY_ORDER = {
    "INFO": 0,
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3,
    "CRITICAL": 4,
}


def _send_email_sync(to_email: str, subject: str, body: str) -> None:
    smtp_host = os.getenv("SMTP_HOST", "").strip()
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "").strip()
    smtp_pass = os.getenv("SMTP_PASS", "").strip()
    from_email = smtp_user or os.getenv("EMAIL_FROM", "devops-agent@localhost").strip()

    if not smtp_host:
        raise ValueError("SMTP_HOST is not configured.")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email
    msg.set_content(body)

    if smtp_port == 465:
        with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=20) as smtp:
            if smtp_user:
                smtp.login(smtp_user, smtp_pass)
            smtp.send_message(msg)
        return

    with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as smtp:
        smtp.ehlo()
        try:
            smtp.starttls()
            smtp.ehlo()
        except smtplib.SMTPException:
            # Some SMTP servers do not support STARTTLS.
            pass
        if smtp_user:
            smtp.login(smtp_user, smtp_pass)
        smtp.send_message(msg)


async def send_test_email(to_email: str, subject: str, message: str) -> None:
    await asyncio.to_thread(_send_email_sync, str(to_email), subject, message)


def should_send_email_for_alert(severity: str) -> bool:
    min_level = os.getenv("ALERT_EMAIL_MIN_SEVERITY", "CRITICAL").strip().upper()
    current = _SEVERITY_ORDER.get((severity or "INFO").upper(), 0)
    minimum = _SEVERITY_ORDER.get(min_level, _SEVERITY_ORDER["CRITICAL"])
    return current >= minimum


async def send_incident_alert_email(alert: dict, incident: dict | None = None) -> bool:
    recipient = os.getenv("ALERT_EMAIL_TO", "").strip()
    if not recipient:
        logger.warning("Skipping email alert: ALERT_EMAIL_TO is not configured.")
        return False

    service = alert.get("service", "unknown-service")
    severity = (alert.get("severity") or "INFO").upper()
    message = alert.get("message", "")
    incident_id = (incident or {}).get("id", "n/a")
    root_cause = (incident or {}).get("root_cause", "n/a")
    action = (incident or {}).get("recommended_action", "n/a")
    timestamp = alert.get("timestamp", "")

    subject = f"[{severity}] DevOps Alert - {service}"
    body = (
        "AI DevOps Agent generated an alert.\n\n"
        f"Severity: {severity}\n"
        f"Service: {service}\n"
        f"Time: {timestamp}\n"
        f"Incident ID: {incident_id}\n"
        f"Message: {message}\n"
        f"Root Cause: {root_cause}\n"
        f"Recommended Action: {action}\n"
    )

    try:
        await asyncio.to_thread(_send_email_sync, recipient, subject, body)
        logger.info("Alert email sent to %s for incident %s", recipient, incident_id)
        return True
    except ValueError as exc:
        logger.warning("Skipping email alert due to config error: %s", exc)
    except smtplib.SMTPException as exc:
        logger.warning("SMTP error while sending incident alert email: %s", exc)
    except OSError as exc:
        logger.warning("SMTP network error while sending incident alert email: %s", exc)
    return False
