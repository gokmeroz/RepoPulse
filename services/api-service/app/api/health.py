"""
/health and /ready endpoints.

/health — liveness check. Returns 200 as long as the process is running.
          Docker and load balancers use this to know whether to restart the container.

/ready  — readiness check. Returns 200 only when both PostgreSQL and RabbitMQ
          are reachable. Returns 503 otherwise.
          Docker Compose uses this to decide when downstream services can start.

We run the blocking DB/broker checks in a thread-pool executor so they don't
block FastAPI's async event loop.
"""
import asyncio
from typing import Any

import pika
import psycopg2
import structlog
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.settings import settings

router = APIRouter(tags=["health"])
logger = structlog.get_logger()


def _check_postgres() -> bool:
    try:
        conn = psycopg2.connect(settings.database_url, connect_timeout=2)
        conn.close()
        return True
    except Exception as exc:
        logger.warning("PostgreSQL readiness check failed", error=str(exc))
        return False


def _check_rabbitmq() -> bool:
    try:
        params = pika.URLParameters(settings.rabbitmq_url)
        params.socket_timeout = 2
        params.connection_attempts = 1
        conn = pika.BlockingConnection(params)
        conn.close()
        return True
    except Exception as exc:
        logger.warning("RabbitMQ readiness check failed", error=str(exc))
        return False


@router.get("/health", summary="Liveness check")
async def health() -> dict[str, Any]:
    return {"status": "ok", "service": settings.app_name, "version": settings.app_version}


@router.get("/ready", summary="Readiness check")
async def ready() -> JSONResponse:
    loop = asyncio.get_event_loop()

    postgres_ok, rabbitmq_ok = await asyncio.gather(
        loop.run_in_executor(None, _check_postgres),
        loop.run_in_executor(None, _check_rabbitmq),
    )

    checks = {
        "postgres": "ok" if postgres_ok else "unavailable",
        "rabbitmq": "ok" if rabbitmq_ok else "unavailable",
    }
    all_healthy = all(v == "ok" for v in checks.values())
    status_code = 200 if all_healthy else 503

    return JSONResponse(
        status_code=status_code,
        content={"status": "ready" if all_healthy else "not ready", "checks": checks},
    )
