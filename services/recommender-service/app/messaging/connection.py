"""
RabbitMQ connection with exponential-backoff retry.
Identical strategy to the ingestion service — see that module for the rationale.
"""
import time

import pika
import structlog

logger = structlog.get_logger()


def connect_with_retry(
    url: str,
    max_retries: int = 10,
    base_delay: float = 1.0,
) -> pika.BlockingConnection:
    for attempt in range(1, max_retries + 1):
        try:
            params = pika.URLParameters(url)
            connection = pika.BlockingConnection(params)
            logger.info("Connected to RabbitMQ", attempt=attempt)
            return connection
        except Exception as exc:
            if attempt == max_retries:
                logger.error(
                    "Failed to connect to RabbitMQ — giving up",
                    attempt=attempt,
                    max_retries=max_retries,
                    error=str(exc),
                )
                raise

            delay = base_delay * (2 ** (attempt - 1))
            logger.warning(
                "RabbitMQ not ready — retrying",
                attempt=attempt,
                retry_in_seconds=delay,
                error=str(exc),
            )
            time.sleep(delay)
