"""
Veeam Plugin Configuration

Pydantic models for multi-server Veeam B&R configuration.
Credentials are stored encrypted via Mission Control Secret Management.
"""

from pydantic import BaseModel, Field


class VeeamServerConfig(BaseModel):
    """Configuration for a single Veeam B&R server."""

    name: str = "default"
    edition: str = "enterprise"
    data_source: str = "both"
    db_type: str = "auto"
    column_case: str = "pascal"
    agent_id: int | None = None
    target_id: int | None = None
    url: str = ""
    username: str = ""
    password: str = ""
    verify_ssl: bool = True
    timeout: int = 30
    retries: int = 3
    enabled: bool = True

    ssh_host: str = ""
    ssh_port: int = 22
    ssh_username: str = ""
    ssh_password: str = ""


class VeeamPluginConfig(BaseModel):
    """Top-level plugin configuration."""

    servers: list[VeeamServerConfig] = Field(default_factory=list)
    auto_sync_enabled: bool = True
    sync_interval_seconds: int = 300
    max_jobs: int = 500
    max_sessions: int = 500
    job_retention_days: int = 30
    event_retention_days: int = 30
    repo_capacity_warning_pct: float = 80.0
    repo_capacity_critical_pct: float = 95.0
