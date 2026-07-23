"""
Veeam B&R Provider Factory

Resolves the appropriate Veeam provider based on DB integration profiles
and environment configuration. Supports both REST API (Enterprise) and
PowerShell remoting (Community Edition) providers.
"""

import base64
import logging
import time
from typing import Any

from sqlalchemy.orm import Session

from app.providers.veeam.base_provider import VeeamProvider
from app.providers.veeam.mock_provider import MockVeeamProvider

logger = logging.getLogger(__name__)

_provider: VeeamProvider | None = None

# ── Cache ───────────────────────────────────────────────────────
# Provider cache: keyed by profile.id, stores (provider, created_at)
_provider_cache: dict[int, tuple[VeeamProvider, float]] = {}
_PROVIDER_CACHE_TTL = 300  # 5 minutes

# db_type cache: keyed by (ssh_host, ssh_port, ssh_username), stores (db_type, detected_at)
_db_type_cache: dict[tuple[str, int, str], tuple[str, float]] = {}
_DB_TYPE_CACHE_TTL = 3600  # 1 hour — db_type doesn't change


def get_veeam_provider(db: Session | None = None) -> VeeamProvider:
    """Return the active Veeam provider.

    Resolution priority:
    1. Cached singleton
    2. DB IntegrationProfile (type='veeam')
       - If base_url is set → REST API provider
       - If no base_url but ssh_host is set → PowerShell provider
    3. Mock fallback
    """
    global _provider
    if _provider is not None:
        return _provider

    if db is not None:
        try:
            from app.core.config import get_settings
            from app.core.security import CredentialCipher
            from app.repositories.integration_profile_repository import (
                IntegrationProfileRepository,
            )

            profiles = IntegrationProfileRepository.get_all_enabled_by_type(
                db, "veeam"
            )
            if profiles:
                profile = profiles[0]
                settings = get_settings()
                cipher = CredentialCipher(settings.missioncontrol_secret_key)
                password = ""
                if profile.encrypted_secret:
                    try:
                        password = cipher.decrypt(
                            profile.encrypted_secret
                        )
                    except Exception:
                        logger.warning("Failed to decrypt Veeam secret")

                ssh_password = ""
                if profile.ssh_password_encrypted:
                    try:
                        ssh_password = cipher.decrypt(
                            profile.ssh_password_encrypted
                        )
                    except Exception:
                        logger.warning("Failed to decrypt Veeam SSH password")

                # Decide provider based on configuration
                has_rest = bool(profile.base_url)
                has_ssh = bool(profile.ssh_host and profile.ssh_username)

                if has_rest:
                    # REST API provider (Enterprise / with REST API)
                    from app.providers.veeam.veeam_provider import VeeamRESTProvider

                    _provider = VeeamRESTProvider(
                        base_url=profile.base_url or "",
                        username=profile.username or "",
                        password=password,
                        timeout=profile.timeout or 30,
                        verify_ssl=(
                            profile.verify_ssl
                            if profile.verify_ssl is not None
                            else True
                        ),
                        ssh_host=profile.ssh_host or "",
                        ssh_port=profile.ssh_port or 22,
                        ssh_username=profile.ssh_username or "",
                        ssh_password=ssh_password,
                        data_source=profile.data_source or "both",
                    )
                    logger.info(
                        "Veeam REST provider initialized from DB profile: %s",
                        profile.name,
                    )
                elif has_ssh:
                    # PowerShell provider (Community Edition - no REST API)
                    from app.providers.veeam.powershell_provider import (
                        VeeamPowerShellProvider,
                    )

                    transport = "ssh"  # Community Edition typically uses SSH
                    port = 22

                    _provider = VeeamPowerShellProvider(
                        host=profile.ssh_host or "",
                        port=5985,
                        username=profile.ssh_username or "",
                        password=ssh_password,
                        timeout=profile.timeout or 60,
                        transport=transport,
                        ssh_port=profile.ssh_port or 22,
                    )
                    logger.info(
                        "Veeam PowerShell provider initialized from DB profile: %s",
                        profile.name,
                    )
                else:
                    logger.warning(
                        "Veeam profile '%s' has no base_url or ssh_host configured",
                        profile.name,
                    )
                    _provider = MockVeeamProvider()
                    return _provider

                return _provider
        except Exception as exc:
            logger.exception("Failed to initialize Veeam provider from DB: %s", exc)

    logger.info("Using mock Veeam provider")
    _provider = MockVeeamProvider()
    return _provider


def reset_veeam_provider() -> None:
    """Clear the cached Veeam provider singleton and all caches."""
    global _provider
    _provider = None
    _provider_cache.clear()
    _db_type_cache.clear()


def _create_provider_for_profile(profile, settings, cipher) -> VeeamProvider | None:
    """Create a provider instance for a single IntegrationProfile."""
    password = ""
    if profile.encrypted_secret:
        try:
            password = cipher.decrypt(profile.encrypted_secret)
        except Exception:
            logger.warning("Failed to decrypt Veeam secret for profile %s", profile.name)

    ssh_password = ""
    if profile.ssh_password_encrypted:
        try:
            ssh_password = cipher.decrypt(profile.ssh_password_encrypted)
        except Exception:
            logger.warning("Failed to decrypt Veeam SSH password for profile %s", profile.name)

    has_rest = bool(profile.base_url)
    has_ssh = bool(profile.ssh_host and profile.ssh_username)

    # Auto-detect database type (PostgreSQL vs MSSQL) — with cache
    db_type = "postgresql"
    column_case = "pascal"
    if has_ssh:
        cache_key = (profile.ssh_host or "", profile.ssh_port or 22, profile.ssh_username or "")
        now = time.monotonic()
        cached = _db_type_cache.get(cache_key)
        if cached and (now - cached[1]) < _DB_TYPE_CACHE_TTL:
            db_type = cached[0]
            logger.info("Cached db_type=%s for profile %s", db_type, profile.name)
        else:
            from app.providers.veeam.db_bridge import detect_db_type
            try:
                db_type = detect_db_type(
                    profile.ssh_host, profile.ssh_port or 22,
                    profile.ssh_username, ssh_password,
                )
                _db_type_cache[cache_key] = (db_type, now)
                logger.info("Detected db_type=%s column_case=%s for profile %s", db_type, column_case, profile.name)
            except Exception as exc:
                logger.warning("DB type detection failed for %s, defaulting to postgresql: %s", profile.name, exc)
        if db_type == "mssql":
            column_case = "snake"

    if has_rest:
        from app.providers.veeam.veeam_provider import VeeamRESTProvider

        provider = VeeamRESTProvider(
            base_url=profile.base_url or "",
            username=profile.username or "",
            password=password,
            timeout=profile.timeout or 30,
            verify_ssl=profile.verify_ssl if profile.verify_ssl is not None else True,
            ssh_host=profile.ssh_host or "",
            ssh_port=profile.ssh_port or 22,
            ssh_username=profile.ssh_username or "",
            ssh_password=ssh_password,
            data_source=profile.data_source or "both",
            db_type=db_type,
            column_case=column_case,
        )
        logger.info("Veeam REST provider created for profile: %s (db_type=%s, column_case=%s)", profile.name, db_type, column_case)
        return provider

    if has_ssh:
        from app.providers.veeam.powershell_provider import VeeamPowerShellProvider

        provider = VeeamPowerShellProvider(
            host=profile.ssh_host or "",
            port=5985,
            username=profile.ssh_username or "",
            password=ssh_password,
            timeout=profile.timeout or 60,
            transport="ssh",
            ssh_port=profile.ssh_port or 22,
            db_type=db_type,
            column_case=column_case,
        )
        logger.info("Veeam PowerShell provider created for profile: %s (db_type=%s, column_case=%s)", profile.name, db_type, column_case)
        return provider

    logger.warning("Profile '%s' has no base_url or ssh_host configured", profile.name)
    return None


def get_all_veeam_providers(
    db: Session | None = None,
) -> list[tuple[str, VeeamProvider]]:
    """Return (name, provider) pairs for every enabled Veeam profile.

    Uses a 5-minute cache to avoid recreating SSH connections on every request.
    """
    if db is None:
        singleton = get_veeam_provider()
        return [("default", singleton)]

    try:
        from app.core.config import get_settings
        from app.core.security import CredentialCipher
        from app.repositories.integration_profile_repository import (
            IntegrationProfileRepository,
        )

        settings = get_settings()
        cipher = CredentialCipher(settings.missioncontrol_secret_key)

        profiles = IntegrationProfileRepository.get_all_enabled_by_type(db, "veeam")
        now = time.monotonic()
        result: list[tuple[str, VeeamProvider]] = []
        uncached_profiles = []

        # Check cache first
        for profile in profiles:
            cached = _provider_cache.get(profile.id)
            if cached and (now - cached[1]) < _PROVIDER_CACHE_TTL:
                result.append((profile.name, cached[0]))
            else:
                uncached_profiles.append(profile)

        # Only create providers for uncached profiles
        for profile in uncached_profiles:
            provider = _create_provider_for_profile(profile, settings, cipher)
            if provider is not None:
                _provider_cache[profile.id] = (provider, now)
                result.append((profile.name, provider))

        return result
    except Exception as exc:
        logger.exception("Failed to load Veeam providers from DB: %s", exc)
        singleton = get_veeam_provider()
        return [("default", singleton)]
