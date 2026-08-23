"""
Plugin Repository Abstraction

Supports multiple plugin repositories: official, community, and private enterprise.
Each repository has a name, URL, priority, enabled state, and trust level.

Sprint 3.10.4 - Plugin Marketplace.
"""

import logging
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

logger = logging.getLogger(__name__)


class TrustLevel(StrEnum):
    OFFICIAL = "official"
    COMMUNITY = "community"
    PRIVATE = "private"
    UNTRUSTED = "untrusted"


@dataclass
class Repository:
    """A plugin repository definition."""

    name: str
    url: str
    priority: int = 100
    enabled: bool = True
    trust_level: TrustLevel = TrustLevel.COMMUNITY
    last_sync: str = ""
    plugin_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "url": self.url,
            "priority": self.priority,
            "enabled": self.enabled,
            "trust_level": self.trust_level.value,
            "last_sync": self.last_sync,
            "plugin_count": self.plugin_count,
        }


DEFAULT_REPOSITORIES = [
    Repository(
        name="official",
        url="https://plugins.missioncontrol.io",
        priority=10,
        enabled=True,
        trust_level=TrustLevel.OFFICIAL,
    ),
    Repository(
        name="community",
        url="https://community.plugins.missioncontrol.io",
        priority=50,
        enabled=True,
        trust_level=TrustLevel.COMMUNITY,
    ),
]


class RepositoryManager:
    """Manages plugin repositories."""

    def __init__(self) -> None:
        self._repositories: list[Repository] = list(DEFAULT_REPOSITORIES)

    def get_all(self) -> list[Repository]:
        return [r for r in self._repositories if r.enabled]

    def get_by_name(self, name: str) -> Repository | None:
        for r in self._repositories:
            if r.name == name:
                return r
        return None

    def add(self, repo: Repository) -> None:
        existing = self.get_by_name(repo.name)
        if existing:
            existing.url = repo.url
            existing.priority = repo.priority
            existing.enabled = repo.enabled
            existing.trust_level = repo.trust_level
        else:
            self._repositories.append(repo)
        logger.info("Repository added/updated: %s", repo.name)

    def remove(self, name: str) -> bool:
        before = len(self._repositories)
        self._repositories = [r for r in self._repositories if r.name != name]
        return len(self._repositories) < before

    def set_enabled(self, name: str, enabled: bool) -> bool:
        repo = self.get_by_name(name)
        if repo:
            repo.enabled = enabled
            return True
        return False

    def get_sorted(self) -> list[Repository]:
        return sorted(self.get_all(), key=lambda r: r.priority)

    def to_dicts(self) -> list[dict[str, Any]]:
        return [r.to_dict() for r in self._repositories]


repository_manager = RepositoryManager()
