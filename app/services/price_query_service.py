from app.db.models import Price
from app.repositories.price_repository import PriceRepository
from app.tickers import Ticker


class PriceNotFoundError(Exception):
    """Raised when no prices are stored for the requested ticker."""


class InvalidPeriodError(ValueError):
    """Raised when the start of the requested period is later than its end."""


class PriceQueryService:
    def __init__(self, repository: PriceRepository) -> None:
        self._repository = repository

    def get_all(self, ticker: Ticker) -> list[Price]:
        return self._repository.get_all(ticker.value)

    def get_latest(self, ticker: Ticker) -> Price:
        price = self._repository.get_latest(ticker.value)
        if price is None:
            raise PriceNotFoundError(f"No prices stored for {ticker.value}")
        return price

    def get_by_period(
        self,
        ticker: Ticker,
        timestamp_from: int | None,
        timestamp_to: int | None,
    ) -> list[Price]:
        if (
            timestamp_from is not None
            and timestamp_to is not None
            and timestamp_from > timestamp_to
        ):
            raise InvalidPeriodError("Period start must not be later than period end")
        return self._repository.get_by_period(
            ticker.value, timestamp_from, timestamp_to
        )