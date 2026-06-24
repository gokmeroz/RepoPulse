from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "repopulse-recommender"
    service_version: str = "0.1.0"

    database_url: str = "postgresql://repopulse:repopulse@localhost:5432/repopulse"
    rabbitmq_url: str = "amqp://repopulse:repopulse@localhost:5672/"

    log_level: str = "INFO"
    log_json: bool = True

    max_message_retries: int = 3

    # Directory where trained model checkpoints are saved/loaded.
    # Mounted as a Docker volume shared between recommender restarts.
    model_artifacts_dir: str = "/artifacts"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
