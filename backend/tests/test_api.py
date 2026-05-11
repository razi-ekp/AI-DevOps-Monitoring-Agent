"""
Basic API tests for the DevOps Agent backend.
"""
import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from app.main import app


@pytest.mark.asyncio
async def test_health_endpoint():
    """Test that /api/health returns 200."""
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data


@pytest.mark.asyncio
async def test_metrics_endpoint():
    """Test that /api/metrics returns a list."""
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.get("/api/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data
        assert isinstance(data["metrics"], list)


@pytest.mark.asyncio
async def test_incidents_endpoint():
    """Test that /api/incidents returns a list."""
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.get("/api/incidents")
        assert response.status_code == 200
        data = response.json()
        assert "incidents" in data
        assert isinstance(data["incidents"], list)


@pytest.mark.asyncio
async def test_ai_analyze_invalid_body():
    """Test that POST /api/ai/analyze with no body returns 422."""
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.post("/api/ai/analyze", json={})
        # Should return 422 for validation error
        assert response.status_code in [401, 422]  # 401 if auth is enabled, 422 if not