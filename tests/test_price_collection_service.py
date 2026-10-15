import asyncio
from decimal import Decimal

import pytest

from app.clients.deribit import DeribitClientError
from app.services.price_service import PriceCollectionService
from tests.fakes import FakeDeribitClient, FakePriceRepository

FIXED_TIME = 1_700_000_000.9


def build_service(
    client: FakeDeribitClient, repository: FakePriceRepository
) -> PriceCollectionService:
    return PriceCollectionService(
        client,
        repository,
        tickers=("btc_usd", "eth_usd"),
        clock=lambda: FIXED_TIME,
    )


def test_collect_saves_price_for_every_ticker() -> None:
    client = FakeDeribitClient(
        {"btc_usd": Decimal("67000.12"), "eth_usd": Decimal("2500.5")}
    )
    repository = FakePriceRepository()

    prices = asyncio.run(build_service(client, repository).collect())

    assert [(p.ticker, p.price, p.timestamp) for p in prices] == [
        ("btc_usd", Decimal("67000.12"), 1_700_000_000),
        ("eth_usd", Decimal("2500.5"), 1_700_000_000),
    ]
    assert repository.saved == prices


def test_collect_saves_nothing_when_any_ticker_fails() -> None:
    client = FakeDeribitClient({"btc_usd": Decimal("67000.12")})
    repository = FakePriceRepository()

    with pytest.raises(DeribitClientError):
        asyncio.run(build_service(client, repository).collect())

    assert repository.saved == []