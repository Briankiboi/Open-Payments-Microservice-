from arq.connections import RedisSettings
from typing import Any

from app.core.config import settings
from app.services.tasks import process_payment_async


async def startup(ctx: Any) -> None:
    """
    Called when the ARQ worker starts.
    Good place to setup DB connection pools if they aren't created lazily.
    """
    print("ARQ Worker starting up...")


async def shutdown(ctx: Any) -> None:
    print("ARQ Worker shutting down...")


class WorkerSettings:
    """
    Configuration for the ARQ worker.
    Start via: `arq app.worker.WorkerSettings`
    """

    functions = [process_payment_async]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    on_startup = startup
    on_shutdown = shutdown
    max_jobs = 10
    max_tries = 3
