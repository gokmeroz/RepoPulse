"""
repopulse_contracts — shared message schemas.

Every RabbitMQ message in RepoPulse is described by a type in this package.
Services import from here; they never define their own wire formats.
"""
from repopulse_contracts.envelope import MessageEnvelope
from repopulse_contracts.commands import (
    GitHubSyncPayload,
    ModelTrainingPayload,
    RecommendationGenerationPayload,
)
from repopulse_contracts.events import (
    GitHubSyncCompletedPayload,
    GitHubSyncFailedPayload,
    ModelTrainingCompletedPayload,
    ModelTrainingFailedPayload,
    RecommendationsGeneratedPayload,
    RecommendationsGenerationFailedPayload,
)
from repopulse_contracts.identifiers import MessageId, CorrelationId, JobId, UserId

__all__ = [
    "MessageEnvelope",
    "GitHubSyncPayload",
    "ModelTrainingPayload",
    "RecommendationGenerationPayload",
    "GitHubSyncCompletedPayload",
    "GitHubSyncFailedPayload",
    "ModelTrainingCompletedPayload",
    "ModelTrainingFailedPayload",
    "RecommendationsGeneratedPayload",
    "RecommendationsGenerationFailedPayload",
    "MessageId",
    "CorrelationId",
    "JobId",
    "UserId",
]
