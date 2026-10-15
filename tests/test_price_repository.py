import pytest

from app.repositories.price_repository import PriceRepository
from tests.factories import make_price


@pytest.fixture
def seeded_repository(repository: PriceRepository) -> PriceRepository:
    repository.add_many(
        [
            make_price("btc_usd", "1", 100),
            make_price("btc_usd", "3", 300),
            make_price("btc_usd", "2", 200),
            make_price("eth_usd", "9", 200),
        ]
    )
    return repository


def test_get_all_returns_only_requested_ticker_ordered_by_time(
    seeded_repository: PriceRepository,
) -> None:
    prices = seeded_repository.get_all("btc_usd")

    assert [p.timestamp for p in prices] == [100, 200, 300]
    assert {p.ticker for p in prices} == {"btc_usd"}


def test_get_all_returns_empty_list_for_ticker_without_data(
    repository: PriceRepository,
) -> None:
    assert repository.get_all("btc_usd") == []


def test_get_latest_returns_most_recent_price_of_ticker(
    seeded_repository: PriceRepository,
) -> None:
    latest = seeded_repository.get_latest("btc_usd")

    assert latest is not None
    assert latest.timestamp == 300


def test_get_latest_returns_none_without_data(repository: PriceRepository) -> None:
    assert repository.get_latest("btc_usd") is None


@pytest.mark.parametrize(
    ("timestamp_from", "timestamp_to", "expected"),
    [
        (None, None, [100, 200, 300]),
        (200, None, [200, 300]),
        (None, 200, [100, 200]),
        (200, 200, [200]),
        (101, 199, []),
    ],
)
def test_get_by_period_filters_with_inclusive_bounds(
    seeded_repository: PriceRepository,
    timestamp_from: int | None,
    timestamp_to: int | None,
    expected: list[int],
) -> None:
    prices = seeded_repository.get_by_period("btc_usd", timestamp_from, timestamp_to)

    assert [p.timestamp for p in prices] == expected