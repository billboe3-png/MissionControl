"""Mission Control Edge Agent - Local SQLite persistence.

Thread-safe local storage with WAL mode. All edge data is written
locally first, then synced to the cloud when online.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import threading
from dataclasses import dataclass, field
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class StorageConfig:
    """Configuration for local SQLite storage."""
    db_path: Path
    wal: bool = True
    journal_mode: str = "WAL"
    busy_timeout_ms: int = 5000


@dataclass
class ConfigManifest:
    """Cloud-pushed configuration manifest."""
    id: int = 1
    config_version: int = 1
    agent_id: int = 0
    last_modified: str = ""
    config: dict[str, Any] = field(default_factory=dict)
    plugins: list[dict[str, Any]] = field(default_factory=list)
    remote_targets: list[dict[str, Any]] = field(default_factory=list)
    integration_profiles: list[dict[str, Any]] = field(default_factory=list)
    pulled_at: str = ""
    applied: bool = False


@dataclass
class PluginRecord:
    """Local plugin execution record."""
    id: int | None = None
    plugin_name: str = ""
    status: str = "pending"
    output: str = ""
    error: str = ""
    started_at: str = ""
    finished_at: str = ""
    duration_ms: float = 0.0
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class InventoryRecord:
    """Local inventory snapshot."""
    id: int | None = None
    plugin_name: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    checksum: str = ""
    collected_at: str = ""
    pushed: bool = False


@dataclass
class HeartbeatRecord:
    """Local heartbeat log."""
    id: int | None = None
    agent_id: int = 0
    status: str = "online"
    latency_ms: float = 0.0
    pushed_at: str = ""
    error: str = ""


class EdgeStorage:
    """Thread-safe SQLite persistence for the edge agent."""

    def __init__(self, config: StorageConfig):
        self._config = config
        self._config.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._lock = threading.Lock()
        self._initialize_schema()

    def _get_connection(self) -> sqlite3.Connection:
        """Get or create a thread-local connection."""
        if not hasattr(self._local, "conn") or self._local.conn is None:
            conn = sqlite3.connect(
                str(self._config.db_path),
                check_same_thread=False,
                timeout=self._config.busy_timeout_ms / 1000.0,
            )
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=5000")
            conn.execute("PRAGMA synchronous=NORMAL")
            self._local.conn = conn
        return self._local.conn

    def close(self) -> None:
        """Close the current thread's connection."""
        if hasattr(self._local, "conn") and self._local.conn is not None:
            try:
                self._local.conn.close()
            except Exception:
                pass
            self._local.conn = None

    def _initialize_schema(self) -> None:
        """Create tables if they don't exist."""
        with self._lock:
            conn = self._get_connection()
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS config_manifest (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    config_version INTEGER NOT NULL DEFAULT 1,
                    agent_id INTEGER NOT NULL,
                    last_modified TEXT,
                    config TEXT,
                    plugins TEXT,
                    remote_targets TEXT,
                    integration_profiles TEXT,
                    pulled_at TEXT,
                    applied BOOLEAN DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS plugin_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plugin_name TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    output TEXT DEFAULT '',
                    error TEXT DEFAULT '',
                    started_at TEXT,
                    finished_at TEXT,
                    duration_ms REAL DEFAULT 0.0,
                    meta TEXT DEFAULT '{}'
                );

                CREATE TABLE IF NOT EXISTS inventory_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plugin_name TEXT NOT NULL,
                    data TEXT NOT NULL,
                    checksum TEXT DEFAULT '',
                    collected_at TEXT NOT NULL,
                    pushed BOOLEAN DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS heartbeat_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'online',
                    latency_ms REAL DEFAULT 0.0,
                    pushed_at TEXT,
                    error TEXT DEFAULT ''
                );

                CREATE TABLE IF NOT EXISTS sync_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    direction TEXT NOT NULL,
                    endpoint TEXT,
                    status_code INTEGER,
                    bytes_in INTEGER DEFAULT 0,
                    bytes_out INTEGER DEFAULT 0,
                    error TEXT DEFAULT '',
                    timestamp TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS plugin_files (
                    plugin_name TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    version TEXT DEFAULT '',
                    checksum TEXT DEFAULT '',
                    installed_at TEXT,
                    active BOOLEAN DEFAULT 1
                );

                CREATE INDEX IF NOT EXISTS idx_inventory_pushed ON inventory_records(pushed);
                CREATE INDEX IF NOT EXISTS idx_inventory_plugin ON inventory_records(plugin_name);
                CREATE INDEX IF NOT EXISTS idx_heartbeat_agent ON heartbeat_records(agent_id);
                CREATE INDEX IF NOT EXISTS idx_sync_timestamp ON sync_log(timestamp);
                """
            )
            conn.commit()

    # ------------------------------------------------------------------ #
    # Config manifest
    # ------------------------------------------------------------------ #

    def save_manifest(self, manifest: ConfigManifest) -> None:
        """Save or update the configuration manifest."""
        with self._lock:
            conn = self._get_connection()
            conn.execute(
                """
                INSERT INTO config_manifest (id, config_version, agent_id, last_modified,
                    config, plugins, remote_targets, integration_profiles,
                    pulled_at, applied)
                VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    config_version=excluded.config_version,
                    last_modified=excluded.last_modified,
                    config=excluded.config,
                    plugins=excluded.plugins,
                    remote_targets=excluded.remote_targets,
                    integration_profiles=excluded.integration_profiles,
                    pulled_at=excluded.pulled_at,
                    applied=excluded.applied
                """,
                (
                    manifest.config_version,
                    manifest.agent_id,
                    manifest.last_modified,
                    json.dumps(manifest.config),
                    json.dumps(manifest.plugins),
                    json.dumps(manifest.remote_targets),
                    json.dumps(manifest.integration_profiles),
                    manifest.pulled_at,
                    manifest.applied,
                ),
            )
            conn.commit()

    def get_manifest(self) -> ConfigManifest | None:
        """Load the current manifest."""
        with self._lock:
            conn = self._get_connection()
            row = conn.execute("SELECT * FROM config_manifest WHERE id=1").fetchone()
            if not row:
                return None
            return ConfigManifest(
                id=row["id"],
                config_version=row["config_version"],
                agent_id=row["agent_id"],
                last_modified=row["last_modified"] or "",
                config=json.loads(row["config"] or "{}"),
                plugins=json.loads(row["plugins"] or "[]"),
                remote_targets=json.loads(row["remote_targets"] or "[]"),
                integration_profiles=json.loads(row["integration_profiles"] or "[]"),
                pulled_at=row["pulled_at"] or "",
                applied=bool(row["applied"]),
            )

    # ------------------------------------------------------------------ #
    # Plugin files
    # ------------------------------------------------------------------ #

    def save_plugin_file(self, plugin_name: str, content: str, version: str = "", checksum: str = "") -> None:
        """Save or update a plugin source file."""
        with self._lock:
            conn = self._get_connection()
            conn.execute(
                """
                INSERT INTO plugin_files (plugin_name, content, version, checksum, installed_at, active)
                VALUES (?, ?, ?, ?, ?, 1)
                ON CONFLICT(plugin_name) DO UPDATE SET
                    content=excluded.content,
                    version=excluded.version,
                    checksum=excluded.checksum,
                    installed_at=excluded.installed_at,
                    active=1
                """,
                (plugin_name, content, version, checksum, datetime.now(UTC).isoformat()),
            )
            conn.commit()

    def get_plugin_file(self, plugin_name: str) -> str | None:
        """Get plugin source content."""
        with self._lock:
            conn = self._get_connection()
            row = conn.execute(
                "SELECT content FROM plugin_files WHERE plugin_name=? AND active=1",
                (plugin_name,),
            ).fetchone()
            return row["content"] if row else None

    def list_plugins(self) -> list[str]:
        """List active plugin names."""
        with self._lock:
            conn = self._get_connection()
            rows = conn.execute("SELECT plugin_name FROM plugin_files WHERE active=1").fetchall()
            return [r["plugin_name"] for r in rows]

    # ------------------------------------------------------------------ #
    # Plugin execution records
    # ------------------------------------------------------------------ #

    def append_plugin_record(self, record: PluginRecord) -> int:
        """Append a plugin execution record."""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.execute(
                """
                INSERT INTO plugin_records (plugin_name, status, output, error,
                    started_at, finished_at, duration_ms, meta)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.plugin_name,
                    record.status,
                    record.output,
                    record.error,
                    record.started_at,
                    record.finished_at,
                    record.duration_ms,
                    json.dumps(record.meta),
                ),
            )
            conn.commit()
            return int(cursor.lastrowid)

    # ------------------------------------------------------------------ #
    # Inventory
    # ------------------------------------------------------------------ #

    def append_inventory(self, record: InventoryRecord) -> int:
        """Append an inventory snapshot."""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.execute(
                """
                INSERT INTO inventory_records (plugin_name, data, checksum,
                    collected_at, pushed)
                VALUES (?, ?, ?, ?, 0)
                """,
                (
                    record.plugin_name,
                    json.dumps(record.data),
                    record.checksum,
                    record.collected_at,
                ),
            )
            conn.commit()
            return int(cursor.lastrowid)

    def get_unpushed_inventory(self, limit: int = 100) -> list[InventoryRecord]:
        """Get inventory records not yet pushed to cloud."""
        with self._lock:
            conn = self._get_connection()
            rows = conn.execute(
                "SELECT * FROM inventory_records WHERE pushed=0 ORDER BY id LIMIT ?",
                (limit,),
            ).fetchall()
            return [
                InventoryRecord(
                    id=r["id"],
                    plugin_name=r["plugin_name"],
                    data=json.loads(r["data"]),
                    checksum=r["checksum"],
                    collected_at=r["collected_at"],
                    pushed=bool(r["pushed"]),
                )
                for r in rows
            ]

    def mark_inventory_pushed(self, record_id: int) -> None:
        """Mark an inventory record as pushed."""
        with self._lock:
            conn = self._get_connection()
            conn.execute("UPDATE inventory_records SET pushed=1 WHERE id=?", (record_id,))
            conn.commit()

    # ------------------------------------------------------------------ #
    # Heartbeat log
    # ------------------------------------------------------------------ #

    def append_heartbeat(self, record: HeartbeatRecord) -> int:
        """Append a heartbeat record."""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.execute(
                """
                INSERT INTO heartbeat_records (agent_id, status, latency_ms, pushed_at, error)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    record.agent_id,
                    record.status,
                    record.latency_ms,
                    record.pushed_at,
                    record.error,
                ),
            )
            conn.commit()
            return int(cursor.lastrowid)

    # ------------------------------------------------------------------ #
    # Sync log
    # ------------------------------------------------------------------ #

    def log_sync(self, direction: str, endpoint: str, status_code: int = 0,
                 bytes_in: int = 0, bytes_out: int = 0, error: str = "") -> None:
        """Log a sync operation."""
        with self._lock:
            conn = self._get_connection()
            conn.execute(
                """
                INSERT INTO sync_log (direction, endpoint, status_code,
                    bytes_in, bytes_out, error, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    direction,
                    endpoint,
                    status_code,
                    bytes_in,
                    bytes_out,
                    error,
                    datetime.now(UTC).isoformat(),
                ),
            )
            conn.commit()

    # ------------------------------------------------------------------ #
    # Utilities
    # ------------------------------------------------------------------ #

    def get_stats(self) -> dict[str, int]:
        """Get basic storage stats."""
        with self._lock:
            conn = self._get_connection()
            stats: dict[str, int] = {}
            for table in ["plugin_records", "inventory_records", "heartbeat_records", "sync_log"]:
                row = conn.execute(f"SELECT COUNT(*) as n FROM {table}").fetchone()
                stats[table] = row["n"]
            return stats

    def vacuum(self) -> None:
        """Vacuum the database to reclaim space."""
        with self._lock:
            conn = self._get_connection()
            conn.execute("VACUUM")
            conn.commit()
