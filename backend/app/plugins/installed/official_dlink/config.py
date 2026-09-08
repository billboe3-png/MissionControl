"""
D-Link DGS-1210 Plugin Configuration
"""
from pydantic import BaseModel, Field
from typing import Optional


class DLinkPluginConfig(BaseModel):
    """Plugin configuration loaded from database/settings."""
    auto_sync_enabled: bool = Field(default=True, description="Enable automatic background sync")
    sync_interval_seconds: int = Field(default=300, ge=60, description="Inventory sync interval in seconds")
    cli_timeout: int = Field(default=30, ge=5, le=300, description="CLI command timeout in seconds")
    webui_port: int = Field(default=443, description="Default Web UI port")
    webui_use_https: bool = Field(default=True, description="Use HTTPS for Web UI by default")
    ssh_port: int = Field(default=22, description="Default SSH port for CLI")
    telnet_port: int = Field(default=23, description="Default Telnet port for CLI")


def get_plugin_config() -> DLinkPluginConfig:
    """Get plugin configuration (can be overridden by database settings)."""
    return DLinkPluginConfig()