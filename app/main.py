from fastapi import FastAPI

from app.api.routers import router
from app.config import Settings
from app.db.session import Database


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    app = FastAPI(title="Deribit Price Tracker")
    app.state.database = Database(settings.database_url)
    app.include_router(router)
    return app  