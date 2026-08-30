import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
import uuid
from unittest.mock import AsyncMock

from app.main import app
from app.api.payments import get_payment_service
from app.services.payment_service import PaymentService
from app.models.payment import PaymentStatus
from app.core.security import verify_api_key

# We would normally use testcontainers here to spin up postgres:
# from testcontainers.postgres import PostgresContainer
# from testcontainers.redis import RedisContainer
# 
# However, for demonstration and speed within this isolated test environment, 
# we'll continue mocking the DB dependency but inject the security keys properly.

class MockDbSession:
    def __init__(self):
        self.objects = []
        
    async def commit(self): pass
    async def refresh(self, obj): pass
    def add(self, obj): 
        self.objects.append(obj)
        if hasattr(obj, 'id') and not obj.id:
            obj.id = uuid.uuid4()
            
    async def execute(self, stmt):
        class MockResult:
            def scalar_one_or_none(self):
                return None
        return MockResult()

def override_get_payment_service():
    mock_db = MockDbSession()
    mock_gateway = AsyncMock()
    return PaymentService(mock_db, mock_gateway)

def override_api_key():
    return "sk_test_123456789"

app.dependency_overrides[get_payment_service] = override_get_payment_service
app.dependency_overrides[verify_api_key] = override_api_key

@pytest.mark.asyncio
async def test_create_payment():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/payments", 
            json={
                "amount": 1500,
                "currency": "KES",
                "customer_phone": "254700000000"
            },
            headers={"X-API-Key": "sk_test_123456789"}
        )
        assert response.status_code == 201
        data = response.json()
        assert "transaction_id" in data
        assert data["status"] == "pending"
        assert data["amount"] == "1500.00"

@pytest.mark.asyncio
async def test_get_payment_not_found():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            f"/payments/fake-transaction-id",
            headers={"X-API-Key": "sk_test_123456789"}
        )
        assert response.status_code == 404

# Forced CI refresh
