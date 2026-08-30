import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

import structlog
from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.payments import router as payments_router
from app.core.config import settings
from app.core.database import engine
from app.core.logger import configure_logging
from app.core.rate_limiter import limiter
from app.webhooks.payment_webhook import router as webhooks_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[Any, None]:
    # Database tables are now managed by Alembic migrations
    configure_logging()
    logger = structlog.get_logger()
    logger.info("Application starting up...")
    yield
    # Cleanup on shutdown
    await engine.dispose()
    logger.info("Database connection closed")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="A modular payment microservice handling transactions and webhooks.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add Middlewares
app.add_middleware(CorrelationIdMiddleware)

# Add Rate Limiter Exception Handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Instrument Prometheus Metrics
Instrumentator().instrument(app).expose(app, tags=["Metrics"])

# Include Routers
app.include_router(payments_router)
app.include_router(webhooks_router)


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok", "app": settings.PROJECT_NAME}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
