"""
Git Plugin Cache

Provides convenient read access to cached Git data.
All queries use synchronous SQLAlchemy sessions.
"""

import logging
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.plugins.installed.git.models import (
    GitBranch,
    GitCommit,
    GitRemote,
    GitRepository,
)

logger = logging.getLogger("plugin.git.cache")


def get_repositories(session: Session) -> list[dict[str, Any]]:
    """Return all cached repositories."""
    result = session.execute(select(GitRepository).order_by(GitRepository.name))
    repos = result.scalars().all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "path": r.path,
            "remote_url": r.remote_url,
            "enabled": r.enabled,
            "status": r.status,
            "last_sync_at": r.last_sync_at.isoformat() if r.last_sync_at else None,
            "last_error": r.last_error,
        }
        for r in repos
    ]


def get_branches(session: Session, repo_id: int | None = None) -> list[dict[str, Any]]:
    """Return cached branches."""
    stmt = select(GitBranch)
    if repo_id:
        stmt = stmt.where(GitBranch.repo_id == repo_id)
    stmt = stmt.order_by(GitBranch.name)
    result = session.execute(stmt)
    branches = result.scalars().all()
    return [
        {
            "id": b.id,
            "repo_id": b.repo_id,
            "name": b.name,
            "is_current": b.is_current,
            "is_remote": b.is_remote,
            "ahead_of_remote": b.ahead_of_remote,
            "behind_remote": b.behind_remote,
            "last_commit_id": b.last_commit_id,
            "last_commit_message": b.last_commit_message,
            "last_commit_author": b.last_commit_author,
            "last_commit_date": b.last_commit_date,
        }
        for b in branches
    ]


def get_commits(session: Session, repo_id: int | None = None, limit: int = 50) -> list[dict[str, Any]]:
    """Return cached commits."""
    stmt = select(GitCommit)
    if repo_id:
        stmt = stmt.where(GitCommit.repo_id == repo_id)
    stmt = stmt.order_by(GitCommit.date.desc()).limit(limit)
    result = session.execute(stmt)
    commits = result.scalars().all()
    return [
        {
            "id": c.id,
            "repo_id": c.repo_id,
            "commit_id": c.commit_id,
            "short_id": c.short_id,
            "message": c.message,
            "author": c.author,
            "email": c.email,
            "date": c.date,
            "branch": c.branch,
            "is_merge": c.is_merge,
        }
        for c in commits
    ]


def get_remotes(session: Session, repo_id: int | None = None) -> list[dict[str, Any]]:
    """Return cached remotes."""
    stmt = select(GitRemote)
    if repo_id:
        stmt = stmt.where(GitRemote.repo_id == repo_id)
    stmt = stmt.order_by(GitRemote.name)
    result = session.execute(stmt)
    remotes = result.scalars().all()
    return [
        {
            "id": r.id,
            "repo_id": r.repo_id,
            "name": r.name,
            "url": r.url,
            "push_url": r.push_url,
        }
        for r in remotes
    ]


def get_summary(session: Session) -> dict[str, Any]:
    """Return aggregated summary from cached data."""
    repo_count = (session.execute(select(func.count(GitRepository.id)))).scalar() or 0
    branch_count = (session.execute(select(func.count(GitBranch.id)))).scalar() or 0
    commit_count = (session.execute(select(func.count(GitCommit.id)))).scalar() or 0
    remote_count = (session.execute(select(func.count(GitRemote.id)))).scalar() or 0

    dirty_repos = (
        session.execute(
            select(func.count(GitRepository.id)).where(GitRepository.status == "dirty")
        )
    ).scalar() or 0

    healthy_repos = (
        session.execute(
            select(func.count(GitRepository.id)).where(GitRepository.status == "healthy")
        )
    ).scalar() or 0

    return {
        "repo_count": repo_count,
        "branch_count": branch_count,
        "commit_count": commit_count,
        "remote_count": remote_count,
        "dirty_repos": dirty_repos,
        "healthy_repos": healthy_repos,
    }


class CacheManager:
    """Wrapper providing method-style access to cache functions."""

    def get_repositories(self, session: Session) -> list[dict[str, Any]]:
        return get_repositories(session)

    def get_branches(self, session: Session, repo_id: int | None = None) -> list[dict[str, Any]]:
        return get_branches(session, repo_id)

    def get_commits(self, session: Session, repo_id: int | None = None, limit: int = 50) -> list[dict[str, Any]]:
        return get_commits(session, repo_id, limit)

    def get_remotes(self, session: Session, repo_id: int | None = None) -> list[dict[str, Any]]:
        return get_remotes(session, repo_id)

    def get_summary(self, session: Session) -> dict[str, Any]:
        return get_summary(session)


cache_manager = CacheManager()
