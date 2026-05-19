"""
Basic API tests for the DevOps Agent backend.
"""

import pytest


@pytest.mark.asyncio
async def test_health_endpoint(api_client):
    """Test that /api/health returns 200."""
    response = await api_client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"


@pytest.mark.asyncio
async def test_metrics_endpoint(api_client):
    """Test that /api/metrics returns a list."""
    response = await api_client.get("/api/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data
    assert isinstance(data["metrics"], list)


@pytest.mark.asyncio
async def test_incidents_endpoint(api_client):
    """Test that /api/incidents returns a list."""
    response = await api_client.get("/api/incidents")
    assert response.status_code == 200
    data = response.json()
    assert "incidents" in data
    assert isinstance(data["incidents"], list)


@pytest.mark.asyncio
async def test_ai_analyze_invalid_body(api_client):
    """Test that POST /api/ai/analyze with no body returns 400."""
    response = await api_client.post("/api/ai/analyze", json={})
    assert response.status_code == 400
    assert response.json()["detail"] == "Provide incident_id or log_sample"


@pytest.mark.asyncio
async def test_auth_rejected(api_client, monkeypatch):
    """Requests are rejected when API_SECRET_KEY is set and no header is provided."""
    monkeypatch.setenv("API_SECRET_KEY", "secret")
    response = await api_client.get("/api/health")
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing API key"


@pytest.mark.asyncio
async def test_auth_accepted(api_client, monkeypatch):
    """Requests succeed when the correct API key header is provided."""
    monkeypatch.setenv("API_SECRET_KEY", "secret")
    response = await api_client.get(
        "/api/health",
        headers={"X-API-Key": "secret"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_inject_incident(api_client):
    """POST /api/incidents/inject/manual returns a new incident with the expected service."""
    payload = {
        "service": "payment",
        "severity": "HIGH",
        "description": "Manual injection test",
        "root_cause": "test root cause",
        "recommended_action": "restart",
        "create_alert": False,
    }
    response = await api_client.post("/api/incidents/inject/manual", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["incident"]["service"] == "payment"
    assert data["incident"]["severity"] == "HIGH"


@pytest.mark.asyncio
async def test_alerts_endpoint(api_client):
    """GET /api/alerts returns a list of alerts."""
    response = await api_client.get("/api/alerts")
    assert response.status_code == 200
    data = response.json()
    assert "alerts" in data
    assert isinstance(data["alerts"], list)
