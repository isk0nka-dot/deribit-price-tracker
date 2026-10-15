from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.models import Base
from app.db.session import Database
from app.main import create_app
from app.repositories.price_repository import PriceRepository


@pytest.fixture
def database(tmp_path: Path) -> Database:
    url = f"sqlite:///{(tmp_path / 'test.db').as_posix()}"
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    engine.dispose()
    return Database(url)


@pytest.fixture
def session(database: Database) -> Iterator[Session]:
    with database.session() as db_session:
        yield db_session


@pytest.fixture
def repository(session: Session) -> PriceRepository:
    return PriceRepository(session)


@pytest.fixture
def client(database: Database) -> TestClient:
    return TestClient(create_app(database=database))