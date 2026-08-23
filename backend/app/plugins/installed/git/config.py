"""
Git Plugin Configuration

Pydantic models for plugin-level settings.
Repository configuration (paths, remotes) comes from IntegrationProfile.
"""

from pydantic import BaseModel, Field


class GitPluginConfig(BaseModel):
    """Top-level plugin configuration."""

    auto_sync_enabled: bool = Field(
        default=True, description="Enable background sync"
    )
    sync_interval_seconds: int = Field(
        default=120, ge=30, le=3600, description="Background sync interval"
    )
    max_repos: int = Field(
        default=50, ge=1, le=500, description="Max repositories to monitor"
    )
    max_commits: int = Field(
        default=50, ge=5, le=500, description="Max commits to cache per repo"
    )
    commit_retention_days: int = Field(
        default=30, ge=1, le=365, description="Commit history retention"
    )
    git_timeout: int = Field(
        default=30, ge=5, le=120, description="Git command timeout (seconds)"
    )
