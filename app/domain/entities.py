from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class PriceData:
    ticker: str
    price: float
    timestamp: datetime
    id: Optional[int] = None
    
    def __post_init__(self):
        if self.price <= 0:
            raise ValueError("Price must be positive")
        if not self.ticker or not isinstance(self.ticker, str):
            raise ValueError("Ticker must be non-empty string")
    
    def to_dict(self) -> dict:
        return {
            "ticker": self.ticker,
            "price": self.price,
            "timestamp": int(self.timestamp.timestamp()),
            "id": self.id
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PriceData':
        return cls(
            ticker=data["ticker"],
            price=data["price"],
            timestamp=datetime.fromtimestamp(data["timestamp"]),
            id=data.get("id")
        )

@dataclass
class PriceStats:
    ticker: str
    period_days: int
    count: int
    min_price: float
    max_price: float
    avg_price: float
    first_price: float
    last_price: float
    change: float
    change_percent: float
    
    def to_dict(self) -> dict:
        return {
            "ticker": self.ticker,
            "period_days": self.period_days,
            "count": self.count,
            "min_price": round(self.min_price, 2),
            "max_price": round(self.max_price, 2),
            "avg_price": round(self.avg_price, 2),
            "first_price": round(self.first_price, 2),
            "last_price": round(self.last_price, 2),
            "change": round(self.change, 2),
            "change_percent": round(self.change_percent, 2)
        }