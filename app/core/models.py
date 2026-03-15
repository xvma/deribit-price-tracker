from sqlalchemy import Column, Integer, String, Float, DateTime, Index
from sqlalchemy.sql import func
from .database import Base

class PriceRecord(Base):
    __tablename__ = "price_records"

    # Исправлено: primary_key, а не primary_key_key
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(20), nullable=False, index=True)
    price = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False, server_default=func.now())
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Составной индекс для оптимизации запросов
    __table_args__ = (
        Index('idx_ticker_timestamp', 'ticker', 'timestamp'),
        Index('idx_ticker', 'ticker'),
    )

    def __repr__(self) -> str:
        return f"<PriceRecord(ticker='{self.ticker}', price={self.price}, timestamp={self.timestamp})>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "ticker": self.ticker,
            "price": self.price,
            "timestamp": int(self.timestamp.timestamp()),
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
