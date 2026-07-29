"""
UniFi Plugin Configuration

Pydantic models for multi-site / multi-controller UniFi configuration.
Supports both UniFi Site Manager (cloud) and local controllers.
"""

from pydantic import BaseModel, Field


class UniFiControllerConfig(BaseModel):
    """Configuration for a single UniFi controller or Site Manager org."""

    name: str = "default"
    url: str = ""
    api_key: str = ""
    site_id: str = "default"
    verify_ssl: bool = True
    timeout: int = 30
    retries: int = 3
    enabled: bool = True
    controller_type: str = "cloud"


class UniFiPluginConfig(BaseModel):
    """Top-level plugin configuration."""

    controllers: list[UniFiControllerConfig] = Field(default_factory=list)
    auto_sync_enabled: bool = True
    sync_interval_seconds: int = 300
    max_clients: int = 2000
    max_devices: int = 500
    max_alerts: int = 500
    alert_retention_days: int = 30
    client_retention_days: int = 7
    cpu_warning_pct: float = 80.0
    cpu_critical_pct: float = 95.0
    memory_warning_pct: float = 80.0
    memory_critical_pct: float = 95.0
    temperature_warning_c: float = 60.0
    temperature_critical_c: float = 75.0
