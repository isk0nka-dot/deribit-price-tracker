import asyncio
from decimal import Decimal
from typing import Any

import aiohttp
import pytest
from aioresponses import aioresponses

from app.clients.deribit import DeribitClient, DeribitClientError

BASE_URL = "https://deribit.test/api/v2"
INDEX_PRICE_URL = f"{BASE_URL}/public/get_index_price?index_name=btc_usd"


async def fetch_price(base_url: str = BASE_URL) -> Decimal:
    async with aiohttp.ClientSession() as session:
        client = DeribitClient(base_url, session)
        return await client.get_index_price("btc_usd")


def test_get_index_price_returns_decimal() -> None:
    with aioresponses() as mocked:
        mocked.get(INDEX_PRICE_URL, payload={"result": {"index_price": 67000.12}})
        price = asyncio.run(fetch_price())

    assert price == Decimal("67000.12")


def test_trailing_slash_in_base_url_is_ignored() -> None:
    with aioresponses() as mocked:
        mocked.get(INDEX_PRICE_URL, payload={"result": {"index_price": 1.5}})
        price = asyncio.run(fetch_price(f"{BASE_URL}/"))

    assert price == Decimal("1.5")


@pytest.mark.parametrize(
    "mock_kwargs",
    [
        {"status": 500},
        {"exception": aiohttp.ClientConnectionError("connection lost")},
        {"exception": asyncio.TimeoutError()},
        {"payload": {"error": {"code": 10000}}},
        {"payload": {"result": {"index_price": "not-a-number"}}},
    ],
    ids=["http-error", "connection-error", "timeout", "error-payload", "invalid-price"],
)
def test_get_index_price_raises_client_error(mock_kwargs: dict[str, Any]) -> None:
    with aioresponses() as mocked:
        mocked.get(INDEX_PRICE_URL, **mock_kwargs)
        with pytest.raises(DeribitClientError):
            asyncio.run(fetch_price())