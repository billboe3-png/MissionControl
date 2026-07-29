"""
Git Plugin REST API Routes

FastAPI router exposed by the Git plugin.
All routes are prefixed with /api/v1/plugins/git.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.plugins.installed.git.models import (
    GitBranch,
    GitCommit,
    GitRemote,
    GitRepository,
)

logger = logging.getLogger("plugin.git.routes")

router = APIRouter(prefix="/api/v1/plugins/git", tags=["git-plugin"])


@router.get("/repositories")
def list_repositories(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """List all registered Git repositories."""
    result = db.execute(select(GitRepository).order_by(GitRepository.name))
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


@router.get("/branches")
def list_branches(
    repo_id: int | None = Query(None),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """List cached Git branches."""
    stmt = select(GitBranch)
    if repo_id:
        stmt = stmt.where(GitBranch.repo_id == repo_id)
    stmt = stmt.order_by(GitBranch.name)
    result = db.execute(stmt)
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


@router.get("/commits")
def list_commits(
    repo_id: int | None = Query(None),
    limit: int = 50,
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """List cached Git commits."""
    stmt = select(GitCommit)
    if repo_id:
        stmt = stmt.where(GitCommit.repo_id == repo_id)
    stmt = stmt.order_by(GitCommit.date.desc()).limit(limit)
    result = db.execute(stmt)
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


@router.get("/remotes")
def list_remotes(
    repo_id: int | None = Query(None),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """List cached Git remotes."""
    stmt = select(GitRemote)
    if repo_id:
        stmt = stmt.where(GitRemote.repo_id == repo_id)
    stmt = stmt.order_by(GitRemote.name)
    result = db.execute(stmt)
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


@router.get("/summary")
def get_summary(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Aggregated Git repository summary from cache."""
    repo_count = (db.execute(select(func.count(GitRepository.id)))).scalar() or 0
    branch_count = (db.execute(select(func.count(GitBranch.id)))).scalar() or 0
    commit_count = (db.execute(select(func.count(GitCommit.id)))).scalar() or 0
    remote_count = (db.execute(select(func.count(GitRemote.id)))).scalar() or 0

    dirty_count = (
        db.execute(
            select(func.count(GitRepository.id)).where(GitRepository.status == "dirty")
        )
    ).scalar() or 0

    healthy_count = (
        db.execute(
            select(func.count(GitRepository.id)).where(GitRepository.status == "healthy")
        )
    ).scalar() or 0

    return {
        "repo_count": repo_count,
        "branch_count": branch_count,
        "commit_count": commit_count,
        "remote_count": remote_count,
        "dirty_repos": dirty_count,
        "healthy_repos": healthy_count,
    }


@router.get("/health")
def get_health(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Health status of cached Git repositories."""
    result = db.execute(select(GitRepository))
    repos = result.scalars().all()
    return {
        "repos": [
            {
                "id": r.id,
                "name": r.name,
                "status": r.status,
                "last_sync_at": r.last_sync_at.isoformat() if r.last_sync_at else None,
                "last_error": r.last_error,
            }
            for r in repos
        ],
        "total": len(repos),
        "healthy": sum(1 for r in repos if r.status == "healthy"),
    }
