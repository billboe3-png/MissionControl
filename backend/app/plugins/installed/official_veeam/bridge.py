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
            rest_url=(profile.base_url or "").strip() or None,
            rest_username=profile.username,
            rest_password_encrypted=profile.encrypted_secret,
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
        existing.rest_url = (profile.base_url or "").strip() or None
        existing.rest_username = profile.username
        existing.rest_password_encrypted = profile.encrypted_secret
        existing.verify_ssl = bool(profile.verify_ssl)
        existing.timeout = profile.timeout or 30
        existing.enabled = bool(profile.enabled)
        existing.legacy_ssh_host = (profile.ssh_host or "").strip() or None
        existing.legacy_ssh_port = profile.ssh_port
        existing.legacy_ssh_username = profile.ssh_username
        existing.legacy_ssh_password_encrypted = profile.ssh_password_encrypted

    db.commit()
    logger.info("Synced veeam integration profile %s to veeam_backup_servers", profile.id)
    reset_veeam_clients()


def delete_profile_server(db: Session, profile_name: str) -> None:
    """Remove the ``veeam_backup_servers`` row for an integration profile."""
    server = db.execute(
        select(VeeamBackupServer).where(VeeamBackupServer.name == profile_name)
    ).scalar_one_or_none()
    if server is not None:
        db.delete(server)
        db.commit()
        logger.info("Removed veeam_backup_servers row for profile %s", profile_name)
        reset_veeam_clients()


def sync_target_to_server(db: Session, target) -> None:
    """Upsert a community veeam_backup_servers row from a remote target.

    Enabled when the target is enabled and its target_plugins include "veeam".
    """
    from app.plugins.installed.official_veeam.models import VeeamBackupServer

    raw = target.target_plugins or ""
    plugins = {p.strip() for p in raw.split(",") if p.strip()}
    row = db.execute(
        select(VeeamBackupServer).where(VeeamBackupServer.target_id == target.id)
    ).scalar_one_or_none()

    if not (target.enabled and "veeam" in plugins):
        if row is not None:
            row.enabled = False
        db.commit()
        return

    if row is None:
        name = f"[{target.name}]"
        clash = db.execute(
            select(VeeamBackupServer).where(VeeamBackupServer.name == name)
        ).scalar_one_or_none()
        if clash is not None and clash.target_id != target.id:
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
        row.enabled = True
    db.commit()


def remove_target_server(db: Session, target_id: int) -> None:
    """Disable the veeam_backup_servers row linked to a deleted remote target."""
    from app.plugins.installed.official_veeam.models import VeeamBackupServer

    row = db.execute(
        select(VeeamBackupServer).where(VeeamBackupServer.target_id == target_id)
    ).scalar_one_or_none()
    if row is not None:
        row.enabled = False
        db.commit()


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