from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from app.api import metrics, logs, incidents, ai, alerts, healing, ws
from app.core.simulator import start_simulator
from app.core.auth import verify_api_key
from slowapi import Limiter
from slowapi.middleware import SlowAPIMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(start_simulator())
    yield
    task.cancel()

app = FastAPI(
    title="AI DevOps Monitoring Agent",
    description="Autonomous DevOps monitoring with AI-driven analysis and auto-healing",
    version="1.0.0",
    lifespan=lifespan,
    dependencies=[Depends(verify_api_key)],
)

# Add rate limiting middleware
app.add_middleware(SlowAPIMiddleware)

# Environment-driven CORS origins
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
cors_origins = [origin.strip() for origin in cors_origins]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(metrics.router, prefix="/api/metrics", tags=["Metrics"])
app.include_router(logs.router, prefix="/api/logs", tags=["Logs"])
app.include_router(incidents.router, prefix="/api/incidents", tags=["Incidents"])
app.include_router(ai.router, prefix="/api/ai", tags=["AI"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["Alerts"])
app.include_router(healing.router, prefix="/api/healing", tags=["Auto-Healing"])
app.include_router(ws.router, tags=["WebSocket"])

@app.get("/")
async def root():
    return {"status": "ok", "message": "AI DevOps Agent running"}

@app.get("/api/health")
async def health():
    return {"status": "healthy", "version": "1.0.0"}
