"""
Shared identifier types used in message envelopes and API responses.
All IDs are UUIDs represented as strings to keep JSON serialization simple.
"""
from typing import Annotated
from uuid import uuid4

from pydantic import Field

# Type alias — a UUID in string form, auto-generated when omitted.
MessageId = Annotated[str, Field(default_factory=lambda: str(uuid4()))]
CorrelationId = Annotated[str, Field(default_factory=lambda: str(uuid4()))]
JobId = Annotated[str, Field(default_factory=lambda: str(uuid4()))]
UserId = Annotated[str, Field(default_factory=lambda: str(uuid4()))]
