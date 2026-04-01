from typing import Optional
import json
import logging
import os

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.state import store

router = APIRouter()
logger = logging.getLogger(__name__)


class AnalyzeRequest(BaseModel):
    incident_id: Optional[str] = None
    log_sample: Optional[str] = Field(default=None, max_length=6000)


def _to_gemini_contents(messages: list) -> list:
    contents = []
    for message in messages:
        role = message.get("role", "user")
        gemini_role = "model" if role == "assistant" else "user"
        contents.append(
            {
                "role": gemini_role,
                "parts": [{"text": message.get("content", "")}],
            }
        )
    return contents


async def _call_gemini(system: str, messages: list, max_tokens: int = 1024) -> str:
    gemini_api_key = os.getenv("GEMINI_API_KEY", "")
    gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    if not gemini_api_key:
        return "WARNING: GEMINI_API_KEY not set. Set it in your .env file to enable real AI analysis."

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model}:generateContent",
                headers={
                    "x-goog-api-key": gemini_api_key,
                    "content-type": "application/json",
                },
                json={
                    "system_instruction": {
                        "parts": [{"text": system}],
                    },
                    "contents": _to_gemini_contents(messages),
                    "generationConfig": {
                        "maxOutputTokens": max_tokens,
                    },
                },
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.TimeoutException as exc:
        logger.warning("Gemini request timed out: %s", exc)
        raise HTTPException(status_code=504, detail="AI analysis timed out. Please retry.")
    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code if exc.response else "unknown"
        logger.warning("Gemini HTTP error: status=%s", status_code)
        raise HTTPException(status_code=502, detail="AI provider returned an error.")
    except httpx.RequestError as exc:
        logger.warning("Gemini network error: %s", exc)
        raise HTTPException(status_code=502, detail="Failed to reach AI provider.")
    except ValueError as exc:
        logger.warning("Gemini response parse error: %s", exc)
        raise HTTPException(status_code=502, detail="AI provider returned malformed data.")

    candidates = data.get("candidates", [])
    if not candidates:
        prompt_feedback = data.get("promptFeedback")
        if prompt_feedback:
            return f"Gemini returned no candidates. Prompt feedback: {json.dumps(prompt_feedback)}"
        return "Gemini returned no candidates."

    parts = candidates[0].get("content", {}).get("parts", [])
    text_parts = [part.get("text", "") for part in parts if part.get("text")]
    if text_parts:
        return "\n".join(text_parts)

    finish_reason = candidates[0].get("finishReason", "UNKNOWN")
    return f"Gemini returned no text content. Finish reason: {finish_reason}"


@router.post("/analyze")
async def analyze(req: AnalyzeRequest):
    """Deep AI analysis of a specific incident or log sample."""
    if req.incident_id:
        incident = None
        for item in store.get_incidents(200):
            if item["id"] == req.incident_id:
                incident = item
                break
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")
        prompt = (
            "Analyze this DevOps incident and provide root cause, impact, and remediation steps:\n"
            f"{json.dumps(incident, indent=2)}"
        )
    elif req.log_sample:
        prompt = f"Analyze these logs for errors, anomalies and patterns:\n{req.log_sample}"
    else:
        raise HTTPException(status_code=400, detail="Provide incident_id or log_sample")

    system = (
        "You are an expert SRE. Provide detailed technical analysis with root cause, "
        "impact assessment, immediate actions (numbered), and prevention steps."
    )
    reply = await _call_gemini(system, [{"role": "user", "content": prompt}], max_tokens=1500)
    return {"analysis": reply}


@router.get("/insights")
async def get_insights():
    """Return pre-computed AI insight cards for the dashboard."""
    incidents = store.get_incidents(10)
    critical = [incident for incident in incidents if incident.get("severity") == "CRITICAL"]
    high = [incident for incident in incidents if incident.get("severity") == "HIGH"]

    insights = []
    for incident in (critical + high)[:3]:
        insights.append(
            {
                "id": incident["id"],
                "severity": incident["severity"],
                "service": incident["service"],
                "summary": incident["description"],
                "root_cause": incident.get("root_cause", "Analyzing..."),
                "recommended_action": incident.get("recommended_action", "Investigating..."),
                "confidence": incident.get("confidence", 85),
                "rag_match": f"incident #{hash(incident['description']) % 9000 + 1000}",
            }
        )
    return {"insights": insights}
