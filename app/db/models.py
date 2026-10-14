from decimal import Decimal

from sqlalchemy import BigInteger, Index, Numeric, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Price(Base):
    __tablename__ = "prices"
    __table_args__ = (Index("ix_prices_ticker_timestamp", "ticker", "timestamp"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(16))
    price: Mapped[Decimal] = mapped_column(Numeric(18, 8))
    timestamp: Mapped[int] = mapped_column(BigInteger)