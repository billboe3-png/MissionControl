"""
D-Link DGS-1210 Cache - In-memory caching layer
"""
import logging
import time
from typing import Any, Dict, List, Optional
from threading import Lock

logger = logging.getLogger("plugin.dlink.cache")


class DLinkCache:
    """Thread-safe in-memory cache for D-Link switch data."""

    def __init__(self, ttl: int = 60):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._ttl = ttl
        self._lock = Lock()

    def _make_key(self, *parts: str) -> str:
        return ":".join(parts)

    def get(self, *parts: str) -> Optional[Any]:
        key = self._make_key(*parts)
        with self._lock:
            entry = self._cache.get(key)
            if entry and time.time() - entry["time"] < self._ttl:
                return entry["value"]
            elif entry:
                del self._cache[key]
        return None

    def set(self, value: Any, *parts: str) -> None:
        key = self._make_key(*parts)
        with self._lock:
            self._cache[key] = {"value": value, "time": time.time()}

    def delete(self, *parts: str) -> None:
        key = self._make_key(*parts)
        with self._lock:
            self._cache.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()

    def invalidate_prefix(self, prefix: str) -> None:
        with self._lock:
            keys_to_delete = [k for k in self._cache if k.startswith(prefix)]
            for k in keys_to_delete:
                del self._cache[k]


class DLinkCacheManager:
    """Manages multiple caches for different data types."""

    def __init__(self, default_ttl: int = 60):
        self._caches: Dict[str, DLinkCache] = {}
        self._default_ttl = default_ttl

    def get_cache(self, name: str, ttl: Optional[int] = None) -> DLinkCache:
        if name not in self._caches:
            self._caches[name] = DLinkCache(ttl or self._default_ttl)
        return self._caches[name]

    def clear_all(self) -> None:
        for cache in self._caches.values():
            cache.clear()


# Singleton instance
cache_manager = DLinkCacheManager(default_ttl=60)


# Convenience functions
def get_switch_cache() -> DLinkCache:
    return cache_manager.get_cache("switches", ttl=300)


def get_mac_cache() -> DLinkCache:
    return cache_manager.get_cache("macs", ttl=60)


def get_vlan_cache() -> DLinkCache:
    return cache_manager.get_cache("vlans", ttl=300)


def get_port_vlan_cache() -> DLinkCache:
    return cache_manager.get_cache("port_vlans", ttl=300)