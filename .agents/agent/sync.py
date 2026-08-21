"""Mission Control Edge Agent - Cloud sync module.

Handles pull-based config sync and data export to the GCE backend.
All operations are best-effort and offline-safe.
"""

from __future__ import annotations

import gzip
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

from .storage import (
    EdgeStorage,
    HeartbeatRecord,
    InventoryRecord,
)

logger = logging.getLogger(__name__)


class SyncResult:
    """Result of a sync operation."""

    def __init__(self, direction: str, success: bool, status_code: int = 0,
                 bytes_in: int = 0, bytes_out: int = 0, error: str = "", restart_requested: bool = False):
        self.direction = direction
        self.success = success
        self.status_code = status_code
        self.bytes_in = bytes_in
        self.bytes_out = bytes_out
        self.error = error
        self.restart_requested = restart_requested
        self.timestamp = datetime.now(UTC).isoformat()


class EdgeSync:
    """Pull-based config sync + data push for the edge agent."""

    def __init__(self, storage: EdgeStorage, base_url: str, api_key: str, agent_id: int, verify_ssl: bool = True, bundle_path: Path | None = None):
        self._storage = storage
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._agent_id = agent_id
        self._last_pull_attempt: str | None = None
        self._client = httpx.Client(
            timeout=httpx.Timeout(30.0, connect=10.0),
            verify=verify_ssl,
        )
        if api_key:
            self._client.headers["X-Agent-API-Key"] = api_key
        self._bundle_path = bundle_path or (Path.cwd() / "agent-bundle-live.zip")

    def close(self) -> None:
        """Close the HTTP client."""
        try:  # noqa: SIM105
            self._client.close()
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    # Config pull
    # ------------------------------------------------------------------ #

    def pull_config(self) -> SyncResult:
        """Pull configuration from the cloud. Non-fatal if offline."""
        endpoint = f"{self._base_url}/api/v1/edge/{self._agent_id}/config"
        try:
            response = self._client.get(endpoint)
            status = response.status_code
            if status == 200:
                payload = response.json()
                manifest = self._parse_manifest(payload)
                self._storage.save_manifest(manifest)
                self._last_pull_attempt = datetime.now(UTC).isoformat()
                self._storage.log_sync(
                    "pull-config", endpoint, status,
                    bytes_in=len(response.content),
                )
                logger.info("Config pulled: version=%s", manifest.config_version)
                return SyncResult("pull-config", True, status, len(response.content), 0)
            if status == 404:
                logger.warning("Config endpoint not found; edge not registered?")
                self._storage.log_sync("pull-config", endpoint, status, error="not found")
                return SyncResult("pull-config", False, status, 0, 0, "not found")
            if status == 401:
                logger.error("Config pull unauthorized; check API key")
                self._storage.log_sync("pull-config", endpoint, status, error="unauthorized")
                return SyncResult("pull-config", False, status, 0, 0, "unauthorized")
            logger.warning("Config pull unexpected status=%s", status)
            self._storage.log_sync("pull-config", endpoint, status, error=f"unexpected {status}")
            return SyncResult("pull-config", False, status)
        except Exception as e:
            error_msg = str(e)
            logger.debug("Config pull failed: %s", error_msg)
            self._storage.log_sync("pull-config", endpoint, 0, error=error_msg)
            return SyncResult("pull-config", False, 0, 0, 0, error_msg)

    def pull_bundle(self, bundle_path: Path) -> SyncResult:
        """Pull latest agent bundle ZIP from the server."""
        endpoint = f"{self._base_url}/api/v1/edge/{self._agent_id}/bundle/download"
        try:
            response = self._client.post(endpoint)
            status = response.status_code
            if status == 200:
                bundle_path = Path(bundle_path)
                bundle_path.parent.mkdir(parents=True, exist_ok=True)
                remote_version = response.headers.get("X-Agent-Bundle-Version", "")
                current_version = ""
                version_path = bundle_path.with_suffix(".version")
                if version_path.exists():
                    current_version = version_path.read_text(encoding="utf-8").strip()
                if remote_version and remote_version == current_version:
                    logger.debug("Bundle version unchanged: %s", remote_version)
                    return SyncResult("pull-bundle", True, status, 0, 0)
                tmp_path = bundle_path.with_suffix(".tmp")
                tmp_path.write_bytes(response.content)
                tmp_path.replace(bundle_path)
                if remote_version:
                    version_path.write_text(remote_version, encoding="utf-8")
                logger.info(
                    "Bundle pulled: %s bytes, version=%s",
                    len(response.content),
                    remote_version or "unknown",
                )
                extracted = self._extract_bundle(bundle_path)
                return SyncResult(
                    "pull-bundle", True, status, len(response.content), 0,
                    restart_requested=extracted,
                )
            logger.warning("Bundle pull unexpected status=%s", status)
            return SyncResult("pull-bundle", False, status, 0, 0, f"HTTP {status}")
        except Exception as e:
            error_msg = str(e)
            logger.debug("Bundle pull failed: %s", error_msg)
            return SyncResult("pull-bundle", False, 0, 0, 0, error_msg)

    def _extract_bundle(self, bundle_path: Path) -> bool:
        """Extract bundle ZIP to the agent package directory."""
        try:
            import zipfile

            extract_root = bundle_path.parent
            logger.info("Extracting bundle to %s", extract_root)
            with zipfile.ZipFile(bundle_path, "r") as zf:
                for member in zf.namelist():
                    if member.endswith("/"):
                        continue
                    target = extract_root / member
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(zf.read(member))
            logger.info("Bundle extracted successfully")
            return True
        except Exception as e:
            logger.error("Bundle extraction failed: %s", e)
            return False
    def _parse_manifest(self, payload: dict[str, Any]) -> Any:
        """Parse cloud payload into a ConfigManifest."""
        from .storage import ConfigManifest
        return ConfigManifest(
            config_version=int(payload.get("config_version", 1)),
            agent_id=int(payload.get("agent_id", self._agent_id)),
            last_modified=payload.get("last_modified", ""),
            config=payload.get("config", {}),
            plugins=payload.get("plugins", []),
            remote_targets=payload.get("remote_targets", []),
            integration_profiles=payload.get("integration_profiles", []),
            pulled_at=datetime.now(UTC).isoformat(),
            applied=False,
        )

    # ------------------------------------------------------------------ #
    # Data push
    # ------------------------------------------------------------------ #

    def push_inventory(self, limit: int = 100) -> SyncResult:
        """Push pending inventory records to the cloud."""
        endpoint = f"{self._base_url}/api/v1/edge/{self._agent_id}/inventory"
        records = self._storage.get_unpushed_inventory(limit)
        if not records:
            return SyncResult("push-inventory", True, 0, 0, 0)

        plugins: dict[str, Any] = {}
        for r in records:
            plugins.setdefault(r.plugin_name, {}).update(r.data if isinstance(r.data, dict) else {"value": str(r.data)})
        payload = {
            "agent_id": self._agent_id,
            "plugins": plugins,
            "records": [self._serialize_inventory(r) for r in records],
        }
        compressed = gzip.compress(json.dumps(payload).encode("utf-8"))
        try:
            response = self._client.post(
                endpoint,
                content=compressed,
                headers={"Content-Encoding": "gzip"},
            )
            status = response.status_code
            success = status == 200
            if success:
                for r in records:
                    self._storage.mark_inventory_pushed(r.id or 0)
                logger.info("Pushed %s inventory records", len(records))
            else:
                logger.warning("Inventory push failed: %s", status)
            self._storage.log_sync(
                "push-inventory", endpoint, status,
                bytes_in=len(compressed),
                bytes_out=len(response.content),
                error="" if success else f"status {status}",
            )
            return SyncResult(
                "push-inventory", success, status,
                len(compressed), len(response.content),
                "" if success else f"status {status}",
            )
        except Exception as e:
            error_msg = str(e)
            logger.debug("Inventory push failed: %s", error_msg)
            self._storage.log_sync("push-inventory", endpoint, 0, error=error_msg)
            return SyncResult("push-inventory", False, 0, len(compressed), 0, error_msg)

    def push_heartbeat(self, record: HeartbeatRecord) -> SyncResult:
        """Push a single heartbeat record."""
        endpoint = f"{self._base_url}/api/v1/edge/{self._agent_id}/heartbeat"
        payload = {
            "agent_id": record.agent_id,
            "status": record.status,
            "latency_ms": record.latency_ms,
            "timestamp": datetime.now(UTC).isoformat(),
            "error": record.error,
            "active_plugins": record.active_plugins,
            "health": record.health,
            "cpu_percent": record.cpu_percent,
            "memory_percent": record.memory_percent,
            "disk_percent": record.disk_percent,
            "agent_version": record.agent_version,
        }
        try:
            response = self._client.post(endpoint, json=payload)
            status = response.status_code
            success = status == 200
            self._storage.log_sync(
                "push-heartbeat", endpoint, status,
                bytes_in=len(json.dumps(payload).encode("utf-8")),
                bytes_out=len(response.content),
            )
            return SyncResult(
                "push-heartbeat", success, status,
                len(json.dumps(payload).encode("utf-8")),
                len(response.content),
                "" if success else f"status {status}",
            )
        except Exception as e:
            error_msg = str(e)
            self._storage.log_sync("push-heartbeat", endpoint, 0, error=error_msg)
            return SyncResult("push-heartbeat", False, 0, 0, 0, error_msg)

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _serialize_inventory(self, record: InventoryRecord) -> dict[str, Any]:
        """Serialize an inventory record for the cloud."""
        return {
            "id": record.id,
            "plugin_name": record.plugin_name,
            "data": record.data,
            "checksum": record.checksum,
            "collected_at": record.collected_at,
        }

    # ------------------------------------------------------------------ #
    # Command pull (server -> edge agent)
    # ------------------------------------------------------------------ #

    def pull_commands(self) -> list[dict[str, Any]]:
        """Pull pending commands for this edge agent. Returns [] when none."""
        endpoint = f"{self._base_url}/api/v1/edge/{self._agent_id}/commands"
        try:
            response = self._client.get(endpoint)
            status = response.status_code
            if status == 200:
                payload = response.json()
                commands = payload.get("commands") or []
                self._storage.log_sync(
                    "pull-commands", endpoint, status,
                    bytes_in=len(response.content),
                )
                if commands:
                    logger.info("Pulled %d edge command(s)", len(commands))
                return [c for c in commands if isinstance(c, dict)]
            if status == 404:
                logger.debug("Edge commands endpoint not found (old server)")
                return []
            logger.warning("Edge commands pull unexpected status=%s", status)
            return []
        except Exception as e:
            logger.debug("Edge commands pull failed: %s", e)
            self._storage.log_sync("pull-commands", endpoint, 0, error=str(e))
            return []

    def push_command_result(self, command_id: int, result: dict[str, Any]) -> SyncResult:
        """Report a command execution result back to the server."""
        endpoint = f"{self._base_url}/api/v1/edge/{self._agent_id}/command-result"
        payload = {
            "command_id": command_id,
            "success": bool(result.get("success")),
            "exit_code": result.get("exit_code"),
            "stdout": result.get("stdout"),
            "stderr": result.get("stderr"),
            "duration_ms": result.get("duration_ms"),
            "error_message": result.get("error_message") or result.get("error"),
        }
        try:
            response = self._client.post(endpoint, json=payload)
            status = response.status_code
            success = status == 200
            self._storage.log_sync(
                "push-command-result", endpoint, status,
                bytes_in=len(json.dumps(payload).encode("utf-8")),
                bytes_out=len(response.content),
                error="" if success else f"status {status}",
            )
            if success:
                logger.info("Command %s result pushed", command_id)
            else:
                logger.warning("Command %s result push failed: %s", command_id, status)
            return SyncResult(
                "push-command-result", success, status,
                len(json.dumps(payload).encode("utf-8")),
                len(response.content),
                "" if success else f"status {status}",
            )
        except Exception as e:
            logger.debug("Command %s result push error: %s", command_id, e)
            self._storage.log_sync("push-command-result", endpoint, 0, error=str(e))
            return SyncResult("push-command-result", False, 0, error=str(e))

    def run_sync_cycle(self) -> dict[str, SyncResult]:
        """Run one full sync cycle: config pull, bundle pull, then data push."""
        results: dict[str, SyncResult] = {}
        results["config"] = self.pull_config()
        results["bundle"] = self.pull_bundle(self._bundle_path)
        results["inventory"] = self.push_inventory()
        return results
