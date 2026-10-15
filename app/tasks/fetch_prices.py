import asyncio
from collections.abc import Sequence

import aiohttp
from celery import Celery

from app.clients.deribit import DeribitClient
from app.config import Settings
from app.db.session import Database
from app.repositories.price_repository import PriceRepository
from app.services.price_collection_service import PriceCollectionService

FETCH_PRICES_TASK_NAME = "prices.fetch"
REQUEST_TIMEOUT_SECONDS = 10


class PriceFetcher:
    def __init__(
        self,
        settings: Settings,
        database: Database,
        tickers: Sequence[str],
    ) -> None:
        self._settings = settings
        self._database = database
        self._tickers = tuple(tickers)

    def run(self) -> int:
        return asyncio.run(self._collect())

    async def _collect(self) -> int:
        timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT_SECONDS)
        async with aiohttp.ClientSession(timeout=timeout) as http_session:
            client = DeribitClient(self._settings.deribit_base_url, http_session)
            with self._database.session() as db_session:
                service = PriceCollectionService(
                    client, PriceRepository(db_session), self._tickers
                )
                prices = await service.collect()
        return len(prices)


def register_fetch_prices_task(celery_app: Celery, fetcher: PriceFetcher) -> None:
    @celery_app.task(name=FETCH_PRICES_TASK_NAME)
    def fetch_prices() -> int:
        return fetcher.run()
