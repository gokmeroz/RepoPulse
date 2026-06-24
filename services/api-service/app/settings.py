from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "repopulse-api"
    app_version: str = "0.1.0"

    # Connection strings — must be set via environment or .env file.
    database_url: str = "postgresql://repopulse:repopulse@localhost:5432/repopulse"
    rabbitmq_url: str = "amqp://repopulse:repopulse@localhost:5672/"

    api_debug: bool = False
    log_level: str = "INFO"
    log_json: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
