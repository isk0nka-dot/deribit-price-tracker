from decimal import Decimal

from app.db.models import Price


def make_price(
    ticker: str = "btc_usd",
    price: str = "67000.12",
    timestamp: int = 1_700_000_000,
) -> Price:
    return Price(ticker=ticker, price=Decimal(price), timestamp=timestamp)