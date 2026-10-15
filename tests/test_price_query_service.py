import pytest

from app.repositories.price_repository import PriceRepository
from app.services.price_query_service import (
    InvalidPeriodError,
    PriceNotFoundError,
    PriceQueryService,
)
from app.tickers import Ticker
from tests.factories import make_price


@pytest.fixture
def service(repository: PriceRepository) -> PriceQueryService:
    return PriceQueryService(repository)


def test_get_all_returns_prices_of_ticker(
    service: PriceQueryService, repository: PriceRepository
) -> None:
    repository.add_many(
        [make_price("btc_usd", timestamp=100), make_price("eth_usd", timestamp=100)]
    )

    prices = service.get_all(Ticker.BTC_USD)

    assert [p.ticker for p in prices] == ["btc_usd"]


def test_get_latest_returns_most_recent_price(
    service: PriceQueryService, repository: PriceRepository
) -> None:
    repository.add_many(
        [make_price(timestamp=100), make_price(timestamp=200), make_price(timestamp=150)]
    )

    assert service.get_latest(Ticker.BTC_USD).timestamp == 200


def test_get_latest_raises_when_no_prices_stored(service: PriceQueryService) -> None:
    with pytest.raises(PriceNotFoundError):
        service.get_latest(Ticker.BTC_USD)


def test_get_by_period_rejects_start_later_than_end(
    service: PriceQueryService,
) -> None:
    with pytest.raises(InvalidPeriodError):
        service.get_by_period(Ticker.BTC_USD, 200, 100)


def test_get_by_period_accepts_equal_bounds(
    service: PriceQueryService, repository: PriceRepository
) -> None:
    repository.add_many([make_price(timestamp=100), make_price(timestamp=200)])

    prices = service.get_by_period(Ticker.BTC_USD, 100, 100)

    assert [p.timestamp for p in prices] == [100]
    