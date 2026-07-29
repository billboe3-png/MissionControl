"""
Git Plugin SQLAlchemy Models

Tables for caching Git repository data locally:
- git_repositories: registered repository connections
- git_branches: cached branch inventory
- git_commits: cached commit history
- git_remotes: cached remote configuration
"""

from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class GitRepository(Base):
    """Registered Git repository connection."""

    __tablename__ = "git_repositories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    integration_profile_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True, index=True,
        comment="FK to integration_profiles.id (nullable for local repos)",
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    path: Mapped[str] = mapped_column(String(1000), nullable=False, unique=True)
    remote_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="unknown")
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class GitBranch(Base):
    """Cached Git branch inventory."""

    __tablename__ = "git_branches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    repo_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("git_repositories.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_remote: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    ahead_of_remote: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    behind_remote: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_commit_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_commit_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_commit_author: Mapped[str | None] = mapped_column(String(200), nullable=True)
    last_commit_date: Mapped[str | None] = mapped_column(String(50), nullable=True)
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class GitCommit(Base):
    """Cached Git commit history."""

    __tablename__ = "git_commits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    repo_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("git_repositories.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    commit_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    short_id: Mapped[str] = mapped_column(String(20), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    date: Mapped[str] = mapped_column(String(50), nullable=False)
    branch: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_merge: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )


class GitRemote(Base):
    """Cached Git remote configuration."""

    __tablename__ = "git_remotes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    repo_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("git_repositories.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    push_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
