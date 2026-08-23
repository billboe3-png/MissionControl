"""
Mission Control Deployment Profiles

Predefined configuration profiles for Community and Enterprise editions.
"""

from __future__ import annotations

import copy
import logging

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------ #
# Profile definitions                                                   #
# ------------------------------------------------------------------ #

DEPLOYMENT_PROFILES: dict[str, dict] = {
    "community": {
        "name": "Community Edition",
        "edition": "community",
        "database": {
            "host": "postgres",
            "port": 5432,
            "pool_size": 10,
        },
        "redis": {
            "host": "redis",
            "port": 6379,
        },
        "storage": "local",
        "ha_ready": False,
        "tls_required": False,
        "max_agents": 100,
        "max_users": 50,
        "plugins_dir": "plugins",
    },
    "enterprise": {
        "name": "Enterprise Edition",
        "edition": "enterprise",
        "database": {
            "host": "postgres",
            "port": 5432,
            "pool_size": 20,
        },
        "redis": {
            "host": "redis",
            "port": 6379,
        },
        "storage": "remote",
        "ha_ready": True,
        "tls_required": True,
        "max_agents": 1000,
        "max_users": 500,
        "plugins_dir": "plugins",
    },
}


# ------------------------------------------------------------------ #
# Helper                                                               #
# ------------------------------------------------------------------ #

def _deep_merge(base: dict, override: dict) -> dict:
    """Merge *override* into a deep copy of *base*.

    Nested dicts are merged recursively. All other values in *override*
    replace those in *base*.
    """
    result = copy.deepcopy(base)
    for key, value in override.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


# ------------------------------------------------------------------ #
# Profile class                                                        #
# ------------------------------------------------------------------ #

class DeploymentProfile:
    """Manages and applies deployment profiles."""

    @staticmethod
    def get_profile(name: str) -> dict:
        """Return the profile dict for *name*, or raise KeyError."""
        if name not in DEPLOYMENT_PROFILES:
            available = ", ".join(sorted(DEPLOYMENT_PROFILES))
            raise KeyError(
                f"Unknown profile '{name}'. Available: {available}"
            )
        return copy.deepcopy(DEPLOYMENT_PROFILES[name])

    @staticmethod
    def list_profiles() -> list[dict]:
        """Return a summary list of all available profiles."""
        return [
            {
                "name": profile["name"],
                "edition": profile["edition"],
                "ha_ready": profile.get("ha_ready", False),
                "max_agents": profile.get("max_agents", 0),
                "max_users": profile.get("max_users", 0),
            }
            for profile in DEPLOYMENT_PROFILES.values()
        ]

    @staticmethod
    def apply_profile(profile_name: str, existing_config: dict) -> dict:
        """Merge profile defaults into *existing_config*.

        Values already present in *existing_config* take precedence over
        the profile defaults. Nested dicts are merged recursively.
        """
        base = DeploymentProfile.get_profile(profile_name)
        return _deep_merge(base, existing_config)

    @staticmethod
    def validate_profile(profile_name: str) -> list[str]:
        """Return a list of warnings or issues for the given profile."""
        issues: list[str] = []

        try:
            profile = DEPLOYMENT_PROFILES[profile_name]
        except KeyError:
            return [f"Unknown profile: {profile_name}"]

        db = profile.get("database", {})
        if db.get("pool_size", 0) > 50:
            issues.append(
                "database.pool_size > 50 may cause connection exhaustion"
            )

        if profile.get("tls_required") and profile.get("storage") == "local":
            issues.append(
                "TLS is required but storage is local — "
                "ensure certificates are configured"
            )

        if profile.get("ha_ready") and db.get("pool_size", 0) < 10:
            issues.append(
                "HA mode enabled but database pool_size < 10"
            )

        if profile.get("max_agents", 0) > 5000:
            issues.append("max_agents > 5000 may degrade performance")

        if profile.get("max_users", 0) > 1000:
            issues.append("max_users > 1000 may degrade performance")

        return issues
