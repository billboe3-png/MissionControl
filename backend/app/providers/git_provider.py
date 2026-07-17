"""
Mission Control Git Provider

Returns live repository information using GitPython.
No shell commands. No subprocess calls.

Gracefully handles Git unavailable or not a repository.
"""

import logging
import os
from datetime import UTC, datetime

logger = logging.getLogger(__name__)

_REPOSITORY_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")


def _find_repo_path() -> str:
    """Walk up from this file to find the .git directory."""
    candidates = ["/project", os.path.abspath(_REPOSITORY_ROOT)]
    for root in candidates:
        path = os.path.abspath(root)
        while path != os.path.dirname(path):
            if os.path.isdir(os.path.join(path, ".git")):
                return path
            path = os.path.dirname(path)
    return os.path.abspath(_REPOSITORY_ROOT)


class GitProvider:
    """Return live Git repository metadata."""

    def get_git_info(self) -> dict:
        """Return repository state. Falls back to unavailable if GitPython fails."""
        try:
            import git

            repo_path = _find_repo_path()
            repo = git.Repo(repo_path, search_parent_directories=True)

            branch = None
            try:
                branch = repo.active_branch.name
            except Exception:
                pass

            latest_commit = None
            commit_author = None
            commit_date = None
            try:
                head_commit = repo.head.commit
                latest_commit = head_commit.hexsha[:12]
                commit_author = str(head_commit.author.name)
                commit_date = datetime.fromtimestamp(
                    head_commit.committed_date, tz=UTC
                ).isoformat()
            except Exception:
                pass

            working_tree_clean = True
            try:
                working_tree_clean = not repo.is_dirty()
            except Exception:
                pass

            ahead_behind = {"ahead": 0, "behind": 0}
            try:
                if branch and "origin" in [r.name for r in repo.remotes]:
                    remote = repo.remotes.origin
                    remote_ref = f"origin/{branch}"
                    if remote_ref in repo.refs:
                        ahead_behind = {
                            "ahead": len(
                                list(
                                    repo.iter_commits(
                                        f"{remote_ref}..{branch}"
                                    )
                                )
                            ),
                            "behind": len(
                                list(
                                    repo.iter_commits(
                                        f"{branch}..{remote_ref}"
                                    )
                                )
                            ),
                        }
            except Exception:
                pass

            remote_url = None
            try:
                if "origin" in [r.name for r in repo.remotes]:
                    remote_url = str(repo.remotes.origin.url)
            except Exception:
                pass

            last_pull = None
            try:
                git_dir = repo.git_dir
                fetch_head_path = os.path.join(git_dir, "FETCH_HEAD")
                if os.path.exists(fetch_head_path):
                    mtime = os.path.getmtime(fetch_head_path)
                    last_pull = datetime.fromtimestamp(
                        mtime, tz=UTC
                    ).isoformat()
            except Exception:
                pass

            return {
                "available": True,
                "repository_name": os.path.basename(repo_path),
                "current_branch": branch,
                "latest_commit": latest_commit,
                "commit_author": commit_author,
                "commit_date": commit_date,
                "working_tree_clean": working_tree_clean,
                "ahead_of_origin": ahead_behind["ahead"],
                "behind_origin": ahead_behind["behind"],
                "last_pull": last_pull,
                "remote_url": remote_url,
            }

        except ImportError:
            logger.warning("GitPython not installed")
            return self._unavailable("GitPython not installed")

        except Exception as exc:
            logger.warning("Git provider failed: %s", exc)
            return self._unavailable(str(exc))

    @staticmethod
    def _unavailable(reason: str) -> dict:
        return {
            "available": False,
            "repository_name": None,
            "current_branch": None,
            "latest_commit": None,
            "commit_author": None,
            "commit_date": None,
            "working_tree_clean": True,
            "ahead_of_origin": 0,
            "behind_origin": 0,
            "last_pull": None,
            "remote_url": None,
            "reason": reason,
        }


git_provider = GitProvider()
