"""
Command payloads — the data inside MessageEnvelope.payload for command messages.

Commands request work. They are published to the repopulse.commands exchange
and consumed by the service that owns that work.

Routing keys:
  github.sync.requested          → ingestion-service
  model.training.requested       → recommender-service
  recommendations.generation.requested → recommender-service
"""
from typing import Optional

from pydantic import BaseModel


class GitHubSyncPayload(BaseModel):
    """Payload for github.sync.requested."""
    github_username: str
    github_token: Optional[str] = None   # Never logged; treated as a secret.
    learning_goals: list[str] = []


class ModelTrainingPayload(BaseModel):
    """Payload for model.training.requested."""
    user_id: str
    # Future: hyperparameter overrides could go here.


class RecommendationGenerationPayload(BaseModel):
    """Payload for recommendations.generation.requested."""
    user_id: str
    model_run_id: Optional[str] = None   # If None, use the latest available model.
    top_k: int = 20
