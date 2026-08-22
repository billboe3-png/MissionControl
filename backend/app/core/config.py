from functools import lru_cache

from pydantic import Field, computed_field, field_validator
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

    edition: str = Field(
        default="community",
        alias="EDITION",
        description="Server edition: community or enterprise",
    )

    compose_project_name: str = Field(
        default="missioncontrol",
        alias="COMPOSE_PROJECT_NAME",
    )

    # ------------------------------------------------------------------
    # Security
    # ------------------------------------------------------------------

    missioncontrol_secret_key: str = Field(
        alias="MISSIONCONTROL_SECRET_KEY",
    )

    @field_validator("missioncontrol_secret_key")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Validate the secret key is a valid Fernet key."""
        from cryptography.fernet import Fernet, InvalidToken

        if not v:
            raise ValueError(
                "MISSIONCONTROL_SECRET_KEY must not be empty"
            )
        try:
            Fernet(v.encode() if isinstance(v, str) else v)
        except (InvalidToken, ValueError) as exc:
            raise ValueError(
                "MISSIONCONTROL_SECRET_KEY must be a valid Fernet key. "
                "Generate one with: python -c \"from cryptography.fernet "
                "import Fernet; print(Fernet.generate_key().decode())\""
            ) from exc
        return v


    # ------------------------------------------------------------------
    # Edge Agent Bundle
    # ------------------------------------------------------------------

    edge_agent_root: str = Field(
        default="/project/.agents",
        alias="MC_EDGE_AGENT_ROOT",
        description="Root directory for edge agent bundle storage",
    )

    # ------------------------------------------------------------------
    # PostgreSQL
    # ------------------------------------------------------------------

    postgres_db: str = Field(
        default="mission_control",
        alias="POSTGRES_DB",
    )

    postgres_user: str = Field(
        default="",
        alias="POSTGRES_USER",
    )

    postgres_password: str = Field(
        default="",
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

    ssh_connect_timeout: int = Field(
        default=10,
        alias="SSH_CONNECT_TIMEOUT",
    )

    ssh_command_timeout: int = Field(
        default=60,
        alias="SSH_COMMAND_TIMEOUT",
    )

    ssh_idle_timeout: int = Field(
        default=300,
        alias="SSH_IDLE_TIMEOUT",
    )

    winrm_connect_timeout: int = Field(
        default=10,
        alias="WINRM_CONNECT_TIMEOUT",
    )

    winrm_operation_timeout: int = Field(
        default=60,
        alias="WINRM_OPERATION_TIMEOUT",
    )

    remote_max_command_timeout: int = Field(
        default=3600,
        alias="REMOTE_MAX_COMMAND_TIMEOUT",
    )

    remote_retry_count: int = Field(
        default=1,
        alias="REMOTE_RETRY_COUNT",
    )

    # When True, unknown SSH host keys are auto-accepted (paramiko
    # AutoAddPolicy). This is convenient for first-time connections to
    # managed home-lab hosts but is vulnerable to MITM. Default False:
    # the client rejects unknown hosts and relies on the system known_hosts
    # file. Set to True only for trusted, single-purpose automation hosts.
    ssh_auto_add_host_keys: bool = Field(
        default=False,
        alias="SSH_AUTO_ADD_HOST_KEYS",
    )

    remote_connection_pool_size: int = Field(
        default=5,
        alias="REMOTE_CONNECTION_POOL_SIZE",
    )

    # ------------------------------------------------------------------
    # Active Directory
    # ------------------------------------------------------------------

    ad_server: str = Field(
        default="",
        alias="AD_SERVER",
    )

    ad_port: int = Field(
        default=636,
        alias="AD_PORT",
    )

    ad_use_ssl: bool = Field(
        default=True,
        alias="AD_USE_SSL",
    )

    ad_username: str = Field(
        default="",
        alias="AD_USERNAME",
    )

    ad_password: str = Field(
        default="",
        alias="AD_PASSWORD",
    )

    ad_base_dn: str = Field(
        default="",
        alias="AD_BASE_DN",
    )

    # ------------------------------------------------------------------
    # Microsoft 365
    # ------------------------------------------------------------------

    m365_tenant_id: str = Field(
        default="",
        alias="M365_TENANT_ID",
    )

    m365_client_id: str = Field(
        default="",
        alias="M365_CLIENT_ID",
    )

    m365_client_secret: str = Field(
        default="",
        alias="M365_CLIENT_SECRET",
    )

    # ------------------------------------------------------------------
    # Zabbix
    # ------------------------------------------------------------------

    zabbix_url: str = Field(
        default="",
        alias="ZABBIX_URL",
    )

    zabbix_username: str = Field(
        default="",
        alias="ZABBIX_USERNAME",
    )

    zabbix_password: str = Field(
        default="",
        alias="ZABBIX_PASSWORD",
    )

    zabbix_verify_ssl: bool = Field(
        default=True,
        alias="ZABBIX_VERIFY_SSL",
    )

    zabbix_timeout: int = Field(
        default=30,
        alias="ZABBIX_TIMEOUT",
    )

    zabbix_retries: int = Field(
        default=3,
        alias="ZABBIX_RETRIES",
    )

    # ------------------------------------------------------------------
    # Rate Limiting
    # ------------------------------------------------------------------

    rate_limit_per_minute: int = Field(
        default=300,
        description="Max requests per minute per IP",
    )

    rate_limit_auth_per_minute: int = Field(
        default=20,
        description="Max login attempts per minute per IP",
    )

    rate_limit_authenticated_per_minute: int = Field(
        default=600,
        description="Max requests per minute per authenticated user",
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
