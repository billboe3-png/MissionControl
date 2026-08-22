"""Mission Control Agent - Offline buffering and command queue."""

import json
import logging
import time
from pathlib import Path

logger = logging.getLogger("mc-agent")


class CommandQueue:
    """Persistent command queue for offline buffering with priorities, retries, and progress tracking."""

    def __init__(self, data_dir: Path, max_size: int = 1000):
        self.data_dir = data_dir
        self.max_size = max_size
        self.queue_file = data_dir / "command_queue.json"
        self.results_file = data_dir / "pending_results.json"
        self.progress_file = data_dir / "command_progress.json"
        self._ensure_dir()

    def _ensure_dir(self) -> None:
        """Ensure data directory exists."""
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def queue_command(self, command: dict, priority: int = 3) -> None:
        """Queue a command for later execution with priority (1=critical, 2=high, 3=normal, 4=low)."""
        command.setdefault("id", int(time.time() * 1000))
        command["priority"] = max(1, min(4, priority))
        command.setdefault("status", "queued")
        command.setdefault("retry_count", 0)
        command.setdefault("max_retries", 3)
        command.setdefault("scheduled_at", None)
        command.setdefault("timeout", None)
        command.setdefault("queued_at", time.time())
        commands = self._load_queue()
        if len(commands) >= self.max_size:
            commands = commands[-(self.max_size - 1) :]
        commands.append(command)
        self._save_queue(commands)

    def dequeue_command(self) -> dict | None:
        """Dequeue the next command (highest priority first, then FIFO)."""
        commands = self._load_queue()
        if not commands:
            return None
        now = time.time()
        executable = [
            c
            for c in commands
            if c.get("scheduled_at") is None or c["scheduled_at"] <= now
        ]
        if not executable:
            return None
        executable.sort(key=lambda c: (c.get("priority", 3), c.get("queued_at", 0)))
        best = executable[0]
        remaining = [c for c in commands if c.get("id") != best.get("id")]
        self._save_queue(remaining)
        return best

    def get_next_command(self) -> dict | None:
        """Dequeue highest priority command first."""
        return self.dequeue_command()

    def cancel_command(self, command_id: int) -> bool:
        """Mark a command as cancelled."""
        commands = self._load_queue()
        for cmd in commands:
            if cmd.get("id") == command_id:
                cmd["status"] = "cancelled"
                self._save_queue(commands)
                return True
        return False

    def update_progress(
        self, command_id: int, progress: int, message: str = ""
    ) -> None:
        """Update progress for a command (0-100 percent)."""
        progress = max(0, min(100, progress))
        data = self._load_progress()
        data[str(command_id)] = {
            "progress": progress,
            "message": message,
            "updated_at": time.time(),
        }
        self._save_progress(data)

    def retry_command(self, command_id: int) -> bool:
        """Re-queue a command if under max retries."""
        commands = self._load_queue()

        for cmd in commands:
            if cmd.get("id") == command_id:
                if cmd.get("retry_count", 0) >= cmd.get("max_retries", 3):
                    logger.warning(
                        "Command %d exceeded max retries (%d)",
                        command_id,
                        cmd.get("max_retries", 3),
                    )
                    return False
                cmd["retry_count"] = cmd.get("retry_count", 0) + 1
                cmd["status"] = "queued"
                cmd["queued_at"] = time.time()
                self._save_queue(commands)
                logger.info(
                    "Re-queued command %d (retry %d/%d)",
                    command_id,
                    cmd["retry_count"],
                    cmd["max_retries"],
                )
                return True
        return False

    def get_queue_stats(self) -> dict:
        """Return counts by priority and status."""
        commands = self._load_queue()
        stats: dict = {
            "total": len(commands),
            "by_priority": {1: 0, 2: 0, 3: 0, 4: 0},
            "by_status": {},
            "scheduled_count": 0,
        }
        for cmd in commands:
            p = cmd.get("priority", 3)
            stats["by_priority"][p] = stats["by_priority"].get(p, 0) + 1
            s = cmd.get("status", "queued")
            stats["by_status"][s] = stats["by_status"].get(s, 0) + 1
            if cmd.get("scheduled_at") and cmd["scheduled_at"] > time.time():
                stats["scheduled_count"] += 1
        return stats

    def cleanup_stale(self, max_age_seconds: int = 3600) -> int:
        """Remove old commands, return count removed."""
        commands = self._load_queue()
        now = time.time()
        original_count = len(commands)
        commands = [
            c for c in commands if (now - c.get("queued_at", now)) < max_age_seconds
        ]
        removed = original_count - len(commands)
        if removed > 0:
            self._save_queue(commands)
            logger.info("Cleaned up %d stale commands from queue", removed)
        return removed

    def queue_result(self, result: dict) -> None:
        """Queue a result for later reporting."""
        results = self._load_results()
        if len(results) >= self.max_size:
            results = results[-(self.max_size - 1) :]
        results.append(result)
        self._save_results(results)

    def dequeue_result(self) -> dict | None:
        """Dequeue the next result."""
        results = self._load_results()
        if not results:
            return None
        result = results.pop(0)
        self._save_results(results)
        return result

    def get_pending_count(self) -> int:
        """Get number of pending commands."""
        return len(self._load_queue())

    def get_results_count(self) -> int:
        """Get number of pending results."""
        return len(self._load_results())

    def clear(self) -> None:
        """Clear all queued data."""
        self._save_queue([])
        self._save_results([])
        self._save_progress({})

    def _load_queue(self) -> list[dict]:
        """Load command queue from disk."""
        try:
            if self.queue_file.exists():
                with open(self.queue_file) as f:
                    return json.load(f)
        except (json.JSONDecodeError, OSError):
            logger.warning("Corrupted queue file, resetting")
        return []

    def _save_queue(self, commands: list[dict]) -> None:
        """Save command queue to disk."""
        try:
            with open(self.queue_file, "w") as f:
                json.dump(commands, f, indent=2)
        except OSError as e:
            logger.error("Failed to save queue: %s", e)

    def _load_results(self) -> list[dict]:
        """Load pending results from disk."""
        try:
            if self.results_file.exists():
                with open(self.results_file) as f:
                    return json.load(f)
        except (json.JSONDecodeError, OSError):
            logger.warning("Corrupted results file, resetting")
        return []

    def _save_results(self, results: list[dict]) -> None:
        """Save pending results to disk."""
        try:
            with open(self.results_file, "w") as f:
                json.dump(results, f, indent=2)
        except OSError as e:
            logger.error("Failed to save results: %s", e)

    def _load_progress(self) -> dict:
        """Load command progress from disk."""
        try:
            if self.progress_file.exists():
                with open(self.progress_file) as f:
                    return json.load(f)
        except (json.JSONDecodeError, OSError):
            logger.warning("Corrupted progress file, resetting")
        return {}

    def _save_progress(self, data: dict) -> None:
        """Save command progress to disk."""
        try:
            with open(self.progress_file, "w") as f:
                json.dump(data, f, indent=2)
        except OSError as e:
            logger.error("Failed to save progress: %s", e)
