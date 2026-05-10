"""
Tests for auth endpoints.
Run: pytest tests/ -v
"""
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch

# We test the app in isolation by mocking DB/Redis
pytestmark = pytest.mark.asyncio


@pytest.fixture
async def client():
    """Create async test client with mocked DB."""
    with patch("config.database.connect_db", new_callable=AsyncMock), \
         patch("config.redis.connect_redis", new_callable=AsyncMock), \
         patch("app.services.scheduler.start_scheduler"), \
         patch("app.services.scheduler.stop_scheduler"):
        from main import app
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            yield ac


async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


async def test_register_missing_fields(client):
    resp = await client.post("/api/v1/auth/register", json={"email": "bad"})
    assert resp.status_code == 422  # Validation error


async def test_login_invalid_credentials(client):
    with patch("app.models.user.User.find_one", new_callable=AsyncMock, return_value=None):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "wrongpass"},
        )
        assert resp.status_code == 401
