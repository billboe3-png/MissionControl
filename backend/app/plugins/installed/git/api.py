"""
Git Plugin API Client

Wraps the git CLI via subprocess calls.
Provides async and sync methods for repository operations.
"""

import asyncio
import logging
import os
import shutil
from typing import Any

logger = logging.getLogger("plugin.git.api")


class GitApiClient:
    """Git CLI client for repository monitoring."""

    def __init__(
        self,
        repo_path: str,
        timeout: int = 30,
        retries: int = 3,
    ) -> None:
        self._repo_path = repo_path.rstrip("/")
        self._timeout = timeout
        self._retries = retries

    def _git_cmd(self, *args: str) -> list[str]:
        """Build a git command with the repo path."""
        return ["git", "-C", self._repo_path, *args]

    async def _run(self, args: list[str]) -> dict[str, Any]:
        """Execute a git command asynchronously with retries."""
        last_error: Exception | None = None
        for attempt in range(1, self._retries + 1):
            try:
                proc = await asyncio.create_subprocess_exec(
                    *args,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=self._timeout
                )
                stdout_str = stdout.decode("utf-8", errors="replace")
                stderr_str = stderr.decode("utf-8", errors="replace")
                if proc.returncode == 0:
                    return {
                        "success": True,
                        "stdout": stdout_str,
                        "stderr": stderr_str,
                        "exit_code": 0,
                    }
                last_error = RuntimeError(
                    f"git exited with code {proc.returncode}: {stderr_str.strip()}"
                )
                if attempt < self._retries:
                    await asyncio.sleep(1)
            except asyncio.TimeoutError:
                last_error = TimeoutError(f"git command timed out after {self._timeout}s")
                if attempt < self._retries:
                    await asyncio.sleep(1)
            except FileNotFoundError:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": "git command not found",
                    "exit_code": -1,
                }
            except Exception as exc:
                last_error = exc
                if attempt < self._retries:
                    await asyncio.sleep(1)
        return {
            "success": False,
            "stdout": "",
            "stderr": str(last_error),
            "exit_code": -1,
        }

    async def test_connection(self) -> dict[str, Any]:
        """Test if the repository path is valid and git is available."""
        if not shutil.which("git"):
            return {"connected": False, "error": "git command not found"}
        if not os.path.isdir(self._repo_path):
            return {"connected": False, "error": f"Path does not exist: {self._repo_path}"}
        result = await self._run(self._git_cmd("rev-parse", "--git-dir"))
        if result["success"]:
            return {"connected": True, "path": self._repo_path}
        return {"connected": False, "error": result["stderr"]}

    async def get_repo_info(self) -> dict[str, Any]:
        """Get basic repository information."""
        path_result = await self._run(self._git_cmd("rev-parse", "--show-toplevel"))
        if not path_result["success"]:
            return {"connected": False, "error": path_result["stderr"]}

        repo_name = os.path.basename(path_result["stdout"].strip())

        branch_result = await self._run(self._git_cmd("rev-parse", "--abbrev-ref", "HEAD"))
        current_branch = branch_result["stdout"].strip() if branch_result["success"] else "unknown"

        remote_result = await self._run(self._git_cmd("remote", "get-url", "origin"))
        remote_url = remote_result["stdout"].strip() if remote_result["success"] else None

        return {
            "connected": True,
            "repository_name": repo_name,
            "repository_path": path_result["stdout"].strip(),
            "current_branch": current_branch,
            "remote_url": remote_url,
        }

    async def get_branches(self) -> list[dict[str, Any]]:
        """List all branches (local and remote)."""
        result = await self._run(self._git_cmd("branch", "--all", "--format=%(refname:short)|%(HEAD)|%(objectname:short)"))
        if not result["success"]:
            return []

        branches = []
        for line in result["stdout"].strip().splitlines():
            parts = line.split("|")
            if len(parts) >= 3:
                name = parts[0]
                is_current = parts[1] == "*"
                commit_id = parts[2]
                is_remote = name.startswith("origin/") or "/" in name
                branches.append({
                    "name": name,
                    "is_current": is_current,
                    "is_remote": is_remote,
                    "commit_id": commit_id,
                })
        return branches

    async def get_commits(self, branch: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        """Get recent commit history."""
        args = self._git_cmd("log", f"--max-count={limit}", "--format=%H|%h|%s|%an|%ae|%ad|%P", "--date=iso")
        if branch:
            args = self._git_cmd("log", f"--max-count={limit}", "--format=%H|%h|%s|%an|%ae|%ad|%P", "--date=iso", branch)

        result = await self._run(args)
        if not result["success"]:
            return []

        commits = []
        for line in result["stdout"].strip().splitlines():
            parts = line.split("|")
            if len(parts) >= 6:
                commits.append({
                    "commit_id": parts[0],
                    "short_id": parts[1],
                    "message": parts[2],
                    "author": parts[3],
                    "email": parts[4],
                    "date": parts[5],
                    "is_merge": len(parts) >= 7 and bool(parts[6]),
                })
        return commits

    async def get_remotes(self) -> list[dict[str, Any]]:
        """Get remote configuration."""
        result = await self._run(self._git_cmd("remote", "-v"))
        if not result["success"]:
            return []

        remotes = []
        seen = set()
        for line in result["stdout"].strip().splitlines():
            parts = line.split("\t")
            if len(parts) >= 2:
                name = parts[0]
                url_part = parts[1].split(" ")
                url = url_part[0] if url_part else ""
                if name not in seen:
                    seen.add(name)
                    remotes.append({
                        "name": name,
                        "url": url,
                    })
        return remotes

    async def get_status(self) -> dict[str, Any]:
        """Get working tree status."""
        result = await self._run(self._git_cmd("status", "--porcelain"))
        if not result["success"]:
            return {"clean": False, "error": result["stderr"]}

        lines = [l for l in result["stdout"].strip().splitlines() if l]
        return {
            "clean": len(lines) == 0,
            "dirty": len(lines) > 0,
            "changed_files": len(lines),
        }

    async def get_ahead_behind(self, branch: str) -> dict[str, int]:
        """Get ahead/behind count for a branch relative to origin."""
        remote_branch = f"origin/{branch}"
        result = await self._run(
            self._git_cmd("rev-list", "--count", f"{remote_branch}..{branch}")
        )
        ahead = 0
        if result["success"]:
            try:
                ahead = int(result["stdout"].strip())
            except ValueError:
                ahead = 0

        result = await self._run(
            self._git_cmd("rev-list", "--count", f"{branch}..{remote_branch}")
        )
        behind = 0
        if result["success"]:
            try:
                behind = int(result["stdout"].strip())
            except ValueError:
                behind = 0

        return {"ahead": ahead, "behind": behind}

    # ------------------------------------------------------------------ #
    # Sync wrappers for background thread use                              #
    # ------------------------------------------------------------------ #

    def _run_async(self, coro: Any) -> Any:
        """Run an async coroutine synchronously (for background thread use)."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result(timeout=self._timeout + 30)
        return asyncio.run(coro)

    def test_connection_sync(self) -> dict[str, Any]:
        return self._run_async(self.test_connection())

    def get_repo_info_sync(self) -> dict[str, Any]:
        return self._run_async(self.get_repo_info())

    def get_branches_sync(self) -> list[dict[str, Any]]:
        return self._run_async(self.get_branches())

    def get_commits_sync(self, branch: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        return self._run_async(self.get_commits(branch=branch, limit=limit))

    def get_remotes_sync(self) -> list[dict[str, Any]]:
        return self._run_async(self.get_remotes())

    def get_status_sync(self) -> dict[str, Any]:
        return self._run_async(self.get_status())

    def get_ahead_behind_sync(self, branch: str) -> dict[str, int]:
        return self._run_async(self.get_ahead_behind(branch))
