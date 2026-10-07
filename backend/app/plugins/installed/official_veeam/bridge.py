"""Bridge between the Integrations UI and the Veeam plugin.

A "veeam" IntegrationProfile (configured in Settings -> Integrations, just like
Zabbix/Hyper-V) is the user-facing way to register a Veeam B&R server. This
module mirrors it into the plugin's live ``veeam_backup_servers`` registry
(which the plugin's ``setup()`` reads to build its API clients and the live-data
routes read to serve dashboard state), so servers added/edited/deleted after
the initial alembic backfill take effect without a restart.
"""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.db.integration_profile import IntegrationProfile
from app.plugins.installed.official_veeam.models import VeeamBackupServer

logger = logging.getLogger("plugin.veeam.bridge")


def sync_profile_to_server(db: Session, profile: IntegrationProfile) -> None:
    """Upsert a ``veeam_backup_servers`` row from a ``veeam`` integration profile.

    Mirrors the mapping used by the ``f1a2b3c4d5e6`` migration backfill: the
    server name matches the profile name (unique in ``veeam_backup_servers``),
    edition is derived from ``base_url`` presence, and the legacy ssh_* fields
    carry the profile's ssh_* connection fields for agent fallback.
    """
    if profile.integration_type != "veeam":
        return

    name = profile.name
    existing = db.execute(
        select(VeeamBackupServer).where(VeeamBackupServer.name == name)
    ).scalar_one_or_none()

    edition = "enterprise" if (profile.base_url or "").strip() else "community"

    if existing is None:
        server = VeeamBackupServer(
            name=name,
            edition=edition,
            data_source=profile.data_source or "both",
            url=(profile.base_url or "").strip() or None,
            username=profile.username,
            encrypted_password=profile.encrypted_secret,
            verify_ssl=bool(profile.verify_ssl),
            timeout=profile.timeout or 30,
            enabled=bool(profile.enabled),
            status="unknown",
            legacy_ssh_host=(profile.ssh_host or "").strip() or None,
            legacy_ssh_port=profile.ssh_port,
            legacy_ssh_username=profile.ssh_username,
            legacy_ssh_password_encrypted=profile.ssh_password_encrypted,
        )
        db.add(server)
    else:
        existing.edition = edition
        existing.data_source = profile.data_source or "both"
        existing.url = (profile.base_url or "").strip() or None
        existing.username = profile.username
        existing.encrypted_password = profile.encrypted_secret
        existing.verify_ssl = bool(profile.verify_ssl)
        existing.timeout = profile.timeout or 30
        existing.enabled = bool(profile.enabled)
        existing.legacy_ssh_host = (profile.ssh_host or "").strip() or None
        existing.legacy_ssh_port = profile.ssh_port
        existing.legacy_ssh_username = profile.ssh_username
        existing.legacy_ssh_password_encrypted = profile.ssh_password_encrypted

    row = existing if existing is not None else server

    if row.url is None:
        from app.models.db.agent_remote_target import AgentRemoteTarget

        ssh_host = (profile.ssh_host or "").strip()
        candidates = []
        for t in db.query(AgentRemoteTarget).filter(
            AgentRemoteTarget.enabled.is_(True)
        ):
            plugins = {
                p.strip() for p in (t.target_plugins or "").split(",") if p.strip()
            }
            if "veeam" in plugins:
                candidates.append(t)

        # Only a target whose hostname is exactly the profile's SSH host may be
        # linked. Guessing "the first veeam-enabled target" relayed one server's
        # queries to another machine and reported that machine's repositories
        # under the wrong server name.
        candidate = next(
            (t for t in candidates if ssh_host and t.hostname == ssh_host), None
        )

        if candidate is not None:
            row.agent_id = candidate.agent_id
            row.target_id = candidate.id
            row.legacy_ssh_host = candidate.hostname
            row.legacy_ssh_port = candidate.port
            row.legacy_ssh_username = candidate.username
            row.legacy_ssh_password_encrypted = candidate.password_encrypted
        elif ssh_host and row.target_id is not None:
            linked = db.get(AgentRemoteTarget, row.target_id)
            if linked is not None and linked.hostname != ssh_host:
                logger.warning(
                    "Veeam profile %s: linked target %s is %s but the profile SSH "
                    "host is %s; unlinking so the relay does not run against the "
                    "wrong host",
                    profile.name, row.target_id, linked.hostname, ssh_host,
                )
                row.agent_id = None
                row.target_id = None

    db.commit()
    logger.info("Synced veeam integration profile %s to veeam_backup_servers", profile.id)
    reset_veeam_clients()


def delete_profile_server(db: Session, profile_name: str) -> None:
    """Remove the ``veeam_backup_servers`` row for an integration profile."""
    server = db.execute(
        select(VeeamBackupServer).where(VeeamBackupServer.name == profile_name)
    ).scalar_one_or_none()
    if server is not None:
        _purge_server_row(db, server)
        db.commit()
        logger.info("Removed veeam_backup_servers row for profile %s", profile_name)
        reset_veeam_clients()


def _stale_target_row(db: Session, row: VeeamBackupServer) -> bool:
    """True when the row points at a remote target that no longer exists."""
    if row.target_id is None:
        return False
    from app.models.db.agent_remote_target import AgentRemoteTarget

    return db.get(AgentRemoteTarget, row.target_id) is None


def _purge_server_row(db: Session, row: VeeamBackupServer) -> int:
    """Delete a server row together with every cached dataset collected for it.

    Returns the deleted row id. Child tables carry ``ondelete=CASCADE`` in
    Postgres, but the rows are removed explicitly here so the purge also works
    on SQLite (tests) where FK enforcement is off by default.
    """
    from app.plugins.installed.official_veeam.models import (
        VeeamJob,
        VeeamJobRun,
        VeeamLicense,
        VeeamRepository,
        VeeamRestorePoint,
        VeeamSnapshot,
    )

    row_id = row.id
    for model in (
        VeeamSnapshot,
        VeeamJobRun,
        VeeamJob,
        VeeamRepository,
        VeeamRestorePoint,
        VeeamLicense,
    ):
        db.query(model).filter(model.server_id == row_id).delete(
            synchronize_session=False
        )
    db.delete(row)
    db.flush()
    return row_id


def sync_target_to_server(db: Session, target) -> None:
    """Upsert a community veeam_backup_servers row from a remote target.

    Enabled when the target is enabled, its target_plugins include "veeam",
    and its protocol is ssh. The agent relay/community path only works over
    SSH, so a psremoting/winrm target never registers a row; if an existing
    row is re-synced against a non-SSH target it is disabled (same path as
    removing the veeam plugin).
    """
    from app.plugins.installed.official_veeam.models import VeeamBackupServer

    raw = target.target_plugins or ""
    plugins = {p.strip() for p in raw.split(",") if p.strip()}
    row = db.execute(
        select(VeeamBackupServer).where(VeeamBackupServer.target_id == target.id)
    ).scalar_one_or_none()

    protocol_is_ssh = (getattr(target, "protocol", "") or "").lower() == "ssh"

    if not (target.enabled and "veeam" in plugins and protocol_is_ssh):
        if row is not None:
            row.enabled = False
            db.commit()
            reset_veeam_clients()
        return

    if row is None:
        name = f"[{target.name}]"
        clash = db.execute(
            select(VeeamBackupServer).where(VeeamBackupServer.name == name)
        ).scalar_one_or_none()
        if clash is not None and clash.target_id != target.id:
            if _stale_target_row(db, clash):
                # Host was deleted (or moved to another agent) but its row
                # survived: drop it and its cached data so the recreated host
                # reclaims the clean name under a brand new server id.
                stale_id = _purge_server_row(db, clash)
                logger.info(
                    "Purged orphaned veeam server %s (%s) for recreated target %s",
                    stale_id, name, target.id,
                )
            else:
                name = f"[{target.name}] #{target.id}"
        row = VeeamBackupServer(
            name=name,
            edition="community",
            data_source="both",
            agent_id=target.agent_id,
            target_id=target.id,
            legacy_ssh_host=target.hostname,
            legacy_ssh_port=target.port,
            legacy_ssh_username=target.username,
            legacy_ssh_password_encrypted=target.password_encrypted,
            db_type=getattr(target, "db_type", None) or "auto",
            column_case=getattr(target, "column_case", None) or "auto",
            enabled=True,
            status="unknown",
        )
        db.add(row)
    else:
        row.agent_id = target.agent_id
        row.target_id = target.id
        row.legacy_ssh_host = target.hostname
        row.legacy_ssh_port = target.port
        row.legacy_ssh_username = target.username
        row.legacy_ssh_password_encrypted = target.password_encrypted
        # Never clobber db_type/column_case on re-sync. The registry row can hold
        # a lazily detected value (or a deliberate operator override) that is more
        # accurate than the remote target's stored default, and copying a stale
        # target value has already broken a working MSSQL registration once. Only
        # fill them in when they are still unset.
        if not row.db_type:
            row.db_type = getattr(target, "db_type", None) or "auto"
        if not row.column_case:
            row.column_case = getattr(target, "column_case", None) or "auto"
        row.enabled = True
    db.commit()
    reset_veeam_clients()


def remove_target_server(db: Session, target_id: int) -> None:
    """Delete the veeam_backup_servers row linked to a deleted remote target.

    The row and every dataset cached for it (jobs, sessions, repositories,
    restore points, licenses, snapshots) are removed, so a host that is
    re-registered - possibly under a different agent - starts from a clean
    slate with a new server id instead of inheriting dead data.
    """
    from app.plugins.installed.official_veeam.models import VeeamBackupServer

    row = db.execute(
        select(VeeamBackupServer).where(VeeamBackupServer.target_id == target_id)
    ).scalar_one_or_none()
    if row is None:
        return
    row_id = _purge_server_row(db, row)
    db.commit()
    logger.info(
        "Removed veeam_backup_servers row %s for deleted target %s",
        row_id, target_id,
    )
    reset_veeam_clients()


def reset_veeam_clients() -> None:
    """Reload the live plugin's API clients from the DB registry.

    Mirrors ``reset_hyperv_provider`` / ``reset_unifi_clients``: it asks the
    running plugin instance (if loaded) to rebuild its client cache so a newly
    saved/updated/removed server takes effect without a server restart.
    """
    try:
        from app.plugins.registry import plugin_registry

        plugin = plugin_registry._live.get("official_veeam")
        if plugin is None:
            return
        import asyncio

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            loop.create_task(plugin.setup())  # type: ignore[union-attr]
        else:
            asyncio.run(plugin.setup())  # type: ignore[union-attr]
    except Exception:  # pragma: no cover - best effort refresh
        logger.exception("Failed to reset Veeam plugin clients")