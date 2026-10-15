from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.api.dependencies import PriceQueryServiceDep
from app.api.schemas import PriceResponse
from app.db.models import Price
from app.services.price_query_service import InvalidPeriodError, PriceNotFoundError
from app.tickers import Ticker

router = APIRouter(prefix="/prices", tags=["prices"])

TickerQuery = Annotated[Ticker, Query(description="Currency ticker")]
TimestampQuery = Annotated[
    int | None, Query(ge=0, description="UNIX timestamp, inclusive")
]


@router.get("", response_model=list[PriceResponse])
def get_all_prices(ticker: TickerQuery, service: PriceQueryServiceDep) -> list[Price]:
    return service.get_all(ticker)


@router.get("/latest", response_model=PriceResponse)
def get_latest_price(ticker: TickerQuery, service: PriceQueryServiceDep) -> Price:
    try:
        return service.get_latest(ticker)
    except PriceNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/by-date", response_model=list[PriceResponse])
def get_prices_by_date(
    ticker: TickerQuery,
    service: PriceQueryServiceDep,
    date_from: TimestampQuery = None,
    date_to: TimestampQuery = None,
) -> list[Price]:
    try:
        return service.get_by_period(ticker, date_from, date_to)
    except InvalidPeriodError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc