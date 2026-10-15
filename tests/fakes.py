from collections.abc import Mapping, Sequence
from decimal import Decimal

from app.clients.deribit import DeribitClientError
from app.db.models import Price


class FakeDeribitClient:
    def __init__(self, prices: Mapping[str, Decimal]) -> None:
        self._prices = prices

    async def get_index_price(self, ticker: str) -> Decimal:
        try:
            return self._prices[ticker]
        except KeyError as exc:
            raise DeribitClientError(f"No price for {ticker}") from exc


class FakePriceRepository:
    def __init__(self) -> None:
        self.saved: list[Price] = []

    def add_many(self, prices: Sequence[Price]) -> None:
        self.saved.extend(prices)