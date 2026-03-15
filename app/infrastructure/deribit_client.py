import aiohttp
import asyncio
from typing import Dict, Any, Optional
import logging
from ..domain.interfaces import DeribitClient
from ..core.config import settings

logger = logging.getLogger(__name__)

class DeribitAPIClient(DeribitClient):
    """Async client for Deribit API"""
    
    def __init__(self):
        self._base_url = settings.DERIBIT_API_URL
        self._session: Optional[aiohttp.ClientSession] = None
        self._timeout = aiohttp.ClientTimeout(total=10)
        
        # Currency mapping
        self._currency_map = {
            "btc_usd": "btc",
            "eth_usd": "eth"
        }
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=self._timeout,
                headers={"User-Agent": "DeribitPriceTracker/1.0"}
            )
        return self._session
    
    async def get_index_price(self, currency: str) -> float:
        """Get current index price for currency from Deribit"""
        try:
            session = await self._get_session()
            
            # Validate and map currency
            currency_lower = currency.lower()
            if currency_lower not in self._currency_map:
                raise ValueError(f"Unsupported currency: {currency}. Supported: {list(self._currency_map.keys())}")
            
            deribit_currency = self._currency_map[currency_lower]
            
            # Prepare request
            url = f"{self._base_url}/public/get_index_price"
            params = {"index_name": f"{deribit_currency}_usd"}
            
            logger.debug(f"Fetching price for {currency} from Deribit")
            
            # Make request
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Deribit API HTTP error {response.status}: {error_text}")
                
                data = await response.json()
                
                # Check for API error
                if data.get("error"):
                    error_msg = data["error"].get("message", "Unknown error")
                    raise Exception(f"Deribit API error: {error_msg}")
                
                # Extract price
                if "result" not in data or "index_price" not in data["result"]:
                    raise Exception(f"Unexpected API response format: {data}")
                
                price = float(data["result"]["index_price"])
                logger.info(f"Successfully fetched {currency} price: {price}")
                
                return price
                
        except asyncio.TimeoutError:
            logger.error(f"Timeout while fetching {currency} price")
            raise Exception(f"Timeout while fetching {currency} price")
        except aiohttp.ClientError as e:
            logger.error(f"HTTP client error while fetching {currency} price: {e}")
            raise Exception(f"Network error while fetching {currency} price: {e}")
        except ValueError as e:
            logger.error(f"Value error while fetching {currency} price: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while fetching {currency} price: {e}")
            raise
    
    async def get_multiple_prices(self, currencies: list) -> Dict[str, float]:
        """Get prices for multiple currencies concurrently"""
        tasks = [self.get_index_price(currency) for currency in currencies]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        prices = {}
        for currency, result in zip(currencies, results):
            if isinstance(result, Exception):
                logger.error(f"Failed to fetch {currency}: {result}")
                prices[currency] = None
            else:
                prices[currency] = result
        
        return prices
    
    async def close(self) -> None:
        """Close the aiohttp session"""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.debug("Deribit API client session closed")
    
    async def __aenter__(self):
        """Context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self.close()