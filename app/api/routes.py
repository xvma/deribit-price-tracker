from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, date
from typing import List, Optional
import logging
from ..core.database import get_db
from ..infrastructure.repository import SQLAlchemyPriceRepository
from ..use_cases.price_use_cases import (
    GetAllPricesUseCase,
    GetLatestPriceUseCase,
    GetPricesByDateUseCase,
    GetPriceStatsUseCase
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Valid tickers
VALID_TICKERS = {"btc_usd", "eth_usd"}

async def get_price_repository(
    db: AsyncSession = Depends(get_db)
) -> SQLAlchemyPriceRepository:
    """Dependency for getting price repository"""
    return SQLAlchemyPriceRepository(db)

def validate_ticker(ticker: str) -> str:
    """Validate ticker parameter"""
    ticker_lower = ticker.lower()
    if ticker_lower not in VALID_TICKERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid ticker. Must be one of: {', '.join(VALID_TICKERS)}"
        )
    return ticker_lower

@router.get(
    "/prices",
    response_model=List[dict],
    summary="Get all prices for ticker",
    description="Returns all saved prices for the specified ticker"
)
async def get_all_prices(
    ticker: str = Query(
        ...,
        description="Currency ticker (btc_usd or eth_usd)",
        example="btc_usd"
    ),
    limit: int = Query(
        1000,
        ge=1,
        le=10000,
        description="Maximum number of records to return"
    ),
    repo: SQLAlchemyPriceRepository = Depends(get_price_repository)
):
    """Get all saved prices for specified ticker"""
    try:
        valid_ticker = validate_ticker(ticker)
        use_case = GetAllPricesUseCase(repo)
        prices = await use_case.execute(valid_ticker)
        
        # Apply limit
        if limit and len(prices) > limit:
            prices = prices[:limit]
        
        logger.info(f"Retrieved {len(prices)} prices for {valid_ticker}")
        return [p.to_dict() for p in prices]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_all_prices: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get(
    "/prices/latest",
    response_model=dict,
    summary="Get latest price",
    description="Returns the most recent price for the specified ticker"
)
async def get_latest_price(
    ticker: str = Query(
        ...,
        description="Currency ticker (btc_usd or eth_usd)",
        example="btc_usd"
    ),
    repo: SQLAlchemyPriceRepository = Depends(get_price_repository)
):
    """Get latest price for specified ticker"""
    try:
        valid_ticker = validate_ticker(ticker)
        use_case = GetLatestPriceUseCase(repo)
        price = await use_case.execute(valid_ticker)
        
        if not price:
            logger.warning(f"No prices found for ticker {valid_ticker}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No prices found for ticker {valid_ticker}"
            )
        
        logger.info(f"Retrieved latest price for {valid_ticker}: {price.price}")
        return price.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_latest_price: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get(
    "/prices/by-date",
    response_model=List[dict],
    summary="Get prices by date",
    description="Returns all prices for the specified ticker on a given date"
)
async def get_prices_by_date(
    ticker: str = Query(
        ...,
        description="Currency ticker (btc_usd or eth_usd)",
        example="btc_usd"
    ),
    date: date = Query(
        ...,
        description="Date in YYYY-MM-DD format",
        example="2024-01-01"
    ),
    repo: SQLAlchemyPriceRepository = Depends(get_price_repository)
):
    """Get prices for specified ticker on a specific date"""
    try:
        valid_ticker = validate_ticker(ticker)
        
        # Create datetime range for the specified date
        start_date = datetime.combine(date, datetime.min.time())
        end_date = datetime.combine(date, datetime.max.time())
        
        use_case = GetPricesByDateUseCase(repo)
        prices = await use_case.execute(valid_ticker, start_date, end_date)
        
        logger.info(f"Retrieved {len(prices)} prices for {valid_ticker} on {date}")
        return [p.to_dict() for p in prices]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_prices_by_date: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get(
    "/prices/history",
    response_model=List[dict],
    summary="Get price history with pagination",
    description="Returns paginated price history for the specified ticker"
)
async def get_price_history(
    ticker: str = Query(
        ...,
        description="Currency ticker (btc_usd or eth_usd)",
        example="btc_usd"
    ),
    limit: int = Query(
        100,
        ge=1,
        le=1000,
        description="Number of records to return"
    ),
    offset: int = Query(
        0,
        ge=0,
        description="Number of records to skip"
    ),
    repo: SQLAlchemyPriceRepository = Depends(get_price_repository)
):
    """Get paginated price history for specified ticker"""
    try:
        valid_ticker = validate_ticker(ticker)
        prices = await repo.get_price_history(valid_ticker, limit, offset)
        
        logger.info(f"Retrieved {len(prices)} prices for {valid_ticker} (offset={offset}, limit={limit})")
        return [p.to_dict() for p in prices]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_price_history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get(
    "/prices/stats",
    response_model=dict,
    summary="Get price statistics",
    description="Returns price statistics for the specified ticker over a period"
)
async def get_price_stats(
    ticker: str = Query(
        ...,
        description="Currency ticker (btc_usd or eth_usd)",
        example="btc_usd"
    ),
    days: int = Query(
        7,
        ge=1,
        le=90,
        description="Number of days for statistics"
    ),
    repo: SQLAlchemyPriceRepository = Depends(get_price_repository)
):
    """Get price statistics for specified ticker"""
    try:
        valid_ticker = validate_ticker(ticker)
        use_case = GetPriceStatsUseCase(repo)
        stats = await use_case.execute(valid_ticker, days)
        
        if not stats:
            logger.warning(f"No data found for {valid_ticker} in last {days} days")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No data found for ticker {valid_ticker} in the last {days} days"
            )
        
        logger.info(f"Retrieved statistics for {valid_ticker} over {days} days")
        return stats.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_price_stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )