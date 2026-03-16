import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.repository import SQLAlchemyPriceRepository
from app.domain.entities import PriceData

pytestmark = pytest.mark.asyncio

class TestPriceRepository:
    async def test_save_price(self, db_session: AsyncSession):
        """Test saving a price record"""
        repo = SQLAlchemyPriceRepository(db_session)
        now = datetime.utcnow()

        price_data = PriceData(
            ticker="btc_usd",
            price=50000.0,
            timestamp=now
        )

        await repo.save(price_data)

        # Verify by getting latest
        latest = await repo.get_latest_by_ticker("btc_usd")
        assert latest is not None
        assert latest.ticker == "btc_usd"
        assert latest.price == 50000.0
        assert latest.timestamp.replace(microsecond=0) == now.replace(microsecond=0)

    async def test_get_latest_by_ticker(self, db_session: AsyncSession):
        """Test getting latest price for ticker"""
        repo = SQLAlchemyPriceRepository(db_session)
        now = datetime.utcnow()

        # Create multiple records
        prices = [
            PriceData("btc_usd", 50000.0, now - timedelta(minutes=2)),
            PriceData("btc_usd", 51000.0, now - timedelta(minutes=1)),
            PriceData("btc_usd", 52000.0, now),
        ]

        for price in prices:
            await repo.save(price)

        latest = await repo.get_latest_by_ticker("btc_usd")
        assert latest is not None
        assert latest.price == 52000.0
        assert latest.timestamp.replace(microsecond=0) == now.replace(microsecond=0)

    async def test_get_by_ticker(self, db_session: AsyncSession):
        """Test getting all prices for ticker"""
        repo = SQLAlchemyPriceRepository(db_session)
        now = datetime.utcnow()

        # Create records for different tickers
        await repo.save(PriceData("btc_usd", 50000.0, now))
        await repo.save(PriceData("btc_usd", 51000.0, now))
        await repo.save(PriceData("eth_usd", 3000.0, now))

        btc_prices = await repo.get_by_ticker("btc_usd")
        assert len(btc_prices) == 2

        eth_prices = await repo.get_by_ticker("eth_usd")
        assert len(eth_prices) == 1

    async def test_get_by_ticker_and_date_range(self, db_session: AsyncSession):
        """Test getting prices within date range"""
        repo = SQLAlchemyPriceRepository(db_session)
        now = datetime.utcnow()

        # Create records with different timestamps
        timestamps = [
            now - timedelta(days=5),
            now - timedelta(days=3),
            now - timedelta(days=1),
            now
        ]

        for ts in timestamps:
            await repo.save(PriceData("btc_usd", 50000.0, ts))

        # Query last 2 days
        start_date = now - timedelta(days=2)
        end_date = now

        prices = await repo.get_by_ticker_and_date_range("btc_usd", start_date, end_date)

        assert len(prices) == 2
        for price in prices:
            assert start_date <= price.timestamp <= end_date

    async def test_get_price_history_pagination(self, db_session: AsyncSession):
        """Test paginated price history"""
        repo = SQLAlchemyPriceRepository(db_session)
        now = datetime.utcnow()

        # Create 15 records
        for i in range(15):
            await repo.save(PriceData(
                "btc_usd",
                50000.0 + i * 100,
                now - timedelta(minutes=i)
            ))

        # Test pagination
        first_page = await repo.get_price_history("btc_usd", limit=10, offset=0)
        assert len(first_page) == 10

        second_page = await repo.get_price_history("btc_usd", limit=10, offset=10)
        assert len(second_page) == 5

        # Verify ordering (newest first)
        assert first_page[0].timestamp > first_page[-1].timestamp

    async def test_delete_old_records(self, db_session: AsyncSession):
        """Test deleting old records"""
        repo = SQLAlchemyPriceRepository(db_session)
        now = datetime.utcnow()

        # Create old and new records
        await repo.save(PriceData("btc_usd", 50000.0, now - timedelta(days=40)))
        await repo.save(PriceData("btc_usd", 51000.0, now - timedelta(days=20)))
        await repo.save(PriceData("btc_usd", 52000.0, now))

        # Delete records older than 30 days
        deleted = await repo.delete_old_records(days=30)

        assert deleted == 1

        # Verify remaining records
        remaining = await repo.get_by_ticker("btc_usd")
        assert len(remaining) == 2
        for price in remaining:
            assert price.timestamp > now - timedelta(days=30)