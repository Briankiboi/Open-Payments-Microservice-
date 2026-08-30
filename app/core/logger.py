import logging
import sys
from typing import Any

import structlog
from asgi_correlation_id import correlation_id


def configure_logging() -> None:
    """Configure structured JSON logging across the application."""

    def add_correlation_id(
        logger: Any, method_name: str, event_dict: dict[str, Any]
    ) -> dict[str, Any]:
        """Add the correlation ID to every log entry representing an HTTP request footprint."""
        request_id = correlation_id.get()
        if request_id:
            event_dict["request_id"] = request_id
        return event_dict

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            add_correlation_id,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    log_level = logging.INFO
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    # Force Uvicorn and other noisy loggers to use structlog formatting
    for _log in ["uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"]:
        logger_obj = logging.getLogger(_log)
        logger_obj.handlers.clear()
        logger_obj.propagate = True
