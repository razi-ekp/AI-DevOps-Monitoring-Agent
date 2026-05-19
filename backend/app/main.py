import asyncio
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api import ai, alerts, healing, incidents, logs, metrics, ws
from app.core.auth import verify_api_key
from app.core.logging_config import configure_logging
from app.core.simulator import start_simulator

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
configure_logging()


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
)

app.state.limiter = ai.limiter

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

app.include_router(metrics.router, prefix="/api/metrics", tags=["Metrics"], dependencies=[Depends(verify_api_key)])
app.include_router(logs.router, prefix="/api/logs", tags=["Logs"], dependencies=[Depends(verify_api_key)])
app.include_router(incidents.router, prefix="/api/incidents", tags=["Incidents"], dependencies=[Depends(verify_api_key)])
app.include_router(ai.router, prefix="/api/ai", tags=["AI"], dependencies=[Depends(verify_api_key)])
app.include_router(alerts.router, prefix="/api/alerts", tags=["Alerts"], dependencies=[Depends(verify_api_key)])
app.include_router(healing.router, prefix="/api/healing", tags=["Auto-Healing"], dependencies=[Depends(verify_api_key)])
app.include_router(ws.router, tags=["WebSocket"])

Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

@app.get("/")
async def root():
    return {"status": "ok", "message": "AI DevOps Agent running"}

@app.get("/api/health")
async def health():
    return {"status": "healthy", "version": "1.0.0"}
