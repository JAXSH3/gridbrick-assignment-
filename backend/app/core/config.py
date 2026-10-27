"""Application configuration settings."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Core application settings with environment variable overrides."""

    PROJECT_NAME: str = "UK Wind Day-Ahead Procurement Desk"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Default day-ahead cutoff time (UTC) on D-1
    DEFAULT_CUTOFF_TIME: str = "09:00"

    # Database file path
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    DATABASE_PATH: Path = DATA_DIR / "energy_cache.db"

    # CORS origins
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()
