import asyncio
from celery import shared_task
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import logging
from ..core.config import settings
from ..infrastructure.repository import SQLAlchemyPriceRepository
from ..infrastructure.deribit_client import DeribitAPIClient
from ..use_cases.price_use_cases import FetchAndSavePriceUseCase

logger = logging.getLogger(__name__)

# Create async engine for worker
async_engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_size=5,
    max_overflow=2,
    pool_pre_ping=True
)

AsyncSessionLocal = sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

@shared_task(
    name="app.worker.tasks.fetch_and_save_price",
    bind=True,
    max_retries=3,
    soft_time_limit=30,
    time_limit=60
)
def fetch_and_save_price(self, ticker: str):
    """
    Celery task to fetch and save price for ticker
    """
    logger.info(f"Starting fetch_and_save_price task for {ticker}")
    
    async def _async_task():
        # Create async session
        async with AsyncSessionLocal() as session:
            client = None
            try:
                # Initialize dependencies
                repository = SQLAlchemyPriceRepository(session)
                client = DeribitAPIClient()
                
                # Execute use case
                use_case = FetchAndSavePriceUseCase(repository, client)
                result = await use_case.execute(ticker)
                
                logger.info(f"Successfully saved {ticker} price: {result.price}")
                
                return {
                    "status": "success",
                    "ticker": ticker,
                    "price": result.price,
                    "timestamp": result.timestamp.isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error in fetch_and_save_price for {ticker}: {str(e)}")
                await session.rollback()
                raise e
            finally:
                if client:
                    await client.close()
    
    # Run async task in sync context
    loop = None
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_async_task())
        return result
        
    except Exception as exc:
        logger.error(f"Task failed for {ticker}: {str(exc)}")
        # Retry the task with exponential backoff
        retry_in = 60 * (2 ** self.request.retries)  # 60, 120, 240 seconds
        self.retry(exc=exc, countdown=retry_in)
        
    finally:
        if loop:
            loop.close()

@shared_task(
    name="app.worker.tasks.cleanup_old_records",
    bind=True,
    max_retries=2,
    soft_time_limit=300  # 5 minutes
)
def cleanup_old_records(self, days: int = 30):
    """
    Celery task to clean up old records
    """
    logger.info(f"Starting cleanup of records older than {days} days")
    
    async def _async_task():
        async with AsyncSessionLocal() as session:
            try:
                repository = SQLAlchemyPriceRepository(session)
                deleted_count = await repository.delete_old_records(days)
                
                logger.info(f"Cleaned up {deleted_count} old records")
                return {
                    "status": "success", 
                    "deleted_count": deleted_count,
                    "days": days
                }
                
            except Exception as e:
                logger.error(f"Error in cleanup: {e}")
                await session.rollback()
                raise e
    
    loop = None
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_async_task())
        return result
        
    except Exception as exc:
        logger.error(f"Cleanup task failed: {str(exc)}")
        self.retry(exc=exc, countdown=300)  # Retry in 5 minutes
        
    finally:
        if loop:
            loop.close()

@shared_task(name="app.worker.tasks.fetch_multiple_prices")
def fetch_multiple_prices():
    """
    Fetch prices for all supported currencies
    """
    currencies = ["btc_usd", "eth_usd"]
    results = {}
    
    for currency in currencies:
        try:
            result = fetch_and_save_price.delay(currency)
            results[currency] = result.id
        except Exception as e:
            logger.error(f"Failed to schedule task for {currency}: {e}")
            results[currency] = None
    
    return results