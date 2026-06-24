"""
Recommender service entry point.

v0.1.0: connects to RabbitMQ, logs success, then blocks.
Training and recommendation consumers are registered in v0.5.0 and v0.6.0.
"""
import logging
import signal
import threading

import structlog

from app.messaging.connection import connect_with_retry
from app.settings import settings


def _configure_logging() -> None:
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    renderer = structlog.processors.JSONRenderer() if settings.log_json else structlog.dev.ConsoleRenderer()
    structlog.configure(
        processors=shared_processors + [renderer],
        wrapper_class=structlog.BoundLogger,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
    )


def main() -> None:
    _configure_logging()
    logger = structlog.get_logger()

    logger.info(
        "Recommender service starting",
        service=settings.service_name,
        version=settings.service_version,
        artifacts_dir=settings.model_artifacts_dir,
    )

    connection = connect_with_retry(settings.rabbitmq_url)

    logger.info(
        "Recommender service ready — waiting for messages",
        service=settings.service_name,
        note="Consumers will be registered in v0.2.0",
    )

    stop_event = threading.Event()

    def _handle_signal(signum: int, frame: object) -> None:
        logger.info("Shutdown signal received", signal=signum)
        stop_event.set()

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    stop_event.wait()

    logger.info("Recommender service shutting down")
    try:
        connection.close()
    except Exception:
        pass


if __name__ == "__main__":
    main()
