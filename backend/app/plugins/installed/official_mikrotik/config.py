"""
MikroTik Plugin Configuration
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class MikroTikPluginConfig(BaseSettings):
    """Plugin-level configuration (per-device settings live in the DB)."""

    model_config = SettingsConfigDict(env_prefix="MIKROTIK_", extra="ignore")

    connection_timeout: int = 30
    command_timeout: int = 60
    auto_sync_enabled: bool = True
    sync_interval_seconds: int = 300
