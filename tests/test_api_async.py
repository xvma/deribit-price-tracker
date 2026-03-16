import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta
from app.domain.entities import PriceData
from app.infrastructure.repository import SQLAlchemyPriceRepository

pytestmark = pytest.mark.asyncio

class TestAPI:
    async def test_root_endpoint(self, client: AsyncClient):
        """Test root endpoint"""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "endpoints" in data

    async def test_health_check(self, client: AsyncClient):
        """Test health check endpoint"""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    async def test_get_prices_invalid_ticker(self, client: AsyncClient):
        """Test getting prices with invalid ticker"""
        response = await client.get("/api/v1/prices?ticker=invalid")
        assert response.status_code == 400  # Validation error

    async def test_get_latest_price_not_found(self, client: AsyncClient):
        """Test getting latest price for non-existent data"""
        response = await client.get("/api/v1/prices/latest?ticker=btc_usd")
        assert response.status_code == 404

    async def test_get_prices_by_date_invalid_format(self, client: AsyncClient):
        """Test getting prices with invalid date format"""
        response = await client.get("/api/v1/prices/by-date?ticker=btc_usd&date=invalid")
        assert response.status_code == 422

    async def test_api_documentation(self, client: AsyncClient):
        """Test API documentation is accessible"""
        response = await client.get("/docs")
        assert response.status_code == 200

    async def test_get_price_history_with_pagination(self, client: AsyncClient, db_session):
        """Test paginated price history endpoint"""
        # Add some test data
        repo = SQLAlchemyPriceRepository(db_session)
        now = datetime.utcnow()

        for i in range(5):
            await repo.save(PriceData(
                "btc_usd",
                50000.0 + i * 100,
                now - timedelta(minutes=i)
            ))

        # Test endpoint
        response = await client.get("/api/v1/prices/history?ticker=btc_usd&limit=3&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

