from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from sqlalchemy.exc import SQLAlchemyError
import logging
from ..core.models import PriceRecord
from ..domain.entities import PriceData
from ..domain.interfaces import PriceRepository

logger = logging.getLogger(__name__)

class SQLAlchemyPriceRepository(PriceRepository):
    """SQLAlchemy implementation of price repository"""
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def save(self, price_data: PriceData) -> None:
        """Save price data to database"""
        try:
            record = PriceRecord(
                ticker=price_data.ticker,
                price=price_data.price,
                timestamp=price_data.timestamp
            )
            self._session.add(record)
            await self._session.commit()
            logger.debug(f"Saved price for {price_data.ticker}: {price_data.price}")
        except SQLAlchemyError as e:
            await self._session.rollback()
            logger.error(f"Failed to save price: {e}")
            raise
    
    async def get_by_ticker(self, ticker: str) -> List[PriceData]:
        """Get all prices for ticker"""
        try:
            query = select(PriceRecord)\
                .where(PriceRecord.ticker == ticker)\
                .order_by(desc(PriceRecord.timestamp))
            
            result = await self._session.execute(query)
            records = result.scalars().all()
            
            return [
                PriceData(
                    id=r.id,
                    ticker=r.ticker,
                    price=r.price,
                    timestamp=r.timestamp
                ) for r in records
            ]
        except SQLAlchemyError as e:
            logger.error(f"Failed to get prices for {ticker}: {e}")
            raise
    
    async def get_latest_by_ticker(self, ticker: str) -> Optional[PriceData]:
        """Get latest price for ticker"""
        try:
            query = select(PriceRecord)\
                .where(PriceRecord.ticker == ticker)\
                .order_by(desc(PriceRecord.timestamp))\
                .limit(1)
            
            result = await self._session.execute(query)
            record = result.scalar_one_or_none()
            
            if record:
                return PriceData(
                    id=record.id,
                    ticker=record.ticker,
                    price=record.price,
                    timestamp=record.timestamp
                )
            return None
        except SQLAlchemyError as e:
            logger.error(f"Failed to get latest price for {ticker}: {e}")
            raise
    
    async def get_by_ticker_and_date_range(
        self, 
        ticker: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[PriceData]:
        """Get prices for ticker within date range"""
        try:
            query = select(PriceRecord)\
                .where(
                    and_(
                        PriceRecord.ticker == ticker,
                        PriceRecord.timestamp >= start_date,
                        PriceRecord.timestamp <= end_date
                    )
                )\
                .order_by(desc(PriceRecord.timestamp))
            
            result = await self._session.execute(query)
            records = result.scalars().all()
            
            return [
                PriceData(
                    id=r.id,
                    ticker=r.ticker,
                    price=r.price,
                    timestamp=r.timestamp
                ) for r in records
            ]
        except SQLAlchemyError as e:
            logger.error(f"Failed to get prices for {ticker} in date range: {e}")
            raise
    
    async def get_price_history(
        self, 
        ticker: str, 
        limit: int = 100,
        offset: int = 0
    ) -> List[PriceData]:
        """Get paginated price history"""
        try:
            query = select(PriceRecord)\
                .where(PriceRecord.ticker == ticker)\
                .order_by(desc(PriceRecord.timestamp))\
                .limit(limit)\
                .offset(offset)
            
            result = await self._session.execute(query)
            records = result.scalars().all()
            
            return [
                PriceData(
                    id=r.id,
                    ticker=r.ticker,
                    price=r.price,
                    timestamp=r.timestamp
                ) for r in records
            ]
        except SQLAlchemyError as e:
            logger.error(f"Failed to get price history for {ticker}: {e}")
            raise
    
    async def delete_old_records(self, days: int = 30) -> int:
        """Delete records older than specified days"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get count of records to delete
            count_query = select(func.count()).select_from(PriceRecord)\
                .where(PriceRecord.timestamp < cutoff_date)
            result = await self._session.execute(count_query)
            count = result.scalar()
            
            # Delete records
            delete_query = select(PriceRecord).where(PriceRecord.timestamp < cutoff_date)
            result = await self._session.execute(delete_query)
            records = result.scalars().all()
            
            for record in records:
                await self._session.delete(record)
            
            await self._session.commit()
            logger.info(f"Deleted {count} records older than {days} days")
            return count
            
        except SQLAlchemyError as e:
            await self._session.rollback()
            logger.error(f"Failed to delete old records: {e}")
            raise
    
    async def get_statistics(self, ticker: str, days: int = 7) -> Optional[dict]:
        """Get price statistics for ticker"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            query = select(
                func.count().label('count'),
                func.min(PriceRecord.price).label('min_price'),
                func.max(PriceRecord.price).label('max_price'),
                func.avg(PriceRecord.price).label('avg_price'),
                func.min(PriceRecord.timestamp).label('first_timestamp'),
                func.max(PriceRecord.timestamp).label('last_timestamp')
            ).where(
                and_(
                    PriceRecord.ticker == ticker,
                    PriceRecord.timestamp >= start_date,
                    PriceRecord.timestamp <= end_date
                )
            )
            
            result = await self._session.execute(query)
            stats = result.one()
            
            if stats.count == 0:
                return None
            
            # Get first and last prices
            first_price_query = select(PriceRecord.price)\
                .where(
                    and_(
                        PriceRecord.ticker == ticker,
                        PriceRecord.timestamp == stats.first_timestamp
                    )
                )
            last_price_query = select(PriceRecord.price)\
                .where(
                    and_(
                        PriceRecord.ticker == ticker,
                        PriceRecord.timestamp == stats.last_timestamp
                    )
                )
            
            first_price_result = await self._session.execute(first_price_query)
            last_price_result = await self._session.execute(last_price_query)
            
            first_price = first_price_result.scalar()
            last_price = last_price_result.scalar()
            
            return {
                "ticker": ticker,
                "period_days": days,
                "count": stats.count,
                "min_price": stats.min_price,
                "max_price": stats.max_price,
                "avg_price": stats.avg_price,
                "first_price": first_price,
                "last_price": last_price,
                "change": last_price - first_price,
                "change_percent": ((last_price - first_price) / first_price) * 100 if first_price else 0
            }
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to get statistics for {ticker}: {e}")
            raise