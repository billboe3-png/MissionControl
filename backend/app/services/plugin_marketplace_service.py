"""
Mission Control Plugin Marketplace Service

Provides the plugin marketplace catalog. In the future this would
fetch from a remote registry; for now it returns a built-in catalog
of known plugins with their metadata.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Built-in plugin catalog.
# In production this would be fetched from a remote marketplace API.
BUILTIN_CATALOG: list[dict[str, Any]] = [
    # ------------------------------------------------------------------ #
    # Server Plugins                                                      #
    # ------------------------------------------------------------------ #
    {
        "slug": "zabbix",
        "name": "Zabbix Monitoring",
        "version": "1.0.0",
        "description": "Monitor infrastructure via Zabbix API",
        "author": "Mission Control",
        "execution_target": "server",
        "category": "monitoring",
        "permissions": ["read:integrations", "read:dashboard"],
        "dependencies": [],
        "min_core_version": "3.0.0",
    },
    {
        "slug": "hyperv",
        "name": "Hyper-V Management",
        "version": "1.0.0",
        "description": "Manage Hyper-V virtual machines and checkpoints",
        "author": "Mission Control",
        "execution_target": "server",
        "category": "virtualization",
        "permissions": ["read:integrations", "manage:integrations"],
        "dependencies": [],
        "min_core_version": "3.0.0",
    },
    {
        "slug": "proxmox",
        "name": "Proxmox VE Management",
        "version": "1.0.0",
        "description": "Manage Proxmox VE nodes, VMs, and containers",
        "author": "Mission Control",
        "execution_target": "server",
        "category": "virtualization",
        "permissions": ["read:integrations", "manage:integrations"],
        "dependencies": [],
        "min_core_version": "3.0.0",
    },
    {
        "slug": "github",
        "name": "GitHub Integration",
        "version": "1.0.0",
        "description": "Repository health, issues, and CI/CD status",
        "author": "Mission Control",
        "execution_target": "server",
        "category": "devops",
        "permissions": ["read:dashboard"],
        "dependencies": [],
        "min_core_version": "3.0.0",
    },
    {
        "slug": "grafana",
        "name": "Grafana Dashboards",
        "version": "1.0.0",
        "description": "Embed Grafana dashboards and alerting",
        "author": "Mission Control",
        "execution_target": "server",
        "category": "monitoring",
        "permissions": ["read:dashboard", "read:integrations"],
        "dependencies": [],
        "min_core_version": "3.0.0",
    },
    {
        "slug": "prometheus",
        "name": "Prometheus Metrics",
        "version": "1.0.0",
        "description": "Query and display Prometheus metrics",
        "author": "Mission Control",
        "execution_target": "server",
        "category": "monitoring",
        "permissions": ["read:dashboard", "read:integrations"],
        "dependencies": [],
        "min_core_version": "3.0.0",
    },
    {
        "slug": "veeam",
        "name": "Veeam Backup & Replication",
        "version": "1.0.0",
        "description": "Monitor Veeam backup jobs, restore points, and repositories",
        "author": "Mission Control",
        "execution_target": "server",
        "category": "backup",
        "permissions": ["read:integrations"],
        "dependencies": [],
        "min_core_version": "3.0.0",
    },
    {
        "slug": "jira",
        "name": "Jira Integration",
        "version": "1.0.0",
        "description": "Sync issues, sprint data, and project boards",
        "author": "Mission Control",
        "execution_target": "server",
        "category": "devops",
        "permissions": ["read:projects", "manage:projects"],
        "dependencies": [],
        "min_core_version": "3.0.0",
    },
    {
        "slug": "servicenow",
        "name": "ServiceNow Integration",
        "version": "1.0.0",
        "description": "Sync incidents, changes, and CMDB data",
        "author": "Mission Control",
        "execution_target": "server",
        "category": "itsm",
        "permissions": ["read:integrations"],
        "dependencies": [],
        "min_core_version": "3.0.0",
    },
    # ------------------------------------------------------------------ #
    # Agent Plugins                                                       #
    # ------------------------------------------------------------------ #
    {
        "slug": "rustdesk",
        "name": "RustDesk Remote Desktop",
        "version": "1.0.0",
        "description": "Remote desktop access via RustDesk",
        "author": "Mission Control",
        "execution_target": "agent",
        "category": "remote-access",
        "permissions": ["execute:commands"],
        "dependencies": [],
        "min_core_version": "3.0.0",
    },
    {
        "slug": "windows-events",
        "name": "Windows Event Logs",
        "version": "1.0.0",
        "description": "Collect and analyze Windows Event Logs",
        "author": "Mission Control",
        "execution_target": "agent",
        "category": "logging",
        "permissions": ["collect:events"],
        "dependencies": [],
        "min_core_version": "3.0.0",
    },
    {
        "slug": "windows-services",
        "name": "Windows Services Monitor",
        "version": "1.0.0",
        "description": "Monitor and manage Windows services",
        "author": "Mission Control",
        "execution_target": "agent",
        "category": "monitoring",
        "permissions": ["collect:inventory", "execute:commands"],
        "dependencies": [],
        "min_core_version": "3.0.0",
    },
    {
        "slug": "hardware-inventory",
        "name": "Hardware Inventory",
        "version": "1.0.0",
        "description": "Collect detailed hardware inventory from agents",
        "author": "Mission Control",
        "execution_target": "agent",
        "category": "inventory",
        "permissions": ["collect:inventory"],
        "dependencies": [],
        "min_core_version": "3.0.0",
    },
    {
        "slug": "smart-disk",
        "name": "SMART Disk Monitoring",
        "version": "1.0.0",
        "description": "Monitor disk health via SMART attributes",
        "author": "Mission Control",
        "execution_target": "agent",
        "category": "monitoring",
        "permissions": ["collect:health"],
        "dependencies": [],
        "min_core_version": "3.0.0",
    },
    {
        "slug": "performance-counters",
        "name": "Performance Counters",
        "version": "1.0.0",
        "description": "Collect CPU, memory, disk, and network performance data",
        "author": "Mission Control",
        "execution_target": "agent",
        "category": "monitoring",
        "permissions": ["collect:performance"],
        "dependencies": [],
        "min_core_version": "3.0.0",
    },
    # ------------------------------------------------------------------ #
    # Hybrid Plugins                                                      #
    # ------------------------------------------------------------------ #
    {
        "slug": "remote-desktop",
        "name": "Remote Desktop",
        "version": "1.0.0",
        "description": "Remote desktop access combining server and agent components",
        "author": "Mission Control",
        "execution_target": "hybrid",
        "category": "remote-access",
        "permissions": ["execute:commands", "read:integrations"],
        "dependencies": [],
        "min_core_version": "3.0.0",
    },
    {
        "slug": "patch-management",
        "name": "Patch Management",
        "version": "1.0.0",
        "description": "Scan, deploy, and verify OS patches across endpoints",
        "author": "Mission Control",
        "execution_target": "hybrid",
        "category": "security",
        "permissions": ["execute:commands", "collect:inventory"],
        "dependencies": [],
        "min_core_version": "3.0.0",
    },
    {
        "slug": "backup-verification",
        "name": "Backup Verification",
        "version": "1.0.0",
        "description": "Verify backup integrity and restore readiness",
        "author": "Mission Control",
        "execution_target": "hybrid",
        "category": "backup",
        "permissions": ["read:integrations", "collect:health"],
        "dependencies": [],
        "min_core_version": "3.0.0",
    },
    {
        "slug": "security-audit",
        "name": "Security Audit",
        "version": "1.0.0",
        "description": "Comprehensive security audit across server and endpoints",
        "author": "Mission Control",
        "execution_target": "hybrid",
        "category": "security",
        "permissions": ["read:integrations", "collect:inventory", "execute:commands"],
        "dependencies": [],
        "min_core_version": "3.0.0",
    },
    {
        "slug": "endpoint-compliance",
        "name": "Endpoint Compliance",
        "version": "1.0.0",
        "description": "Verify endpoint compliance with security policies",
        "author": "Mission Control",
        "execution_target": "hybrid",
        "category": "security",
        "permissions": ["collect:inventory", "execute:commands"],
        "dependencies": [],
        "min_core_version": "3.0.0",
    },
]


class PluginMarketplaceService:
    """Marketplace catalog and installation recommendations."""

    @staticmethod
    def list_catalog(
        execution_target: str | None = None,
        category: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return the plugin catalog with optional filtering."""
        results = list(BUILTIN_CATALOG)
        if execution_target:
            results = [p for p in results if p["execution_target"] == execution_target]
        if category:
            results = [p for p in results if p["category"] == category]
        return results

    @staticmethod
    def get_plugin_info(slug: str) -> dict[str, Any] | None:
        """Return catalog info for a specific plugin."""
        for p in BUILTIN_CATALOG:
            if p["slug"] == slug:
                return p
        return None

    @staticmethod
    def get_categories() -> list[str]:
        """Return distinct categories from the catalog."""
        return sorted({p["category"] for p in BUILTIN_CATALOG if p.get("category")})

    @staticmethod
    def merge_with_installed(
        catalog: list[dict[str, Any]],
        installed_slugs: set[str],
    ) -> list[dict[str, Any]]:
        """Annotate catalog entries with installation status."""
        result = []
        for entry in catalog:
            enriched = dict(entry)
            enriched["installed"] = entry["slug"] in installed_slugs
            result.append(enriched)
        return result


plugin_marketplace_service = PluginMarketplaceService()
