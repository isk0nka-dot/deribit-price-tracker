from app.config import Settings
from app.db.session import Database
from app.tasks.celery_app import create_celery_app

settings = Settings()
celery_app = create_celery_app(settings, Database(settings.database_url))