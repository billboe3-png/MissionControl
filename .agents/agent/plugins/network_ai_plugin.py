"""Mission Control Edge Agent - Network AI Plugin (server-side AI).

Lightweight edge plugin that collects local context and forwards
questions to the Mission Control server for AI-assisted answers.
The AI model runs on the GCE server; the agent only sends context
and receives answers.
"""

from __future__ import annotations

import json
import logging
import os
import platform
import socket
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("mc-agent.plugin.network_ai")


class NetworkAIPlugin:
    """Network AI assistant client."""

    name = "network_ai"
    version = "1.0.0"
    description = "AI-assisted network troubleshooting via server-side model"
    platform_required = None

    def __init__(self, data_dir: Path | None = None):
        self._data_dir = (
            data_dir or Path.home() / ".local" / "share" / "mission-control-agent"
        )
        self._interactions_path = self._data_dir / "network_ai_interactions.jsonl"
        self._config: dict[str, Any] = {
            "enabled": True,
            "retention_days": 90,
        }
        self._initialized = False

    async def initialize(self, context: dict[str, Any]) -> bool:
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._initialized = True
        logger.info("Network AI plugin initialized")
        return True

    async def shutdown(self) -> None:
        self._initialized = False

    async def collect_inventory(self) -> dict[str, Any]:
        return {
            "plugin": self.name,
            "version": self.version,
            "enabled": self._config.get("enabled", True),
            "interactions_total": self._count_interactions(),
        }

    async def execute_command(
        self, command: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        if command == "ask":
            return await self._handle_ask(args)
        if command == "status":
            return self._handle_status()
        if command == "clear":
            return self._handle_clear(args)
        return {"error": f"Unknown command: {command}"}

    async def _handle_ask(self, args: dict[str, Any]) -> dict[str, Any]:
        question = (args.get("question") or "").strip()
        context_plugins = args.get("context_plugins", [])
        if not question:
            return {"error": "question is required"}

        timestamp = datetime.now(UTC).isoformat()
        context = self._build_context(plugin_names=context_plugins)

        # Build payload for server-side AI
        payload = {
            "question": question,
            "context": context,
            "timestamp": timestamp,
        }

        # Try server-side AI endpoint via existing client
        try:
            # We don't have config here; best-effort using env
            server_url = os.environ.get("MC_SERVER_URL", "").rstrip("/")
            api_key = os.environ.get("MC_API_KEY", "")
            agent_id = os.environ.get("MC_AGENT_ID", "")
            if not server_url or not api_key or not agent_id:
                logger.debug("Missing server URL/API key/agent ID for AI ask")
                return self._local_fallback(question, context)

            import httpx

            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.post(
                    f"{server_url}/api/v1/edge/{agent_id}/ai/ask",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                )
            if response.status_code == 200:
                data = response.json()
                answer = data.get("answer") or data.get("response") or ""
                if answer:
                    result = {
                        "question": question,
                        "timestamp": timestamp,
                        "answer": answer,
                        "confidence": data.get("confidence", "high"),
                        "sources": ["server_ai"],
                    }
                    if data.get("learned"):
                        result["sources"].append("server_learned")
                    self._log_interaction(question, result)
                    return result
        except Exception as e:
            logger.debug("Server AI ask failed: %s", e)

        return self._local_fallback(question, context)

    def _local_fallback(self, question: str, context: dict[str, Any]) -> dict[str, Any]:
        answer = (
            "I couldn't reach the server-side assistant right now. "
            "Local context is available, but AI answers require connectivity to Mission Control."
        )
        result = {
            "question": question,
            "timestamp": datetime.now(UTC).isoformat(),
            "answer": answer,
            "confidence": "low",
            "sources": ["local_fallback"],
        }
        self._log_interaction(question, result)
        return result

    def _handle_status(self) -> dict[str, Any]:
        return {
            "plugin": self.name,
            "version": self.version,
            "initialized": self._initialized,
            "interactions_total": self._count_interactions(),
        }

    def _handle_clear(self, args: dict[str, Any]) -> dict[str, Any]:
        target = args.get("target", "all")
        if target in ("all", "interactions") and self._interactions_path.exists():
            self._interactions_path.unlink()
        return {"status": "cleared", "target": target}

    def _build_context(self, plugin_names: list[str] | None = None) -> dict[str, Any]:
        context: dict[str, Any] = {
            "hostname": socket.gethostname(),
            "platform": platform.system(),
            "plugins_requested": plugin_names or [],
        }
        try:
            import psutil

            context["cpu_percent"] = psutil.cpu_percent(interval=0.1)
            context["memory_percent"] = psutil.virtual_memory().percent
        except Exception:
            pass
        return context

    def _log_interaction(self, question: str, response: dict[str, Any]) -> None:
        try:
            line = json.dumps(
                {
                    "question": question,
                    "answer": response.get("answer"),
                    "confidence": response.get("confidence"),
                    "sources": response.get("sources"),
                    "timestamp": response.get("timestamp"),
                }
            )
            with open(self._interactions_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception as e:
            logger.debug("Failed to log interaction: %s", e)

    def _count_interactions(self) -> int:
        if not self._interactions_path.exists():
            return 0
        try:
            return sum(1 for _ in open(self._interactions_path, encoding="utf-8"))
        except Exception:
            return 0
