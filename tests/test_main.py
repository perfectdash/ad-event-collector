import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.publisher import publisher
from unittest.mock import AsyncMock

@pytest_asyncio.fixture
async def async_client():
    # I did this to setup lifespan events during testing
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_health_endpoint(async_client: AsyncClient):
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "queue_size" in data

@pytest.mark.asyncio
async def test_valid_ad_event(async_client: AsyncClient):
    payload = {
        "event_id": "a4d33458-1be2-4b2a-bf3a-9f5b24479e02",
        "timestamp": "2026-07-25T12:00:00Z",
        "campaign_id": "camp-98765",
        "advertiser_id": "adv-12345",
        "event_type": "click",
        "cost": 1.25,
        "user_agent": "Mozilla/5.0 Chrome/120.0",
        "ip_address": "192.168.1.1"
    }
    
    response = await async_client.post("/api/v1/events", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "Accepted"
    assert data["event_id"] == payload["event_id"]

@pytest.mark.asyncio
async def test_invalid_uuid(async_client: AsyncClient):
    payload = {
        "event_id": "invalid-uuid-format",
        "timestamp": "2026-07-25T12:00:00Z",
        "campaign_id": "camp-98765",
        "advertiser_id": "adv-12345",
        "event_type": "click",
        "cost": 0.5
    }
    response = await async_client.post("/api/v1/events", json=payload)
    assert response.status_code == 422
    assert "event_id must be a valid UUID" in response.text

@pytest.mark.asyncio
async def test_invalid_campaign_id(async_client: AsyncClient):
    payload = {
        "event_id": "a4d33458-1be2-4b2a-bf3a-9f5b24479e02",
        "timestamp": "2026-07-25T12:00:00Z",
        "campaign_id": "invalid-prefix-98765",
        "advertiser_id": "adv-12345",
        "event_type": "impression",
        "cost": 0.0
    }
    response = await async_client.post("/api/v1/events", json=payload)
    assert response.status_code == 422
    assert "campaign_id must start with prefix" in response.text

@pytest.mark.asyncio
async def test_invalid_event_type(async_client: AsyncClient):
    payload = {
        "event_id": "a4d33458-1be2-4b2a-bf3a-9f5b24479e02",
        "timestamp": "2026-07-25T12:00:00Z",
        "campaign_id": "camp-98765",
        "advertiser_id": "adv-12345",
        "event_type": "invalid_type",
        "cost": 0.0
    }
    response = await async_client.post("/api/v1/events", json=payload)
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_negative_cost(async_client: AsyncClient):
    payload = {
        "event_id": "a4d33458-1be2-4b2a-bf3a-9f5b24479e02",
        "timestamp": "2026-07-25T12:00:00Z",
        "campaign_id": "camp-98765",
        "advertiser_id": "adv-12345",
        "event_type": "conversion",
        "cost": -10.0
    }
    response = await async_client.post("/api/v1/events", json=payload)
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_backpressure_rate_limit(async_client: AsyncClient, monkeypatch):
    # I did this to mock enqueue_event and simulate a full queue
    mock_enqueue = AsyncMock(return_value=False)
    monkeypatch.setattr(publisher, "enqueue_event", mock_enqueue)
    
    payload = {
        "event_id": "a4d33458-1be2-4b2a-bf3a-9f5b24479e02",
        "timestamp": "2026-07-25T12:00:00Z",
        "campaign_id": "camp-98765",
        "advertiser_id": "adv-12345",
        "event_type": "click",
        "cost": 1.0
    }
    response = await async_client.post("/api/v1/events", json=payload)
    assert response.status_code == 429
    assert "Queue is full" in response.json()["detail"]
