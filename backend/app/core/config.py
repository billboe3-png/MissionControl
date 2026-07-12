from functools import lru_cache

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ------------------------------------------------------------------
    # Application
    # ------------------------------------------------------------------

    project_name: str = Field(
        default="Mission Control",
        alias="PROJECT_NAME",
    )

    environment: str = Field(
        default="development",
        alias="ENVIRONMENT",
    )

    compose_project_name: str = Field(
        default="missioncontrol",
        alias="COMPOSE_PROJECT_NAME",
    )

    # ------------------------------------------------------------------
    # PostgreSQL
    # ------------------------------------------------------------------

    postgres_db: str = Field(
        default="mission_control",
        alias="POSTGRES_DB",
    )

    postgres_user: str = Field(
        default="mission_control",
        alias="POSTGRES_USER",
    )

    postgres_password: str = Field(
        default="mission_control",
        alias="POSTGRES_PASSWORD",
    )

    postgres_host: str = Field(
        default="postgres",
        alias="POSTGRES_HOST",
    )

    postgres_port: int = Field(
        default=5432,
        alias="POSTGRES_PORT",
    )

    # ------------------------------------------------------------------
    # Redis
    # ------------------------------------------------------------------

    redis_host: str = Field(
        default="redis",
        alias="REDIS_HOST",
    )

    redis_port: int = Field(
        default=6379,
        alias="REDIS_PORT",
    )

    # ------------------------------------------------------------------
    # SQLAlchemy
    # ------------------------------------------------------------------

    database_echo: bool = Field(
        default=False,
        alias="DATABASE_ECHO",
    )

    database_pool_size: int = Field(
        default=10,
        alias="DATABASE_POOL_SIZE",
    )

    database_max_overflow: int = Field(
        default=20,
        alias="DATABASE_MAX_OVERFLOW",
    )

    # ------------------------------------------------------------------
    # Remote Operations
    # ------------------------------------------------------------------

    terminal_max_sessions: int = Field(
        default=10,
        alias="TERMINAL_MAX_SESSIONS",
    )

    # ------------------------------------------------------------------
    # API
    # ------------------------------------------------------------------

    backend_cors_origins: str = Field(
        default="http://localhost,http://localhost:3000,http://localhost:5173",
        alias="BACKEND_CORS_ORIGINS",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # Computed Properties
    # ------------------------------------------------------------------

    @computed_field
    @property
    def database_url(self) -> str:
        """
        SQLAlchemy connection string using the psycopg3 driver.
        """
        return (
            f"postgresql+psycopg://"
            f"{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}"
            f"/{self.postgres_db}"
        )

    @computed_field
    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/0"

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.backend_cors_origins.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
