import asyncio
from decimal import Decimal, InvalidOperation

import aiohttp


class DeribitClientError(Exception):
    """Raised when Deribit is unreachable or returns an unexpected response."""


class DeribitClient:
    def __init__(self, base_url: str, session: aiohttp.ClientSession) -> None:
        self._base_url = base_url.rstrip("/")
        self._session = session

    async def get_index_price(self, ticker: str) -> Decimal:
        url = f"{self._base_url}/public/get_index_price"
        try:
            async with self._session.get(url, params={"index_name": ticker}) as response:
                response.raise_for_status()
                payload = await response.json()
        except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
            raise DeribitClientError(f"Request for {ticker} failed: {exc!r}") from exc

        try:
            return Decimal(str(payload["result"]["index_price"]))
        except (KeyError, TypeError, InvalidOperation) as exc:
            raise DeribitClientError(f"Unexpected response for {ticker}: {payload}") from exc