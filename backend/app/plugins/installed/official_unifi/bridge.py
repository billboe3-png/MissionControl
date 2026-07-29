"""Bridge between the Integrations UI and the UniFi plugin.

A "unifi" IntegrationProfile (configured in Settings -> Integrations, just like
Zabbix/Hyper-V) is the user-facing way to supply a UniFi Site Manager API key.
This module mirrors it into the plugin's ``unifi_controllers`` table (which the
plugin's ``setup()`` reads to build its API clients) and refreshes the live
plugin's in-memory client cache so changes take effect without a restart.
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import CredentialCipher
from app.models.db.integration_profile import IntegrationProfile
from app.plugins.installed.official_unifi.models import UniFiController

logger = logging.getLogger("plugin.unifi.bridge")

SITE_MANAGER_URL = "https://api.ui.com"


def _cipher() -> CredentialCipher:
    from app.core.config import get_settings

    return CredentialCipher(get_settings().missioncontrol_secret_key)


def sync_profile_to_controllers(db: Session, profile: IntegrationProfile) -> None:
    """Upsert a ``unifi_controllers`` row from a ``unifi`` integration profile.

    The controller name is unique per integration profile id so editing the
    same profile updates the same controller row instead of duplicating.
    """
    if profile.integration_type != "unifi":
        return

    api_key = _cipher().decrypt(profile.encrypted_secret) or ""
    name = f"integration:{profile.id}"

    existing = db.execute(
        select(UniFiController).where(UniFiController.name == name)
    ).scalar_one_or_none()

    is_cloud = profile.base_url in (SITE_MANAGER_URL, SITE_MANAGER_URL + "/", "", None)
    controller_url = SITE_MANAGER_URL if is_cloud else profile.base_url
    controller_type = "cloud" if is_cloud else "local"

    if existing is None:
        controller = UniFiController(
            name=name,
            url=controller_url,
            encrypted_api_key=_cipher().encrypt(api_key) if api_key else None,
            controller_type=controller_type,
            verify_ssl=profile.verify_ssl,
            timeout=profile.timeout or 30,
            enabled=bool(profile.enabled),
        )
        db.add(controller)
    else:
        existing.url = controller_url
        existing.encrypted_api_key = _cipher().encrypt(api_key) if api_key else None
        existing.controller_type = controller_type
        existing.verify_ssl = profile.verify_ssl
        existing.timeout = profile.timeout or 30
        existing.enabled = bool(profile.enabled)

    db.commit()
    logger.info("Synced unifi integration profile %s to unifi_controllers", profile.id)
    reset_unifi_clients()


def delete_profile_controllers(db: Session, profile_id: int) -> None:
    """Remove the controller row associated with an integration profile."""
    name = f"integration:{profile_id}"
    controller = db.execute(
        select(UniFiController).where(UniFiController.name == name)
    ).scalar_one_or_none()
    if controller is not None:
        db.delete(controller)
        db.commit()
        logger.info("Removed unifi_controllers row for integration profile %s", profile_id)
        reset_unifi_clients()


def reset_unifi_clients() -> None:
    """Reload the live plugin's API clients from the DB controllers.

    Mirrors ``reset_hyperv_provider`` / ``reset_proxmox_provider``: it asks the
    running plugin instance (if loaded) to rebuild its client cache so a newly
    saved/updated API key takes effect without a server restart.
    """
    try:
        from app.plugins.registry import plugin_registry

        plugin = plugin_registry._live.get("official_unifi")
        if plugin is None:
            return
        import asyncio

        # setup() is async and reloads controllers from the DB.
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            loop.create_task(plugin.setup())  # type: ignore[union-attr]
        else:
            asyncio.run(plugin.setup())  # type: ignore[union-attr]
    except Exception:  # pragma: no cover - best effort refresh
        logger.exception("Failed to reset UniFi plugin clients")
