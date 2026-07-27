"""
Zabbix Plugin Configuration

Multi-server Zabbix connection configuration.
"""

from pydantic import BaseModel, Field


class ZabbixServerConfig(BaseModel):
    """Single Zabbix server connection details."""

    name: str = Field(default="default", description="Display name")
    url: str = Field(default="", description="Zabbix API URL")
    username: str = Field(default="", description="Zabbix username")
    password: str = Field(default="", description="Zabbix password")
    verify_ssl: bool = Field(default=True, description="Verify SSL certificates")
    timeout: int = Field(default=30, ge=1, le=300, description="Request timeout (s)")
    retries: int = Field(default=3, ge=0, le=10, description="Retry count")
    enabled: bool = Field(default=True, description="Enable this server")


class ZabbixPluginConfig(BaseModel):
    """Top-level plugin configuration."""

    servers: list[ZabbixServerConfig] = Field(default_factory=list)
    sync_interval_seconds: int = Field(
        default=300, ge=60, le=3600, description="Background sync interval"
    )
    auto_sync_enabled: bool = Field(default=True, description="Enable background sync")
    max_problems_per_host: int = Field(
        default=50, ge=1, le=500, description="Max problems to fetch per host"
    )
    event_retention_days: int = Field(
        default=30, ge=1, le=365, description="Local event retention"
    )
