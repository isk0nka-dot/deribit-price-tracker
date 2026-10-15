from celery import Celery
from app.tickers import Ticker
from app.config import Settings
from app.db.session import Database
from app.tasks.fetch_prices import (
    FETCH_PRICES_TASK_NAME,
    PriceFetcher,
    register_fetch_prices_task,
)

TICKERS = tuple(ticker.value for ticker in Ticker)
FETCH_INTERVAL_SECONDS = 60.0


def create_celery_app(settings: Settings, database: Database) -> Celery:
    celery_app = Celery(
        "deribit_price_tracker",
        broker=settings.redis_url,
    )
    celery_app.conf.update(
        timezone="UTC",
        enable_utc=True,
        task_ignore_result=True,
        broker_connection_retry_on_startup=True,
        beat_schedule={
            "fetch-prices-every-minute": {
                "task": FETCH_PRICES_TASK_NAME,
                "schedule": FETCH_INTERVAL_SECONDS,
            },
        },
    )
    fetcher = PriceFetcher(settings, database, TICKERS)
    register_fetch_prices_task(celery_app, fetcher)
    return celery_app