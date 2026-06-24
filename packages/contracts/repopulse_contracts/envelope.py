"""
Message envelope — the outer wrapper for every RabbitMQ message in RepoPulse.

Every message, whether a command or an event, is wrapped in this envelope.
This gives every message a consistent identity (message_id), traceability
(correlation_id, job_id), retry awareness (attempt), and timing (occurred_at).

The actual command/event-specific data lives in `payload`.
"""
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class MessageEnvelope(BaseModel):
    # Unique ID for this specific message — used for idempotency checks.
    message_id: str = Field(default_factory=lambda: str(uuid4()))

    # Routing key / event type, e.g. "github.sync.requested".
    message_type: str

    # Ties together all messages that belong to one logical operation
    # (e.g. a single sync job: command + completion event share the same ID).
    correlation_id: str = Field(default_factory=lambda: str(uuid4()))

    # The RepoPulse job this message belongs to.
    job_id: str

    # The user who triggered the work.
    user_id: str

    # Starts at 1; incremented each time the message is requeued after failure.
    # Workers reject permanently (NACK without requeue) once attempt > MAX_RETRIES.
    attempt: int = 1

    # UTC timestamp set by the publisher at send time.
    occurred_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # Command- or event-specific data.
    payload: dict[str, Any] = Field(default_factory=dict)

    model_config = {"json_encoders": {datetime: lambda v: v.isoformat()}}
