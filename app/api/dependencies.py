from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.db.session import Database
from app.repositories.price_repository import PriceRepository
from app.services.price_query_service import PriceQueryService


def get_session(request: Request) -> Iterator[Session]:
    database: Database = request.app.state.database
    with database.session() as session:
        yield session


def get_price_query_service(
    session: Annotated[Session, Depends(get_session)],
) -> PriceQueryService:
    return PriceQueryService(PriceRepository(session))


PriceQueryServiceDep = Annotated[PriceQueryService, Depends(get_price_query_service)]