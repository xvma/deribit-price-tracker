from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Protocol
from .entities import PriceData, PriceStats

class PriceRepository(ABC):
    """Abstract interface for price repository"""
    
    @abstractmethod
    async def save(self, price_data: PriceData) -> None:
        """Save price data to repository"""
        pass
    
    @abstractmethod
    async def get_by_ticker(self, ticker: str) -> List[PriceData]:
        """Get all prices for ticker"""
        pass
    
    @abstractmethod
    async def get_latest_by_ticker(self, ticker: str) -> Optional[PriceData]:
        """Get latest price for ticker"""
        pass
    
    @abstractmethod
    async def get_by_ticker_and_date_range(
        self, 
        ticker: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[PriceData]:
        """Get prices for ticker within date range"""
        pass
    
    @abstractmethod
    async def get_price_history(
        self, 
        ticker: str, 
        limit: int = 100,
        offset: int = 0
    ) -> List[PriceData]:
        """Get paginated price history"""
        pass
    
    @abstractmethod
    async def delete_old_records(self, days: int = 30) -> int:
        """Delete records older than specified days"""
        pass

class DeribitClient(ABC):
    """Abstract interface for Deribit API client"""
    
    @abstractmethod
    async def get_index_price(self, currency: str) -> float:
        """Get current index price for currency"""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Close client session"""
        pass

class UseCase(Protocol):
    """Protocol for use cases"""
    async def execute(self, *args, **kwargs):
        """Execute use case"""
        pass