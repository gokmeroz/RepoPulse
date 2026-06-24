from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "repopulse-ingestion"
    service_version: str = "0.1.0"

    database_url: str = "postgresql://repopulse:repopulse@localhost:5432/repopulse"
    rabbitmq_url: str = "amqp://repopulse:repopulse@localhost:5672/"

    log_level: str = "INFO"
    log_json: bool = True

    # Maximum number of times a message is retried before being dead-lettered.
    # Implemented in v0.2.0 — defined here so it's visible from the start.
    max_message_retries: int = 3

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
