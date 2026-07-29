"""
Git Plugin Sync

Background synchronization classes that pull data from Git repositories
via the git CLI and write to local cache tables.
"""

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.plugins.installed.git.models import (
    GitBranch,
    GitCommit,
    GitRemote,
    GitRepository,
)

if TYPE_CHECKING:
    from app.plugins.installed.git.api import GitApiClient

logger = logging.getLogger("plugin.git.sync")


class RepositorySync:
    """Synchronize repository registrations."""

    def sync(self, session: Session, repo_id: int, repo_info: dict) -> int:
        """Upsert a repository record."""
        stmt = pg_insert(GitRepository).values(
            id=repo_id,
            name=repo_info.get("name", "unknown"),
            path=repo_info.get("path", ""),
            remote_url=repo_info.get("remote_url"),
            enabled=True,
            last_sync_at=datetime.now(UTC),
            status="healthy",
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["id"],
            set_={
                "name": repo_info.get("name", "unknown"),
                "path": repo_info.get("path", ""),
                "remote_url": repo_info.get("remote_url"),
                "enabled": True,
                "last_sync_at": datetime.now(UTC),
                "status": "healthy",
            },
        )
        session.execute(stmt)
        session.commit()
        return 1


class BranchSync:
    """Synchronize branch inventory from Git to local cache."""

    def sync(self, session: Session, client: "GitApiClient", repo_id: int) -> dict[str, int]:
        """Pull branches and upsert into git_branches."""
        branches = client.get_branches_sync()
        synced = 0

        for b in branches:
            name = b.get("name", "")
            if not name:
                continue

            ahead = 0
            behind = 0
            if not b.get("is_remote"):
                ab = client.get_ahead_behind_sync(name)
                ahead = ab.get("ahead", 0)
                behind = ab.get("behind", 0)

            stmt = pg_insert(GitBranch).values(
                repo_id=repo_id,
                name=name,
                is_current=b.get("is_current", False),
                is_remote=b.get("is_remote", False),
                ahead_of_remote=ahead,
                behind_remote=behind,
                last_commit_id=b.get("commit_id"),
                last_seen_at=datetime.now(UTC),
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["repo_id", "name"],
                set_={
                    "is_current": b.get("is_current", False),
                    "is_remote": b.get("is_remote", False),
                    "ahead_of_remote": ahead,
                    "behind_remote": behind,
                    "last_commit_id": b.get("commit_id"),
                    "last_seen_at": datetime.now(UTC),
                },
            )
            session.execute(stmt)
            synced += 1

        session.commit()
        logger.info("Branch sync: %d synced", synced)
        return {"synced": synced}


class CommitSync:
    """Synchronize commit history from Git to local cache."""

    def sync(self, session: Session, client: "GitApiClient", repo_id: int, limit: int = 50) -> dict[str, int]:
        """Pull commits and upsert into git_commits."""
        commits = client.get_commits_sync(limit=limit)
        synced = 0

        for c in commits:
            commit_id = c.get("commit_id", "")
            if not commit_id:
                continue

            stmt = pg_insert(GitCommit).values(
                repo_id=repo_id,
                commit_id=commit_id,
                short_id=c.get("short_id", ""),
                message=c.get("message", ""),
                author=c.get("author", ""),
                email=c.get("email"),
                date=c.get("date", ""),
                is_merge=c.get("is_merge", False),
                last_seen_at=datetime.now(UTC),
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["repo_id", "commit_id"],
                set_={
                    "short_id": c.get("short_id", ""),
                    "message": c.get("message", ""),
                    "author": c.get("author", ""),
                    "email": c.get("email"),
                    "date": c.get("date", ""),
                    "is_merge": c.get("is_merge", False),
                    "last_seen_at": datetime.now(UTC),
                },
            )
            session.execute(stmt)
            synced += 1

        session.commit()
        logger.info("Commit sync: %d synced", synced)
        return {"synced": synced}


class RemoteSync:
    """Synchronize remote configuration from Git to local cache."""

    def sync(self, session: Session, client: "GitApiClient", repo_id: int) -> dict[str, int]:
        """Pull remotes and upsert into git_remotes."""
        remotes = client.get_remotes_sync()
        synced = 0

        for r in remotes:
            name = r.get("name", "")
            if not name:
                continue

            stmt = pg_insert(GitRemote).values(
                repo_id=repo_id,
                name=name,
                url=r.get("url", ""),
                last_seen_at=datetime.now(UTC),
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["repo_id", "name"],
                set_={
                    "url": r.get("url", ""),
                    "last_seen_at": datetime.now(UTC),
                },
            )
            session.execute(stmt)
            synced += 1

        session.commit()
        logger.info("Remote sync: %d synced", synced)
        return {"synced": synced}
