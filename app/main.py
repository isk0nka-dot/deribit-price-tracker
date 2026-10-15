from fastapi import FastAPI

from app.api.routers import router
from app.config import Settings
from app.db.session import Database


def create_app(
    settings: Settings | None = None,
    database: Database | None = None,
) -> FastAPI:
    if database is None:
        database = Database((settings or Settings()).database_url)
    app = FastAPI(title="Deribit Price Tracker")
    app.state.database = database
    app.include_router(router)
    return app