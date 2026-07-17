"""Mission Control Agent - Offline buffering and command queue."""

import json
import logging
from pathlib import Path

logger = logging.getLogger("mc-agent")


class CommandQueue:
    """Persistent command queue for offline buffering."""

    def __init__(self, data_dir: Path, max_size: int = 1000):
        self.data_dir = data_dir
        self.max_size = max_size
        self.queue_file = data_dir / "command_queue.json"
        self.results_file = data_dir / "pending_results.json"
        self._ensure_dir()

    def _ensure_dir(self) -> None:
        """Ensure data directory exists."""
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def queue_command(self, command: dict) -> None:
        """Queue a command for later execution."""
        commands = self._load_queue()
        if len(commands) >= self.max_size:
            commands = commands[-(self.max_size - 1) :]
        commands.append(command)
        self._save_queue(commands)

    def dequeue_command(self) -> dict | None:
        """Dequeue the next command."""
        commands = self._load_queue()
        if not commands:
            return None
        command = commands.pop(0)
        self._save_queue(commands)
        return command

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
