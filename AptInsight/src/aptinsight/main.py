from fastapi import FastAPI

from aptinsight.api.chat import router as chat_router
from aptinsight.api.health import router as health_router
from aptinsight.core.config import settings
from aptinsight.core.logging import setup_logging


def create_app() -> FastAPI:
    setup_logging(settings.log_level)
    app = FastAPI(title=settings.app_name)
    app.include_router(health_router)
    app.include_router(chat_router, prefix="/api")
    return app


app = create_app()

