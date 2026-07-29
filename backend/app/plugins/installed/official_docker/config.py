"""
Docker Plugin Configuration

Pydantic models for multi-host Docker configuration.
Supports local Unix socket, TCP, and remote Docker Engine API.
"""

from pydantic import BaseModel, Field


class DockerHostConfig(BaseModel):
    """Configuration for a single Docker host."""

    name: str = "default"
    host: str = ""
    tls: bool = False
    tls_cert_path: str = ""
    tls_verify: bool = True
    timeout: int = 30
    retries: int = 3
    enabled: bool = True


class DockerPluginConfig(BaseModel):
    """Top-level plugin configuration."""

    hosts: list[DockerHostConfig] = Field(default_factory=list)
    auto_sync_enabled: bool = True
    sync_interval_seconds: int = 120
    max_containers: int = 2000
    max_images: int = 500
    max_volumes: int = 500
    max_networks: int = 200
    max_events: int = 500
    cpu_warning_pct: float = 80.0
    cpu_critical_pct: float = 95.0
    memory_warning_pct: float = 80.0
    memory_critical_pct: float = 95.0
    disk_warning_pct: float = 80.0
    disk_critical_pct: float = 95.0
