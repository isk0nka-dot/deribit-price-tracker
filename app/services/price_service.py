import asyncio
import time
from collections.abc import Callable, Sequence

from app.clients.deribit import DeribitClient
from app.db.models import Price
from app.repositories.price_repository import PriceRepository


class PriceCollectionService:
    def __init__(
        self,
        client: DeribitClient,
        repository: PriceRepository,
        tickers: Sequence[str],
        clock: Callable[[], float] = time.time,
    ) -> None:
        self._client = client
        self._repository = repository
        self._tickers = tuple(tickers)
        self._clock = clock

    async def collect(self) -> list[Price]:
        index_prices = await asyncio.gather(
            *(self._client.get_index_price(ticker) for ticker in self._tickers)
        )
        timestamp = int(self._clock())
        prices = [
            Price(ticker=ticker, price=index_price, timestamp=timestamp)
            for ticker, index_price in zip(self._tickers, index_prices, strict=True)
        ]
        self._repository.add_many(prices)
        return prices