from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Price


class PriceRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add_many(self, prices: Sequence[Price]) -> None:
        self._session.add_all(prices)

    def get_all(self, ticker: str) -> list[Price]:
        statement = (
            select(Price)
            .where(Price.ticker == ticker)
            .order_by(Price.timestamp)
        )
        return list(self._session.scalars(statement))

    def get_latest(self, ticker: str) -> Price | None:
        statement = (
            select(Price)
            .where(Price.ticker == ticker)
            .order_by(Price.timestamp.desc())
            .limit(1)
        )
        return self._session.scalars(statement).first()

    def get_by_period(
        self,
        ticker: str,
        timestamp_from: int | None,
        timestamp_to: int | None,
    ) -> list[Price]:
        statement = select(Price).where(Price.ticker == ticker)
        if timestamp_from is not None:
            statement = statement.where(Price.timestamp >= timestamp_from)
        if timestamp_to is not None:
            statement = statement.where(Price.timestamp <= timestamp_to)
        statement = statement.order_by(Price.timestamp)
        return list(self._session.scalars(statement))