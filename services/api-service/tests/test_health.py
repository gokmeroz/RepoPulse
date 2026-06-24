"""
Startup tests for the API service health endpoints.

These tests use FastAPI's TestClient (synchronous) and mock the blocking
I/O calls so no real database or broker is needed.
"""
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_200():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "repopulse-api"


def test_ready_returns_200_when_all_healthy():
    with (
        patch("app.api.health._check_postgres", return_value=True),
        patch("app.api.health._check_rabbitmq", return_value=True),
    ):
        response = client.get("/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["checks"]["postgres"] == "ok"
    assert body["checks"]["rabbitmq"] == "ok"


def test_ready_returns_503_when_postgres_unavailable():
    with (
        patch("app.api.health._check_postgres", return_value=False),
        patch("app.api.health._check_rabbitmq", return_value=True),
    ):
        response = client.get("/ready")
    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "not ready"
    assert body["checks"]["postgres"] == "unavailable"
    assert body["checks"]["rabbitmq"] == "ok"


def test_ready_returns_503_when_rabbitmq_unavailable():
    with (
        patch("app.api.health._check_postgres", return_value=True),
        patch("app.api.health._check_rabbitmq", return_value=False),
    ):
        response = client.get("/ready")
    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "not ready"
    assert body["checks"]["rabbitmq"] == "unavailable"


def test_ready_returns_503_when_all_unavailable():
    with (
        patch("app.api.health._check_postgres", return_value=False),
        patch("app.api.health._check_rabbitmq", return_value=False),
    ):
        response = client.get("/ready")
    assert response.status_code == 503
