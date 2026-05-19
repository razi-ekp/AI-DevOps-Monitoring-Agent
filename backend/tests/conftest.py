import importlib
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient


@pytest.fixture(autouse=True)
def mock_redis(mocker):
    redis_client = MagicMock()
    redis_client.lrange = AsyncMock(return_value=[])
    redis_client.lpush = AsyncMock(return_value=0)
    redis_client.ltrim = AsyncMock(return_value=True)
    redis_client.delete = AsyncMock(return_value=0)

    mocker.patch("redis.asyncio.from_url", return_value=redis_client)
    return redis_client


@pytest.fixture
def mock_gemini(mocker, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")

    fake_response = MagicMock()
    fake_response.raise_for_status = MagicMock()
    fake_response.json = MagicMock(
        return_value={
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": "Test AI response from Gemini"}]
                    }
                }
            ]
        }
    )

    mocker.patch("httpx.AsyncClient.post", new=AsyncMock(return_value=fake_response))
    return fake_response


@pytest_asyncio.fixture
async def api_client(monkeypatch):
    monkeypatch.delenv("API_SECRET_KEY", raising=False)

    backend_dir = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(backend_dir))

    import app.main as app_main
    importlib.reload(app_main)

    async with AsyncClient(transport=ASGITransport(app=app_main.app), base_url="http://testserver") as client:
        yield client
