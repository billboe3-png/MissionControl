"""Business logic for the MikroTik plugin.

Connects to RouterOS devices over SSH, Telnet, or the REST API,
executes commands with audit logging and credential decryption,
caches facts/status, and runs background sync. Routes stay thin.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import re
import time
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import CredentialCipher
from app.events import Event, EventType, event_bus
from app.plugins.installed.official_mikrotik.connector import (
    ConnectorConfig,
    SshConnector,
    SwitchConnectorError,
    TelnetConnector,
    WebUiConnector,
)
from app.plugins.installed.official_mikrotik.models import MikroTikServer
from app.plugins.installed.official_mikrotik.relay import relay_executor
from app.plugins.installed.official_mikrotik.repository import MikroTikRepository
from app.plugins.installed.official_mikrotik.service_types import CommandResult

logger = logging.getLogger("plugin.mikrotik.service")

CONNECTOR_TYPES = ("ssh", "telnet", "rest")

RELAY_CONNECTOR_TYPE = "relay"


def _cipher() -> CredentialCipher:
    return CredentialCipher(get_settings().missioncontrol_secret_key)


def encrypt_password(plaintext: str | None) -> str | None:
    if not plaintext:
        return None
    return _cipher().encrypt(plaintext)


def decrypt_password(token: str | None) -> str:
    if not token:
        return ""
    try:
        return _cipher().decrypt(token)
    except Exception:
        logger.exception("Failed to decrypt MikroTik credentials for server id=%s", getattr(token, "id", "?"))
        return ""


class MikroTikService:
    """Connection, execution, testing, and sync orchestration."""

    def __init__(self, repository: MikroTikRepository | None = None) -> None:
        self._repository = repository or MikroTikRepository()

    # ------------------------------------------------------------------ #
    # Connector factory                                                   #
    # ------------------------------------------------------------------ #

    @staticmethod
    def resolve_connector_type(server: MikroTikServer, connector_type: str | None = None) -> str:
        if server.relay_agent_id:
            return RELAY_CONNECTOR_TYPE
        if connector_type:
            chosen = connector_type.lower()
            if chosen not in CONNECTOR_TYPES:
                raise ValueError(f"Unknown connector type '{chosen}'")
            return chosen
        if server.api_enabled:
            return "rest"
        if server.telnet_enabled:
            return "telnet"
        return "ssh"

    @staticmethod
    def build_connector(
        server: MikroTikServer, connector_type: str | None = None
    ) -> WebUiConnector | SshConnector | TelnetConnector:
        """Instantiate a configured connector for a server (not connected)."""
        chosen = MikroTikService.resolve_connector_type(server, connector_type)
        if chosen == RELAY_CONNECTOR_TYPE:
            raise SwitchConnectorError(
                "This server executes through a relay agent; "
                "no direct connector is available"
            )
        password = decrypt_password(server.password_encrypted)

        config = ConnectorConfig(
            host=server.host,
            username=server.username,
            password=password,
            timeout=30,
        )

        if chosen == "ssh":
            config.port = server.ssh_port or 22
            return SshConnector(config)
        if chosen == "telnet":
            config.port = server.telnet_port or 23
            return TelnetConnector(config)
        config.port = server.api_port or 443
        return WebUiConnector(config)

    # ------------------------------------------------------------------ #
    # Command execution                                                   #
    # ------------------------------------------------------------------ #

    async def run_command(
        self,
        db: Session,
        server: MikroTikServer,
        command: str,
        executed_by: str | None = None,
        connector_type: str | None = None,
    ) -> CommandResult:
        """Connect, execute one command, write the audit log, update status.

        Servers with a relay agent configured are reached through the
        agent's SSH connector instead of a local connection.
        """
        started = time.monotonic()
        result = CommandResult(success=False)
        if server.relay_agent_id:
            used_type = RELAY_CONNECTOR_TYPE
            relay_result = await relay_executor.execute_via_agent(
                db, server, command, executed_by=executed_by
            )
            result.success = relay_result.success
            result.output = relay_result.output
            result.error = relay_result.error
            if result.success:
                if server.status != "online":
                    await self._publish_state(server, "online")
                server.status = "online"
                server.last_error = None
                server.last_sync_at = datetime.now(UTC)
                self._update_cached_facts(db, server, used_type, command, result.output)
            else:
                previous = server.status
                server.status = "unreachable"
                lowered_error = result.error.lower()
                if "authentication" in lowered_error or "auth" in lowered_error:
                    server.status = "auth_failed"
                server.last_error = result.error[:500]
                if previous != server.status and server.status in ("unreachable", "auth_failed"):
                    await self._publish_state(server, "offline")
            result.duration_ms = int((time.monotonic() - started) * 1000)
            db.commit()
            self._repository.add_command_log(
                db,
                server_id=server.id,
                connector_type=used_type,
                command=command,
                output=result.output[:20000] if result.success else None,
                success=result.success,
                error=result.error[:2000] or None,
                duration_ms=result.duration_ms,
                executed_by=executed_by,
            )
            db.commit()
            return result

        used_type = self.resolve_connector_type(server, connector_type)
        connector = None
        try:
            connector = await asyncio.to_thread(self.build_connector, server, connector_type)
            await asyncio.to_thread(connector.connect)
            output = await asyncio.to_thread(connector.execute, command)
            result.success = True
            result.output = output

            if server.status != "online":
                await self._publish_state(server, "online")
            server.status = "online"
            server.last_error = None
            server.last_sync_at = datetime.now(UTC)
            self._update_cached_facts(db, server, used_type, command, output)
            db.commit()
        except SwitchConnectorError as exc:
            result.error = str(exc)
            previous = server.status
            server.status = "unreachable"
            if "authentication failed" in str(exc).lower():
                server.status = "auth_failed"
            server.last_error = str(exc)[:500]
            if previous != server.status and server.status in ("unreachable", "auth_failed"):
                await self._publish_state(server, "offline")
            db.commit()
        except Exception as exc:
            result.error = f"{type(exc).__name__}: {exc}"
            server.status = "unreachable"
            server.last_error = result.error[:500]
            db.commit()
            logger.exception("Unexpected error executing command on server id=%s", server.id)
        finally:
            result.duration_ms = int((time.monotonic() - started) * 1000)
            if connector is not None:
                with contextlib.suppress(Exception):
                    await asyncio.to_thread(connector.disconnect)

        self._repository.add_command_log(
            db,
            server_id=server.id,
            connector_type=used_type,
            command=command,
            output=result.output[:20000] if result.success else None,
            success=result.success,
            error=result.error[:2000] or None,
            duration_ms=result.duration_ms,
            executed_by=executed_by,
        )
        db.commit()
        return result

    # ------------------------------------------------------------------ #
    # Testing                                                             #
    # ------------------------------------------------------------------ #

    async def test_server(self, db: Session, server: MikroTikServer) -> dict[str, object]:
        """Attempt connection + resource fetch; returns the /test contract."""
        result: dict[str, object] = {
            "connected": False,
            "version": "",
            "name": server.name,
            "server_id": server.id,
        }
        resource = await self.run_command(db, server, "/system resource print")
        result["connector_used"] = self.resolve_connector_type(server)
        if not resource.success:
            result["error"] = resource.error
            return result

        info = self._parse_resource_output(resource.output)
        version = str(info.get("version") or "")
        result["connected"] = True
        result["version"] = version
        return result

    # ------------------------------------------------------------------ #
    # Live data fetchers (REST-first with CLI fallback)                   #
    # ------------------------------------------------------------------ #

    async def fetch_interfaces(self, db: Session, server: MikroTikServer) -> list[dict[str, object]]:
        result = await self.run_command(db, server, "/interface print detail without-paging")
        if not result.success:
            raise SwitchConnectorError(result.error or "interface fetch failed")
        # Static fields (type/mtu/mac) and counters (rx/tx bytes) live in two
        # different print views; merge them by interface name.
        stats = await self.run_command(
            db, server, "/interface print stats-detail without-paging"
        )
        return self._map_interfaces(result, stats if stats.success else None)

    async def fetch_system(self, db: Session, server: MikroTikServer) -> dict[str, object]:
        result = await self.run_command(db, server, "/system resource print")
        if not result.success:
            raise SwitchConnectorError(result.error or "system resource fetch failed")
        return self._parse_resource_output(result.output)

    async def fetch_firewall(self, db: Session, server: MikroTikServer) -> list[dict[str, object]]:
        result = await self.run_command(
            db, server, "/ip firewall filter print detail without-paging"
        )
        return self._map_firewall(result)

    async def fetch_dhcp_leases(self, db: Session, server: MikroTikServer) -> list[dict[str, object]]:
        result = await self.run_command(
            db, server, "/ip dhcp-server lease print detail without-paging"
        )
        return self._map_dhcp(result)

    # ------------------------------------------------------------------ #
    # Background sync                                                     #
    # ------------------------------------------------------------------ #

    async def sync_all(self, db: Session) -> dict[str, int]:
        """Light-weight status/facts refresh for every enabled server."""
        from app.plugins.installed.official_mikrotik.cache import cache_manager

        servers = self._repository.list_servers(db, enabled_only=True)
        summary = {"total": len(servers), "online": 0, "offline": 0}
        for server in servers:
            result = await self.run_command(db, server, "/system resource print")
            if result.success:
                summary["online"] += 1
                # Keep the interface cache warm so dashboards always have
                # data even if a browser fetch raced a restart.
                try:
                    rows = await self.fetch_interfaces(db, server)
                    cache_manager.replace_interfaces(db, server.id, rows)
                except Exception:
                    logger.warning(
                        "Interface cache refresh failed for %s", server.name, exc_info=True
                    )
                # The background sync loop closes its session without
                # committing; persist facts/status explicitly.
                db.commit()
            else:
                summary["offline"] += 1
        logger.info(
            "MikroTik sync cycle complete: %d server(s), %d online",
            summary["total"],
            summary["online"],
        )
        return summary

    # ------------------------------------------------------------------ #
    # Output mapping                                                      #
    # ------------------------------------------------------------------ #

    def _map_interfaces(
        self, result: CommandResult, stats: CommandResult | None = None
    ) -> list[dict[str, object]]:
        if not result.success:
            raise SwitchConnectorError(result.error or "interface fetch failed")
        if result.output.lstrip().startswith("["):
            parsed = json.loads(result.output)
            rows = parsed if isinstance(parsed, list) else []
            mapped: list[dict[str, object]] = []
            for item in rows:
                running = str(item.get("running", "")).lower() == "true"
                mapped.append(
                    {
                        "name": item.get("name", ""),
                        "type": item.get("type"),
                        "status": "running" if running else "down",
                        "link_status": "link-ok" if running else "none",
                        "rx_bytes": int(item.get("rx-byte") or 0),
                        "tx_bytes": int(item.get("tx-byte") or 0),
                        "rx_packets": int(item.get("rx-packet") or 0),
                        "tx_packets": int(item.get("tx-packet") or 0),
                        "mac": item.get("mac-address"),
                        "mtu": int(item["actual-mtu"]) if item.get("actual-mtu") else None,
                    }
                )
            return mapped
        records_by_name: dict[str, dict[str, str]] = {}
        for record in self._parse_key_value_output(result.output):
            name = record.get("name", "")
            if name:
                records_by_name[name] = record
        if stats is not None:
            for record in self._parse_key_value_output(stats.output):
                name = record.get("name", "")
                if not name:
                    continue
                existing = records_by_name.get(name)
                if existing is None:
                    records_by_name[name] = record
                else:
                    merged_flags = set(existing.get("_flags", "")) | set(record.get("_flags", ""))
                    existing.update(record)
                    existing["_flags"] = "".join(sorted(merged_flags))
        mapped = []
        for record in records_by_name.values():
            flags = record.get("_flags", "")
            running = "R" in flags or record.get("running", "").lower() in {"yes", "true"}
            mapped.append(
                {
                    "name": record.get("name", ""),
                    "type": record.get("type"),
                    "status": "running" if running else "down",
                    "link_status": "link-ok" if running else "none",
                    "rx_bytes": self._detail_int(record.get("rx-byte")),
                    "tx_bytes": self._detail_int(record.get("tx-byte")),
                    "rx_packets": self._detail_int(record.get("rx-packet")),
                    "tx_packets": self._detail_int(record.get("tx-packet")),
                    "mac": record.get("mac-address"),
                    "mtu": self._detail_int(record.get("actual-mtu")) or None,
                }
            )
        return mapped

    def _map_firewall(self, result: CommandResult) -> list[dict[str, object]]:
        if not result.success:
            raise SwitchConnectorError(result.error or "firewall fetch failed")
        rows: list[dict[str, object]] = []
        if result.output.lstrip().startswith("["):
            parsed = json.loads(result.output)
            for item in parsed if isinstance(parsed, list) else []:
                rows.append(
                    {
                        "chain": item.get("chain", ""),
                        "action": item.get("action"),
                        "comment": item.get("comment"),
                        "disabled": str(item.get("disabled", "")).lower() == "true"
                        or item.get("disabled") is True,
                        "bytes": int(item.get("bytes") or 0),
                        "packets": int(item.get("packets") or 0),
                    }
                )
            return rows
        for record in self._parse_key_value_output(result.output):
            flags = record.get("_flags", "")
            rows.append(
                {
                    "chain": record.get("chain", ""),
                    "action": record.get("action"),
                    "comment": record.get("comment"),
                    "disabled": "X" in flags or record.get("disabled") == "yes",
                    "bytes": self._detail_int(record.get("bytes")),
                    "packets": self._detail_int(record.get("packets")),
                }
            )
        return rows

    def _map_dhcp(self, result: CommandResult) -> list[dict[str, object]]:
        if not result.success:
            raise SwitchConnectorError(result.error or "dhcp lease fetch failed")
        rows: list[dict[str, object]] = []
        if result.output.lstrip().startswith("["):
            parsed = json.loads(result.output)
            for item in parsed if isinstance(parsed, list) else []:
                rows.append(
                    {
                        "address": item.get("address"),
                        "mac": item.get("mac-address", ""),
                        "host_name": item.get("host-name"),
                        "client_id": item.get("client-id"),
                        "status": item.get("status"),
                        "expires": item.get("expires-after"),
                    }
                )
            return rows
        for record in self._parse_key_value_output(result.output):
            flags = record.get("_flags", "")
            rows.append(
                {
                    "address": record.get("address"),
                    "mac": record.get("mac-address", ""),
                    "host_name": record.get("host-name"),
                    "client_id": record.get("client-id"),
                    "status": (
                        record.get("status")
                        or ("disabled" if "X" in flags else None)
                    ),
                    "expires": record.get("expires-after"),
                }
            )
        return rows

    # ------------------------------------------------------------------ #
    # Helpers                                                             #
    # ------------------------------------------------------------------ #

    _KV_RE = re.compile(r"([A-Za-z0-9_-]+)=(.*?)(?=\s+[A-Za-z0-9_-]+=|$)")

    @staticmethod
    def _detail_int(value: str | None) -> int:
        """RouterOS formats counters with space thousands separators."""
        if not value:
            return 0
        compact = value.replace(" ", "")
        return int(compact) if compact.isdigit() else 0

    @staticmethod
    def _parse_key_value_output(raw: str) -> list[dict[str, str]]:
        """Parse RouterOS ``print detail`` output into flat records.

        Records start on a line whose first token is the entry index;
        long entries wrap across indented continuation lines, and flag
        letters (R/S/X/D...) between the index and the first key=value
        pair are collected under the reserved ``_flags`` key.
        """
        records: list[dict[str, str]] = []
        current: dict[str, str] | None = None

        def apply_kvs(record: dict[str, str], text: str) -> None:
            for match in MikroTikService._KV_RE.finditer(text):
                key = match.group(1)
                value = match.group(2).strip()
                if not value:
                    continue
                if len(value) >= 2 and value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                record[key] = value

        for line in raw.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("Flags:") or stripped.startswith("#"):
                continue
            tokens = stripped.split()
            if re.fullmatch(r"\d+", tokens[0]):
                flags: set[str] = set()
                idx = 1
                while (
                    idx < len(tokens)
                    and "=" not in tokens[idx]
                    and tokens[idx].isalpha()
                    and tokens[idx].isupper()
                ):
                    flags.update(tokens[idx])
                    idx += 1
                current = {"_flags": "".join(sorted(flags))}
                records.append(current)
                apply_kvs(current, " ".join(tokens[idx:]))
            elif current is not None:
                apply_kvs(current, stripped)
        return records

    def _parse_resource_output(self, output: str) -> dict[str, object]:
        """Extract system resource facts from REST JSON or CLI output."""
        try:
            data = json.loads(output)
        except ValueError:
            data = None
        if isinstance(data, dict):
            return {
                "version": data.get("version"),
                "board-name": data.get("board-name"),
                "uptime": data.get("uptime"),
                "cpu-load": str(data.get("cpu-load")) if data.get("cpu-load") is not None else None,
                "memory_usage_pct": self._memory_usage_pct(
                    data.get("free-memory"), data.get("total-memory")
                ),
            }

        records = self._parse_key_value_output(output)
        info = records[0] if records else self._parse_colon_output(output)
        return {
            "version": info.get("version"),
            "board-name": info.get("board-name"),
            "uptime": info.get("uptime"),
            "cpu-load": info.get("cpu-load"),
            "memory_usage_pct": self._memory_usage_pct(
                info.get("free-memory"), info.get("total-memory")
            ),
        }

    @staticmethod
    def _memory_bytes(value: object) -> int | None:
        """Parse a byte count or a human string like '193.3MiB' into bytes."""
        if value is None:
            return None
        text = str(value).strip()
        multipliers = {"KiB": 1024, "MiB": 1024**2, "GiB": 1024**3}
        for unit, multiplier in multipliers.items():
            if text.endswith(unit):
                try:
                    return int(float(text[: -len(unit)]) * multiplier)
                except ValueError:
                    return None
        try:
            return int(float(text))
        except ValueError:
            return None

    def _memory_usage_pct(self, free_raw: object, total_raw: object) -> int | None:
        free_bytes = self._memory_bytes(free_raw)
        total_bytes = self._memory_bytes(total_raw)
        if free_bytes is None or not total_bytes:
            return None
        try:
            return round(100 * (total_bytes - free_bytes) / total_bytes)
        except ZeroDivisionError:
            return None

    @staticmethod
    def _parse_colon_output(raw: str) -> dict[str, str]:
        """Parse 'key: value' lines from RouterOS 'print' output."""
        parsed: dict[str, str] = {}
        for line in raw.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("Flags:"):
                continue
            if ":" in line:
                key, _, value = line.partition(":")
                parsed[key.strip()] = value.strip()
        return parsed

    def _update_cached_facts(
        self, db: Session, server: MikroTikServer, connector_type: str, command: str, output: str
    ) -> None:
        """Best-effort caching of identity/version/board facts from output."""
        lowered_cmd = command.lower()
        if "resource" not in lowered_cmd:
            return
        try:
            info = self._parse_resource_output(output)
            if info.get("version"):
                server.version = str(info["version"])[:50]
            if info.get("board-name"):
                server.board_name = str(info["board-name"])[:100]
            if info.get("uptime"):
                server.uptime = str(info["uptime"])[:100]
            if info.get("cpu-load") is not None:
                server.cpu_load = str(info["cpu-load"])[:20]
            if info.get("memory_usage_pct") is not None:
                server.memory_usage_pct = int(info["memory_usage_pct"])
            db.flush()
        except Exception:
            logger.debug("Could not parse facts from output on server id=%s", server.id)

    async def _publish_state(self, server: MikroTikServer, state: str) -> None:
        event_type = (
            EventType.NETWORK_DEVICE_ONLINE if state == "online" else EventType.NETWORK_DEVICE_OFFLINE
        )
        await event_bus.publish(
            Event(
                type=event_type,
                data={
                    "plugin": "official_mikrotik",
                    "server_id": server.id,
                    "name": server.name,
                    "host": server.host,
                },
                source="mikrotik-plugin",
            )
        )


mikrotik_service = MikroTikService()
