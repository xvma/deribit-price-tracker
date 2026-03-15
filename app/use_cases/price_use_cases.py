from datetime import datetime, timedelta
from typing import List, Optional
import logging
from ..domain.entities import PriceData, PriceStats
from ..domain.interfaces import PriceRepository, DeribitClient

logger = logging.getLogger(__name__)

class FetchAndSavePriceUseCase:
    """Use case for fetching current price and saving to database"""
    
    def __init__(self, repository: PriceRepository, deribit_client: DeribitClient):
        self._repository = repository
        self._deribit_client = deribit_client
    
    async def execute(self, ticker: str) -> PriceData:
        """Fetch current price from Deribit and save to database"""
        try:
            logger.info(f"Fetching price for {ticker}")
            
            # Fetch price from Deribit
            price = await self._deribit_client.get_index_price(ticker)
            
            # Create price data entity
            price_data = PriceData(
                ticker=ticker,
                price=price,
                timestamp=datetime.utcnow()
            )
            
            # Save to repository
            await self._repository.save(price_data)
            
            logger.info(f"Successfully saved {ticker} price: {price}")
            return price_data
            
        except Exception as e:
            logger.error(f"Failed to fetch and save price for {ticker}: {e}")
            raise

class GetAllPricesUseCase:
    """Use case for getting all prices for a ticker"""
    
    def __init__(self, repository: PriceRepository):
        self._repository = repository
    
    async def execute(self, ticker: str) -> List[PriceData]:
        """Get all saved prices for ticker"""
        try:
            logger.debug(f"Getting all prices for {ticker}")
            prices = await self._repository.get_by_ticker(ticker)
            logger.debug(f"Found {len(prices)} prices for {ticker}")
            return prices
        except Exception as e:
            logger.error(f"Failed to get all prices for {ticker}: {e}")
            raise

class GetLatestPriceUseCase:
    """Use case for getting latest price for a ticker"""
    
    def __init__(self, repository: PriceRepository):
        self._repository = repository
    
    async def execute(self, ticker: str) -> Optional[PriceData]:
        """Get latest price for ticker"""
        try:
            logger.debug(f"Getting latest price for {ticker}")
            price = await self._repository.get_latest_by_ticker(ticker)
            if price:
                logger.debug(f"Found latest price for {ticker}: {price.price}")
            else:
                logger.debug(f"No prices found for {ticker}")
            return price
        except Exception as e:
            logger.error(f"Failed to get latest price for {ticker}: {e}")
            raise

class GetPricesByDateUseCase:
    """Use case for getting prices by date range"""
    
    def __init__(self, repository: PriceRepository):
        self._repository = repository
    
    async def execute(
        self, 
        ticker: str, 
        start_date: datetime, 
        end_date: Optional[datetime] = None
    ) -> List[PriceData]:
        """Get prices for ticker within date range"""
        try:
            if end_date is None:
                end_date = datetime.utcnow()
            
            logger.debug(f"Getting prices for {ticker} from {start_date} to {end_date}")
            prices = await self._repository.get_by_ticker_and_date_range(
                ticker, start_date, end_date
            )
            logger.debug(f"Found {len(prices)} prices for {ticker} in date range")
            return prices
        except Exception as e:
            logger.error(f"Failed to get prices by date for {ticker}: {e}")
            raise

class GetPriceStatsUseCase:
    """Use case for getting price statistics"""
    
    def __init__(self, repository: PriceRepository):
        self._repository = repository
    
    async def execute(self, ticker: str, days: int = 7) -> Optional[PriceStats]:
        """Get price statistics for last N days"""
        try:
            logger.debug(f"Getting statistics for {ticker} over last {days} days")
            
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Get prices in range
            prices = await self._repository.get_by_ticker_and_date_range(
                ticker, start_date, end_date
            )
            
            if not prices:
                logger.debug(f"No data found for {ticker} in last {days} days")
                return None
            
            # Calculate statistics
            price_values = [p.price for p in prices]
            first_price = prices[-1].price  # Oldest
            last_price = prices[0].price     # Newest
            
            stats = PriceStats(
                ticker=ticker,
                period_days=days,
                count=len(prices),
                min_price=min(price_values),
                max_price=max(price_values),
                avg_price=sum(price_values) / len(price_values),
                first_price=first_price,
                last_price=last_price,
                change=last_price - first_price,
                change_percent=((last_price - first_price) / first_price) * 100 if first_price else 0
            )
            
            logger.debug(f"Statistics calculated for {ticker}: {stats.to_dict()}")
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get statistics for {ticker}: {e}")
            raise