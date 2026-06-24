"""
Event payloads — the data inside MessageEnvelope.payload for event messages.

Events report outcomes. They are published to the repopulse.events exchange
and consumed by the API service to update job statuses.

Routing keys:
  github.sync.completed / github.sync.failed
  model.training.completed / model.training.failed
  recommendations.generated / recommendations.generation.failed
"""
from typing import Optional

from pydantic import BaseModel


class GitHubSyncCompletedPayload(BaseModel):
    """Payload for github.sync.completed."""
    starred_count: int
    candidate_count: int
    sync_run_id: str


class GitHubSyncFailedPayload(BaseModel):
    """Payload for github.sync.failed."""
    reason: str
    retriable: bool = True


class ModelTrainingCompletedPayload(BaseModel):
    """Payload for model.training.completed."""
    model_run_id: str
    precision_at_10: float
    ndcg_at_10: float


class ModelTrainingFailedPayload(BaseModel):
    """Payload for model.training.failed."""
    reason: str
    retriable: bool = True


class RecommendationsGeneratedPayload(BaseModel):
    """Payload for recommendations.generated."""
    recommendation_run_id: str
    count: int
    model_version: str   # e.g. "ranker-v1.0.0" or "baseline"


class RecommendationsGenerationFailedPayload(BaseModel):
    """Payload for recommendations.generation.failed."""
    reason: str
    retriable: bool = True
