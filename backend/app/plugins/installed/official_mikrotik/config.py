"""
MikroTik Plugin Configuration
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class MikroTikPluginConfig(BaseSettings):
    """Plugin-level configuration."""

    model_config = SettingsConfigDict(env_prefix="MIKROTIK_", extra="ignore")

    default_ssh_port: int = 22
    default_telnet_port: int = 23
    default_webfig_port: int = 80
    connection_timeout: int = 30
    command_timeout: int = 60
    auto_sync_enabled: bool = True
    sync_interval_seconds: int = 300
