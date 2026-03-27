from typing import List, Optional
import json
import os

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.state import store

router = APIRouter()

PROJECT_CONTEXT = """Project facts:
- This repository is an AI DevOps Monitoring Agent, not a generic microservices application.
- Backend: FastAPI application in backend/app with REST APIs and a WebSocket endpoint.
- Frontend: React dashboard in frontend/src.
- Core behavior: simulates infrastructure metrics, logs, incidents, alerts, and auto-healing actions in memory.
- Dashboard areas shown in the UI include overview, metrics, pod status, logs, incidents, alerts, healing actions, AI insights, and an AI chatbot.
- API areas in the backend include metrics, logs, incidents, alerts, healing, AI, and WebSocket streaming.
- The simulator generates synthetic data unless the project is configured to connect to real systems.
- Auto-heal actions are controlled by the backend and can be toggled on or off.
- AI analysis uses Gemini when GEMINI_API_KEY is configured.

Answering rules:
- Answer only from the project facts above plus the current runtime state included in the prompt.
- Do not invent services, gateways, databases, queues, authentication systems, or infrastructure that are not explicitly present in this project context.
- If the user asks something not supported by the known project context, say that directly and then answer with what is known.
- When asked to explain the project, describe this repo's dashboard, backend, simulator, alerts, incidents, and auto-healing features in simple terms.
"""


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]


class AnalyzeRequest(BaseModel):
    incident_id: Optional[str] = None
    log_sample: Optional[str] = None


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


@router.post("/chat")
async def chat(req: ChatRequest):
    """AI chatbot endpoint that answers questions about the current system state."""
    summary = store.get_summary()
    recent_logs = store.get_logs(limit=10)
    recent_incidents = store.get_incidents(limit=5)

    system = f"""You are an expert AI DevOps assistant embedded in this project's monitoring dashboard.
{PROJECT_CONTEXT}

Current system state:
- Health: {summary['system_health']}
- CPU: {summary['cpu']:.1f}%  Memory: {summary['memory']:.1f}%  Network: {summary['network']:.0f} KB/s
- Active incidents: {summary['active_incidents']}
- Auto-heal: {'ON' if summary['auto_heal'] else 'OFF'}

Recent incidents (last 5):
{json.dumps(recent_incidents, indent=2)}

Recent logs (last 10):
{chr(10).join(log['message'] for log in recent_logs)}

Answer concisely and technically. Use bullet points where helpful.
"""
    messages = [{"role": message.role, "content": message.content} for message in req.messages]
    reply = await _call_gemini(system, messages)
    return {"reply": reply}


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
