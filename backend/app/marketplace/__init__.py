"""
Mission Control Plugin Marketplace

Secure package manager for Mission Control plugins.
Supports official, community, and private enterprise repositories.
Handles download, verification, installation, updates, and rollback.

AI NEVER executes infrastructure changes.
Agents never install plugins directly.
Server is the only component that manages plugins.

Sprint 3.10.4 - Plugin Marketplace.
"""

from app.marketplace.installer import PluginInstaller
from app.marketplace.registry import MarketplaceRegistry

__all__ = ["MarketplaceRegistry", "PluginInstaller"]
