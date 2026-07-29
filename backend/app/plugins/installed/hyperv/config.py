"""
Hyper-V Plugin Configuration

Pydantic models for plugin-level settings.
Note: Host configuration (WinRM/SSH credentials, transport) comes from
IntegrationProfile — not from this config. This config only controls
plugin behavior like sync interval and cache limits.
"""

from pydantic import BaseModel, Field


class HyperVPluginConfig(BaseModel):
    """Top-level plugin configuration."""

    auto_sync_enabled: bool = Field(
        default=True, description="Enable background sync"
    )
    sync_interval_seconds: int = Field(
        default=120, ge=30, le=3600, description="Background sync interval"
    )
    max_vms: int = Field(
        default=2000, ge=100, le=10000, description="Max VMs to cache"
    )
    max_networks: int = Field(
        default=200, ge=10, le=1000, description="Max networks to cache"
    )
    max_volumes: int = Field(
        default=500, ge=10, le=5000, description="Max volumes to cache"
    )
    max_checkpoints: int = Field(
        default=500, ge=10, le=5000, description="Max checkpoints to cache"
    )
    cpu_warning_pct: float = Field(
        default=80.0, ge=50, le=99, description="CPU warning threshold (%)"
    )
    cpu_critical_pct: float = Field(
        default=95.0, ge=80, le=100, description="CPU critical threshold (%)"
    )
    memory_warning_pct: float = Field(
        default=80.0, ge=50, le=99, description="Memory warning threshold (%)"
    )
    memory_critical_pct: float = Field(
        default=95.0, ge=80, le=100, description="Memory critical threshold (%)"
    )
